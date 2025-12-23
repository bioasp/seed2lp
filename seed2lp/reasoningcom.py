from time import time
from .network import Network
from .reasoning import Reasoning
from .file import delete, save, load_tsv, existing_file
from . import color, logger
from multiprocessing import Process, Queue
from os import path
from json import loads


USE_MULTIPROCESSING=True

###################################################################
################# Class Reasoning : herit Solver ################## 
###################################################################
class ComReasoning(Reasoning):
    def __init__(self, run_mode:str, run_solve:str, network:Network,
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None, 
                 intersection:bool=False, union:bool=False, 
                 temp_dir:str=None, short_option:str=None, 
                 verbose:bool=False, community_mode:str=None, 
                 partial_delete_supset:bool=False, all_transfers:bool=False,
                 not_shown_transfers:bool=False, limit_transfers:int=-1):
        """Initialize Object ComReasoning, herit from Reasoning

        Args:
            run_mode (str): Running command used (full or target)
            network (Network): Network constructed
            time_limit_minute (float, optional): Time limit given by user in minutes. Defaults to None.
            number_solution (int, optional): Limit number of solutions to find. Defaults to None.
            clingo_configuration (str, optional): Configuration for clingo resolution. Defaults to None.
            clingo_strategy (str, optional): Strategy for clingo resolution. Defaults to None.
            intersection (bool, optional):  Find the intersection of all solutions without limitation (give one solution). Defaults to False.
            union (bool, optional): Find the union of all solutions without limitation (give one solution). Defaults to False.
            minimize (bool, optional): Search the minimal carinality of solutions. Defaults to False.
            subset_minimal (bool, optional):  Search the subset minimal solutions. Defaults to False.
            temp_dir (str, optional): Temporary directory for saving instance file and clingo outputs. Defaults to None.
            short_option (str, optional): Short way to write option on filename. Defaults to None.
            verbose (bool, optional): Set debug mode. Defaults to False.
        """
        super().__init__(run_mode, run_solve, network,
                        time_limit_minute, number_solution, 
                        clingo_configuration, clingo_strategy, 
                        intersection, union, 
                        False, True, # Minimize=False, Subset minimal = True
                        temp_dir, short_option, 
                        verbose, 
                        community_mode, all_transfers) # 'global', 'bisteps', 'delsupset', 'all'
        self.partial_delete_supset = partial_delete_supset
        self.not_shown_transfers = not_shown_transfers
        self.limit_transfers = limit_transfers
        if self.limit_transfers != -1:
            self.clingo_constant.append('-c')
            self.clingo_constant.append(f'limit_transfers={self.limit_transfers}')

    def search_seed(self):
        """Define the asp files to use before performing parent seed_searching
        """
        self.asp_files.append(self.asp.ASP_SRC_COMMUNITY)  
        if self.limit_transfers != -1:
            self.asp_files.append(self.asp.ASP_SRC_LIMIT_TRANSFERS)
        match self.community_mode:
            case "global"|"delsupset":  
                if not self.not_shown_transfers:
                    self.asp_files.append(self.asp.ASP_SRC_COM_HEURISTIC)
                    self.asp_files.append(self.asp.ASP_SRC_SHOW_TRANSFERS)
                super().search_seed()
                
            case "bisteps":
                super().search_seed()



    def kill_conditon(self, size_list_sol:int,  current_timer:float, stats:dict):
        """_summary_

        Args:
            solution_list (int): _description_
            current_timer (float): _description_
            stats_seeds (dict): _description_
        """
         # No limit on number of solution
        no_limit_solution = False
        
        if self.number_solution == 0:
            no_limit_solution = True

        return not (((size_list_sol < self.number_solution \
                        and not no_limit_solution) \
                        or no_limit_solution )\
                        and \
                        ((self.time_limit and float(current_timer) < float(self.time_limit))\
                        or not self.time_limit)\
                        and \
                        stats == None)



    def solve_bisteps(self, full_option:list, solution_list:dict, 
                        search_mode:str, step:str, asp_files:list=None, 
                        queue:Queue=None, full_path:str=None):
        """Solve enumeration for Reasoning Classic mode using Clyngor

        Args:
            full_option (list): A list of all options needed for clingo solving
            solution_list (dict): A dictionnary of all found solutions
            search_mode (str): Optimization selected for the search (submin-enumeration / minimze-enumeration)
            step (str): Which seed solving mode (classic, filter, guess-check or guess-chekc-div)
            asp_files (list, optional): List of needed ASP files to solve ASP with Clyngor.
            queue (Queue, optional): Queue for multiprocessing program (managing time limit). Defaults to None.
            full_path (str, optional):  Full path of temporary solution file

        Returns:
            solution_list (dict): a dictionnary of all found solutions
        """
       
        cobra_flux=None
        # Guess_check or Guess_check diversity mode   
        if "guess_check" in self.run_solve :
            is_guess_check = True
        else:
            is_guess_check = False

        match step:
            case "classic":
                mode = 'REASONING'
            case "filter":
                mode = 'REASONING FILTER'
            case "guess_check" | "guess_check_div":
                mode = self.get_gc_mode()

        # When we check filter, we want the limit of number solutions
        # on validating flux model, and not on finding model only
        if step == "classic":
            nb_seeds=self.number_solution
        else:
            nb_seeds=0

        _,full_option_seeds = self.construct_string_option(full_option)
        full_option_seeds = self.complete_option(full_option_seeds, nb_seeds)
        ctrl_seeds = self.control_init(full_option_seeds, asp_files, is_guess_check)

        # Transfer preparing clingo
        # In this step we do not need to search again for seeds
        if self.all_transfers:
            nb_transfer=0
        else:
            nb_transfer=1

        transfers_asp_files=self.get_transfers_asp_file()
        transfers_asp_files.append(self.asp.ASP_SRC_SEED_EXTERNAL)
        _,full_option_transfer = self.construct_string_option(full_option)
        full_option_transfer = self.complete_option(full_option_transfer,nb_transfer)
        ctrl_transfers = self.control_init(full_option_transfer, transfers_asp_files, is_guess_check)


        self.get_message("command search seed")
        idx = 1
        
        current_timer=0
        number_rejected=0
        start_time=time()
        # When stats appears, Therefore clingo has finished his solutions
        # Condition on stats helps finish while loop, especially when 
        # no time_limit or no numbersolution is given, or when time limit 
        # is higher than the total time for clingo to compute
        # or number solution is higher than all solutions found with clingo.
        # The condition on stats avoid to loop again on solving again
        stats_seeds=None
        
        with ctrl_seeds.solve(yield_=True) as h_seeds:
            for model_seeds in h_seeds:
                print("\n")

                seeds_set = model_seeds.symbols(shown=True)

                seeds, seeds_full, _, _ = self.get_seeds_transfers(seeds_set)
                # enforce seeds
                for seed in seeds_set:
                    ctrl_transfers.assign_external(seed, True)

                # Get transfer for fixed set of seeds
                self.get_message("command search transfers")
                with ctrl_transfers.solve(yield_=True) as h_transfers:
                    for model_transfers in h_transfers:
                        transfers_set = model_transfers.symbols(shown=True)
                        _, _, transferred, _ = self.get_seeds_transfers(transfers_set)
                        transf_short, trans_complete, trans_solution_list =self.get_transfers_info(transferred)

                        size_seeds = len(seeds)

                        if step == "classic":
                            self.network.add_result_seeds(mode, search_mode, 'model_'+str(idx), size_seeds, seeds, transferred_list=trans_solution_list)
                            keep_solution=True
                        else:
                            res = self.network.check_seeds(seeds, trans_solution_list)
                            if res[0]:
                                # valid solution
                                logger.print_log(f'CHECK Solution {size_seeds} seeds -> OK\n', 'debug')
                                cobra_flux=res[1]
                                self.network.add_result_seeds(mode, "Community bisteps", 'model_'+str(idx), size_seeds, seeds, flux_cobra=cobra_flux, transferred_list=trans_solution_list)
                                keep_solution=True
                            else:
                                logger.print_log(f'CHECK Solution {size_seeds} seeds -> KO\n', 'debug')
                                number_rejected +=1
                                keep_solution=False
                                current_timer = time() - start_time
                                # write all 100 rejected 
                                # or write from 5 minute before finishing the process near to finish  the process
                                if USE_MULTIPROCESSING and number_rejected%100 == 0 \
                                or (current_timer!=0 and current_timer > self.time_limit_minute*60 - 300):
                                    self.temp_rejected(number_rejected, full_path)
                            #print(current_timer)
                            current_timer = time() - start_time
                        if keep_solution:
                            message = color.cyan_light  + f"Answer: {idx}{color.reset} ({size_seeds} seeds{transf_short}) \n"
                            self.print_answer(message, seeds, seeds_full, trans_complete)
                            solution_list, solution_temp = self.complete_solutions(solution_list, 'model_'+str(idx), size_seeds, seeds, trans_solution_list,cobra_flux,number_rejected)
                            if USE_MULTIPROCESSING:
                                solution_temp.append(seeds_full)
                                save(full_path, "", solution_temp, "tsv", True)
                            idx+=1
                        current_timer = time() - start_time

                        if self.kill_conditon(len(solution_list), current_timer, stats_seeds):
                            ctrl_transfers.interrupt()
                            ctrl_transfers.cleanup()
                            ctrl_seeds.interrupt()
                    
                # deactivate enforced seeds
                for seed in seeds_set:
                    ctrl_transfers.assign_external(seed, False)

        stats_seeds = ctrl_seeds.statistics

        if self.kill_conditon(len(solution_list), current_timer, stats_seeds):
            ctrl_seeds.interrupt()
            ctrl_seeds.cleanup()
    

        if step != "classic":
            logger.print_log(f'Rejected solution during process: {number_rejected} \n', "info")
        else:
            number_rejected=None

        if not any(solution_list): 
            logger.print_log('Unsatisfiable problem', "error")
            
        if USE_MULTIPROCESSING:
            queue.put([self, solution_list, None, current_timer, number_rejected])
        else:
            return solution_list, number_rejected
    

    def check_set_submin(self, seeds:list, dict_by_size_seeds:dict, max_size:int, solution_list:dict):
        """Used for delete superset mode. Check if the subset minimal set of seeds found is a subset
        of a previous solutions found or not. If it is, the other solution is deleted.
        "Manual checking" of subset minimal solution

        Args:
            seeds (list): List of seed found (subset minimal solution)
            dict_by_size_seeds (dict): A dictionnary of all set of seeds found, having as key the size of the set to limit the loops
            max_size (int): The maximal value of the size found (higher key of dict_by_size_seeds dictionnary)
            solution_list (dict): List of solutions into a dictionnary (key value is the name of the model)
        """
        size_sup=len(seeds)+1

        while size_sup <= max_size:
            if size_sup in dict_by_size_seeds:
                list_do_delete=list()
                for name, solution in dict_by_size_seeds[size_sup].items():
                    if set(seeds).issubset(set(solution["seeds"])):
                        list_do_delete.append(name)
                        del solution_list[name]
                        self.network.result_seeds
                        # when there is no set of seeds in the key of dictionnary we remove it
                        if len(dict_by_size_seeds[size_sup])==0:
                            del dict_by_size_seeds[size_sup]
                for name in list_do_delete:
                    del dict_by_size_seeds[size_sup][name]
            size_sup+=1
        return solution_list
    

    def complete_dict_solution(self, solution_list:dict, dict_by_size_seeds:dict, max_size:int, seeds:list, size:int, name:str, sol:dict):
        """Used for delete superset mode. Complete the dictionnary (key = size) solution  and list of by adding or deleting solutions
        After checking if set of seeds is a subset of a previous set of seeds found.

        Args:
            solution_list (dict): List of solutions into a dictionnary (key value is the name of the model)
            dict_by_size_seeds (dict): A dictionnary of all set of seeds found, having as key the size of the set to limit the loops
            max_size (int): The maximal value of the size found (higher key of dict_by_size_seeds dictionnary)
            seeds (list): List of seed found (subset minimal solution)
            size (int): size of set of seeds
            name (str): name of the model solution
            sol (dict): Dictionnary of the curent solution

        Returns:
            dict, dict, int: solution_list, dict_by_size_seeds, max_size
        """
        if size not in dict_by_size_seeds:
            dict_by_size_seeds[size]={name:sol}
            # when the size is bigger than all previsous size, this is a new subset minimal and can't be
            # a superset of previous because of ASP constraints on superset
            if (max_size and size > max_size) or not max_size:
                max_size=size
            # when the size is not on the dictionnary, we can have 2 situations:
            # 1. The size is the smallest
            # 2. The size is between two sizes
            # For each of these cases we have to check if the solution is not a subset min of all
            # solution having a bigger size
            else :
                if not self.partial_delete_supset:
                    solution_list=self.check_set_submin(seeds, dict_by_size_seeds, max_size, solution_list)
        # When the size is in the dictionnary, we add the solution on the list of solution of this size
        # and we have to check if the solution is not a subset min of all solution having a bigger size
        else:
            dict_by_size_seeds[size][name] = sol

            if not self.partial_delete_supset:
                solution_list=self.check_set_submin(seeds, dict_by_size_seeds, max_size, solution_list)
        return solution_list, dict_by_size_seeds, max_size


    def solve_delete_superset(self, full_option:list, solution_list:dict, 
                              step:str, asp_files:list, 
                              queue:Queue=None, full_path:str=None):
        """Solve the seed searching in delete superset mode. For each global subset minimal solution 
        (seeds and transfer subset min), the set of seeds and superset oft this set is forbidden for the 
        next clingo solve. Because of this specific mode, some solution can be found as subset minimal as 
        previous solution later, and a manual check into solutions is needed by adding new solution and removing 
        all previous solution containing the new solution found.
        WARNING: This is the only mode where Filter and Guess-Chek are integrated into the function due to
        the specific solving mode.

        Args:
            full_option (list): All Clingo option 
            solution_list (dict): _description_
            step (str): step solving mode (classic, filter, guess_check, guess_check_div).
            asp_files (list):  List of needed ASP files to solve ASP (Clingo package)
            queue (Queue, optional): Queue for multiprocessing program (managing time limit). Defaults to None.
            full_path (str, optional):  Full path of temporary solution file. Defaults to None.

        Returns:
            _type_: _description_
        """
        all_time_solve = 0
        all_time_ground = 0
        dict_by_size_seeds=dict()
        max_size=None
        avoided = []
        stats = None

        _,full_option = self.construct_string_option(full_option)
        full_option = self.complete_option(full_option,0)

        if "guess_check" in self.run_solve :
            is_guess_check = True
        else:
            is_guess_check = False

        ctrl = self.control_init(full_option, asp_files, is_guess_check)
        solution_idx = 1
        number_rejected = 0
        keep_solution = True

        match step:
            case "classic":
                mode = 'REASONING'
            case "filter":
                mode = 'REASONING FILTER'
            case "guess_check" | "guess_check_div":
                mode = self.get_gc_mode()
        
        start_time=time()
        current_timer=0
        while not self.kill_conditon(len(solution_list), current_timer, None):
            with ctrl.solve(yield_=True) as h:
                seeds = list()
                transferred = list()
                sol=dict()
                cobra_flux=None
                for model in h:
                    atoms = model.symbols(shown=True)
                    
                    seeds, seeds_full, transferred, seed_complete_constraints = self.get_seeds_transfers(atoms)
                    transf_short, trans_complete, trans_solution_list =self.get_transfers_info(transferred)

                    size = len(seeds)

                    if step == "classic":
                        keep_solution=True
                    #Filter, Guess Check ou Guess Check Diversity
                    else :
                        res = self.network.check_seeds(seeds, trans_solution_list)
                        if res[0]:
                            # valid solution
                            logger.print_log(f'CHECK Solution {size} seeds -> OK\n', 'debug')
                            cobra_flux=res[1]
                            keep_solution=True
                        else:
                            logger.print_log(f'CHECK Solution {size} seeds -> KO\n', 'debug')
                            number_rejected +=1
                            keep_solution=False
                            current_timer = time() - start_time
                            # write all 100 rejected 
                            # or write from 5 minute before finishing the process near to finish  the process
                            if USE_MULTIPROCESSING and number_rejected%100 == 0 \
                            or (current_timer!=0 and current_timer > self.time_limit_minute*60 - 300):
                                self.temp_rejected(number_rejected, full_path)
                            keep_solution=False

                    current_timer = time() - start_time
                    if self.kill_conditon(len(solution_list), current_timer, None):
                        ctrl.interrupt()
                    
                    if keep_solution:
                        if seeds:
                            name = 'model_' +  str(solution_idx)
                            
                            sol["seeds"] = set(seeds)
                            sol["seeds_full"]=seeds_full
                            sol["transf_short"]=transf_short
                            sol["trans_complete"]=trans_complete
                        else: 
                            if not transferred:
                                sol["transf_short"] = sol["trans_complete"] = "" 
                                trans_solution_list = list()  
                            else:
                                sol["transf_short"]=transf_short
                                sol["trans_complete"]=trans_complete
                        if not self.partial_delete_supset:
                            solution_list, dict_by_size_seeds, max_size = self.complete_dict_solution(solution_list, dict_by_size_seeds, max_size, seeds, size, name, sol)
                        else:
                            message = color.cyan_light + f"Answer: {solution_idx}{color.reset} ({size} seeds{transf_short})\n"
                            self.print_answer(message, seeds, seeds_full, trans_complete)
                            self.network.add_result_seeds(mode, "Community delete superset of seeds", 'model_'+str(solution_idx), size, seeds, flux_cobra=cobra_flux, transferred_list=trans_solution_list)
                    break
                
                if not seeds: 
                    break

            if keep_solution:
                # Sum all grounding time together and all solving time together

                #Save solution list as found (without deletion)
                solution_list, solution_temp = self.complete_solutions(solution_list, name, size, seeds, trans_solution_list,cobra_flux,number_rejected)
                if USE_MULTIPROCESSING:
                    solution_temp.append(seeds_full)
                    save(full_path, "", solution_temp, "tsv", True)
                solution_idx +=1
            
            stats = ctrl.statistics
            total_time = stats["summary"]["times"]["total"]
            time_solve = stats["summary"]["times"]["solve"]
            time_ground  = total_time - time_solve

            all_time_solve += float(time_solve)
            all_time_ground += float(time_ground)

            current_timer = time() - start_time
            if self.kill_conditon(len(solution_list), current_timer, None):

                ctrl.interrupt()
                ctrl.cleanup()
            else: 
                # exclude solution and its supersets
                ctrl.add("skip_seed_and_supset", [], seed_complete_constraints)
                ctrl.ground([("skip_seed_and_supset",[])])

            match step:
                case "guess_check" | "guess_check_div":
                    ctrl, avoided= self.guess_check_constraints(ctrl, atoms, seeds, avoided)

        if not self.partial_delete_supset:
            solution_list = self.add_print_solution(solution_list, dict_by_size_seeds, mode, cobra_flux)

        if step != "classic":
            logger.print_log(f'Rejected solution during process: {number_rejected} \n', "info")
        else:
            number_rejected=None

        if USE_MULTIPROCESSING:
            queue.put([self, solution_list, all_time_ground, all_time_solve, number_rejected])
        else:
            return solution_list, number_rejected



    def add_print_solution(self,solution_list:dict, dict_by_size_seeds:dict, mode:str, flux_cobra:float=None):
        """Used for delete superset mode. The solution are printed after manually checking solution to identify if they are
        subset minimal of previous found solution and finding the defined number of solutions wanted. The model name (solution)
        are therefore reviewed. The solution are both printed and added as answer to the Network object.

        Args:
            solution_list (dict): List of solutions into a dictionnary (key value is the name of the model)
            dict_by_size_seeds (dict): A dictionnary of all set of seeds found, having as key the size of the set to limit the loops
            mode (str): The string solving mode (Classic, filter, guess_check, guess_check diversty)
            flux_cobra (float, optional): The obra flux. Defaults to None.

        Returns:
            dict: new_solution_list
        """

        solution_idx = 1
        new_solution_list=dict()
        for name, solution in solution_list.items():
            new_name = 'model_'+str(solution_idx)
            new_solution_list[new_name]=solution
            size = int(solution[1])
            seeds = solution[3]
            trans_solution_list = solution[5]
            
            transf_short = dict_by_size_seeds[size][name]["transf_short"]
            seeds_full = dict_by_size_seeds[size][name]["seeds_full"]
            trans_complete = dict_by_size_seeds[size][name]["trans_complete"]

            message = color.cyan_light + f"Answer: {solution_idx}{color.reset} ({size} seeds{transf_short})\n"
            self.print_answer(message, seeds, seeds_full, trans_complete)
            self.network.add_result_seeds(mode, "Community delete superset of seeds", new_name, size, seeds, flux_cobra=flux_cobra, transferred_list=trans_solution_list)

            solution_idx +=1
        return new_solution_list



    def get_solution_from_temp_com(self, unsat:bool, full_path:str, step:str, mode:str):
        """Get the solution written in temporary file during execution fo seed searching while using 
        multiprocessing.

        Args:
            unsat (bool): Determine if the model is unsat
            full_path (str): Path of temporary file
            step (str): step solving mode (classic, filter, guess_check, guess_check_div). 

        Returns:
            List: list of solutions
        """
        solution_list = dict()
        transferred_list = None

        dict_by_size_seeds=dict()
        max_size=None
        number_rejected=None
        if not unsat and existing_file(full_path):
        # in case of enumeration it is needed to get the results back from the saved temporary
        # file which is saved during the called 
            column_len = 7
            try:
                temp_list = load_tsv(full_path)
                for solution in temp_list:
                    if len(solution) == column_len:
                        # some line has no data value only the number of rejected solution
                        if solution[0]:
                            name = solution[0]
                            size = int(solution[1])
                            seeds = solution[2].replace(" ", "")
                            seeds = seeds.replace("\'", "")
                            seeds_list = seeds[1:-1].split(',')
                            sol=dict()
                            sol["seeds"] = set(seeds)
                            seeds_full = solution[6].replace("[[", "[")
                            seeds_full = seeds_full.replace("]]", "]")
                            seeds_full = seeds_full.replace("String('", "'")
                            seeds_full = seeds_full.replace("')", "'")
                            seeds_full = eval(seeds_full)
                            sol["seeds_full"] = seeds_full

                            sol_details = ["size", solution[1]] + \
                                ["Set of seeds",seeds_list]

                            transferred_list = eval(solution[5]) 
                            sol_details += ["Set of transferred", transferred_list]

                            flux_cobra = loads(solution[4].replace("'",'"'))
                            sol += ["Cobra flux",  flux_cobra]

                            transf_short, trans_complete, _ =self.get_transfers_info(transferred_list)

                            sol["transf_short"]=transf_short
                            sol["trans_complete"]=trans_complete

                            solution_list[solution[0]] = sol_details

                            solution_list, dict_by_size_seeds, max_size = self.complete_dict_solution(solution_list, dict_by_size_seeds, max_size, seeds, size, name, sol)

                            solution_list=self.check_set_submin(seeds, dict_by_size_seeds, max_size, solution_list)
                    #get the last occurence for rejected solutions number
                    number_rejected = solution[3]

            except Exception as e:
                logger.print_log(f"An error occured while reading temporary file\n {full_path}:\n {e}", 'error')

            if any(solution_list):
                solution_list = self.add_print_solution(solution_list, dict_by_size_seeds, mode, flux_cobra) 

            if step != "classic":
                logger.print_log(f'Rejected solution during process: at least {number_rejected} \n', 'info')

        delete(full_path)
        return solution_list, number_rejected


    def run_multiprocess(self, full_option:list, solution_list:dict, 
                         step:str, asp_files:list, timer:dict,
                         output_type:str,suffix:str, search_mode:str=None):
        """_summary_

        Args:
            full_option (list): _description_
            solution_list (dict): _description_
            step (str): _description_
            asp_files (list): _description_
            timer (dict): _description_
            output_type (str): _description_
            suffix (str): _description_
            search_mode (str,Optional): _description_. Defaults to None.
        """
        queue = Queue()
        full_path = path.join(self.temp_dir,f"{self.temp_result_file}.tsv")
        start = time()
        if self.community_mode == "bisteps":
            p = Process(target=self.solve_bisteps(full_option, solution_list, search_mode,
                                                        step, asp_files, queue, full_path))
        elif self.community_mode == "delsupset":
            p = Process(target=self.solve_delete_superset(full_option, solution_list, 
                                                        step, asp_files, queue, full_path))
        p.start()
        try:
            # the time out limit is added here
            obj, solution_list, time_ground, time_solve, number_rejected = queue.get(timeout=self.time_limit)
            self.network.result_seeds = obj.network.result_seeds 
            delete(full_path)
        except:
            time_process=time() - start
            time_ground = time_solve = -1
            unsat = False
            time_out = False
            if not self.time_limit or time_process < self.time_limit:
                unsat = True
            else:
                time_out = True
            if time_out:
                logger.print_log(f'Time out: {self.time_limit_minute} min expired', "error")

            match step:
                case "classic":
                    mode = 'REASONING'
                case "filter":
                    mode = 'REASONING FILTER'
                case "guess_check":
                    mode = 'REASONING GUESS-CHECK'
                case "guess_check_div":
                    mode =  'REASONING GUESS-CHECK DIVERSITY'  
            solution_list, number_rejected = self.get_solution_from_temp_com(unsat, full_path, step, mode)
        
        p.terminate()
        queue.close()

        if not any(solution_list): 
            logger.print_log('Unsatisfiable problem', "error")

        if time_ground != None:
            if time_ground != -1:
                timer["Grounding time"] = round(time_ground, 3)
            else:
                timer["Grounding time"] = "Time out"
        results=self.get_constructed_result(time_solve, timer, dict(), solution_list, number_rejected)
        self.output[output_type+suffix] = results


    def solve(self, search_mode:str, timer:dict, asp_files:list=None, step:str="classic"):
        """Solve the seed searching using the launch mode

        Args:
            search_mode (str, optional): Describe the launch mode.
            timer (dict): Timer dictionnary containing grouding time
        """
        solution_list = dict()
        full_option, _, _, output_type = self.get_solutions_infos(search_mode)

        match self.community_mode:
            # When a subset minimal is done on global mode, meaning on both seeds and transfers together
            # we can use the solving from the parent (class Reasoning) and therefore the filter and 
            # guess check fucntions from the parent.
            case "global" :
                super().solve(search_mode,timer,asp_files,step)
            
            # To use the bisteps mode, meaning first we do a subset minimal on seeds then we find one
            # subset minimal on transfers, we need a new solving modes
            case "bisteps":
                suffix=self.get_suffix(step)
                match search_mode, step:
                    # CLASSIC MODE (NO FILTER, NO GUESS-CHECK)   
                    case "minimize-enumeration" | "minimize-one-model", _:
                        logger.print_log("No minimisation in community", "warning")

                    case "submin-enumeration", _:
                        logger.print_log("SOLVING...\n", "info")
                        if USE_MULTIPROCESSING:
                            self.run_multiprocess(full_option, solution_list, step, asp_files, timer, output_type, suffix, search_mode)
                        else :
                            time_solve = time()
                            solution_list, number_rejected = self.solve_bisteps(full_option, solution_list, 
                                                                        search_mode,step, asp_files)
                            time_solve = time() - time_solve

                            results=self.get_constructed_result(time_solve, timer, dict(), solution_list, number_rejected)
                            self.output[output_type+suffix] = results

                        

            # To use the delsupset mode, meaning we solve and subset min on both seed and transfers, then add
            # a constraint to forbid all superset of set of seeds (only) found, we need to to id step by step
            # and dynamically add the constraint on superset. We need a new solving mode, getting the first subsetmin
            # solution in seed, adding a constraint and redoing this until having the number of solution requested.
            # Doing this might select some set as subset min first (mixing seeds and transfers) but after find a subsetmin
            # of seed (but different transfers) that will be a subsetmin of first solution. It is needed to take into account
            # manually this cases and delete the previous solution of results.
            # example :
            # solution 1: seeds are A, B, C , transfers is D
            # solution 2: seeds are A, B, transfers D, E
            # both are global subset min, but solution 2 is subset min of solution 1 regarding only seeds
            case "delsupset":
                suffix=self.get_suffix(step)
                match search_mode, step:
                    # CLASSIC MODE (NO FILTER, NO GUESS-CHECK)   
                    case "minimize-enumeration" | "minimize-one-model", _:
                        logger.print_log("No minimisation in community", "warning")

                    # Because of specific analyse of solution with "manual deletion of previous superset"
                    # All solving mode are in one function (classic, filter, guess check and gues check div)
                    # unlike all other community modes (or signle network modes)
                    case "submin-enumeration", "classic" | "filter" | "guess_check" | "guess_check_div":
                        logger.print_log("SOLVING...\n", "info")
                        
                        # Time limit may not work well if no solutions found within time limit
                        # But save time from writting into temporary file
                        if USE_MULTIPROCESSING:
                            self.run_multiprocess(full_option, solution_list, step, asp_files, timer, output_type, suffix)

                        else :
                            time_solve = time()
                            solution_list, number_rejected = self.solve_delete_superset(full_option, solution_list, 
                                                                        step, asp_files)
                            time_solve = time() - time_solve

                            results=self.get_constructed_result(time_solve, timer, dict(), solution_list, number_rejected)
                            self.output[output_type+suffix] = results

                        

