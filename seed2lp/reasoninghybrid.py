from .solver import Solver
from .network import Network
from multiprocessing import Process, Queue
from .file import save, delete, write_instance_file, load_tsv, existing_file
import clingo
from . import color, logger
from os import path
import random
from time import time
from json import loads

###################################################################
############# Class HybridReasoning : herit Solver ################ 
###################################################################
class HybridReasoning(Solver):
    def __init__(self, run_mode:str, network:Network,
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None, 
                 intersection:bool=False, union:bool=False, 
                 minimize:bool=False, subset_minimal:bool=False, 
                 temp_dir:str=None, short_option:str=None, run_solve:str=None,
                 verbose:bool=False, community_mode:str=None,all_transfers:bool=False):
        """Initialize Object HybridReasoning, herit from Solver

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
        super().__init__(run_mode, network, time_limit_minute, number_solution, clingo_configuration, 
                         clingo_strategy, intersection, union, minimize, subset_minimal, 
                         temp_dir, short_option, run_solve, verbose, community_mode)
        
        self.all_transfers = all_transfers
        

    ######################## METHODS ########################
        
    def control_init(self, full_option:list, asp_files:list, is_guess_check:bool=False):
        """Initiate Clingo control for package Clingo

        Args:
            full_option (list): All Clingo option 
            asp_files (list): List of needed ASP files to solve ASP (Clingo package)
            is_guess_check (bool, optional): Determine if it is a Guess Check (True) or a Filter (Fale). 
                                            Defaults to False.

        Returns:
            ctrl (clingo.Control): Return Clingo control for solving
        """
        if "--warn=none" not in full_option:
            full_option.append("--warn=none")
        ctrl = clingo.Control(full_option)

        for file in asp_files:
            ctrl.load(file)

        ctrl.ground([("base",[])])
        if self.diversity and is_guess_check:
            ctrl.add("diversity", [], """
            #program diversity.
            #heuristic new_seed(M) : avoidseed(M). [10,false]
            #heuristic new_seed(M). [1,false] % subset
            #external avoidseed(M) : metabolite(M,_).
            """)
            ctrl.ground([("diversity",[])])

        self.get_message("command")
        logger.print_log('clingo ' + ' '.join(full_option) + ' ' + ' '.join(asp_files), 'debug')
        return ctrl
    

    def get_constructed_result(self, time_solve:float, timer:dict, results:dict, solution_list:dict, number_rejected:int):
        """Complete and structure the resulted dictionnary

        Args:
            time_solve (float): Solving time
            timer (dict): dictionnary of timers (with other timer if exists)
            results (dict): final dictionnary of results
            solution_list (dict): Dictionnary containing the models resulted for one mode (reasoning, filter, guess-check ...)
            number_rejected (int): Used for hybrid-cobra modes (filter, guess-check, guesscheck div)

        Returns:
            dict: results
        """
        if time_solve != -1:
            timer["Solving time"] = round(time_solve, 3)
        else:
            timer["Solving time"] = "Time out"      
        results["Timer"] = timer.copy()
        results['solutions'] = solution_list
        if number_rejected is not None:
            results['rejected'] = number_rejected
        return results
    

    def save_seeds_tmp(self, seeds_fact:str, idx:int):
        """Save seeds as asp fact in temporary file for bistep mode in community after the first step which find and subset min only on seeds
        to be able to retrieve the seeds as an asp file and do the second step which found the first solution of subsetminimal transfers with
        those saved seeds

        Args:
            seeds_fact (str): seeds converted into asp facts
            idx (int): index of the soulution (solution number idx)

        Returns:
            str: seeds_temp_file
        """
        # create a temporary seeds instance file
        seeds_temp_file=f"seeds_model_{idx}_{self.temp_result_file}.lp"
        seeds_temp_file=path.join(self.temp_dir,seeds_temp_file)
        write_instance_file(seeds_temp_file, seeds_fact)
        return seeds_temp_file


    def get_transfers_info(self, list_transferred:list):
        """From list of transferred, get datas and structure them into a dictionnary for output result file

        Args:
            list_transferred (list): List of transferred metabolite

        Returns:
            str,str,list: transf_short (size of transfers), trans_complete (line of printed transfers), trans_solution_list
        """
        size_transf = len(list_transferred)
        trans_complete=None
        trans_solution_list=list()
        if not self.network.is_community:
            transf_short = ""
        elif size_transf>0:
            transf_short = f" and {size_transf} transfers"
            trans_complete = f"\n  Transfers   {color.cyan_dark}|{color.reset}     From     {color.cyan_dark}|{color.reset}     To\n"
            trans_complete += f"--------------{color.cyan_dark}|{color.reset}--------------{color.cyan_dark}|{color.reset}--------------\n"
            for meta in list_transferred:
                # When we get the data from temp file, it is already formated as dictionnary
                if type(meta) == dict:
                    dict_transf=meta
                else:
                    dict_transf=dict()
                    dict_transf["Metabolite"] = str(meta[0]).replace('"','')
                    dict_transf["From"] = str(meta[1]).replace('"','')
                    dict_transf["To"]  = str(meta[2]).replace('"','')
                    dict_transf["ID from"]  = str(meta[3]).replace('"','')
                    dict_transf["ID to"]  = str(meta[4]).replace('"','')
                trans_complete += f'{dict_transf["Metabolite"]} {color.cyan_dark}|{color.reset} {dict_transf["From"]} {color.cyan_dark}|{color.reset} {dict_transf["To"]}\n'
                trans_solution_list.append(dict_transf)
        else:
            transf_short = f" and no transfers"

        return transf_short, trans_complete, trans_solution_list
        

    def complete_option(self, full_option:list, nb_sol:int):
        """Convert the list of clingo options into string and complete it with the wanted number of solutions.
        The number of solutions depends on if we are minimizing the solution, or if we want to find the only the first
        subset minimal of solutions.

        Args:
            full_option (list): List of clingo options
            nb_sol (int): number of solutions to ask to clingo

        Returns:
            str: complete_option
        """
        complete_option=full_option.copy()
        complete_option.append(f'-n {nb_sol}')
        return complete_option
    

    def get_transfers_asp_file(self):
        """Remove seed solving files and get transfers file for asp solving.

        Returns:
            list: list of path to asp files
        """
        transf_asp_files=self.asp_files.copy()
        transf_asp_files.remove(self.asp.ASP_SRC_SEED_SOLVING)
        transf_asp_files.remove(self.asp.ASP_SRC_SHOW_SEEDS)
        transf_asp_files.append(self.asp.ASP_SRC_ATOM_TRANSF)
        transf_asp_files.append(self.asp.ASP_SRC_SHOW_TRANSFERS)
        return transf_asp_files


    def convert_seeds_to_fact(self, args:tuple, seeds_fact:str, is_supsetconstraint:bool = False):
        """Convert either seeds into asp seeds fact (bisteps mode) or constraints from seeds
        to forbid set of seed as solution for next solve and constraints for superset of seeds
        to frobid solution including set of seeds (delsupset mode)

        Args:
            args (tuple): Atom argument from clingo
            seeds_fact (str): Seeds asp fact convert to string to complete

        Returns:
            str: seeds_fact
        """
        metabolite_id=str(args[0]).replace('"','')
        metabolite_flag=str(args[1]).replace('"','')
        metabolite_name=str(args[2]).replace('"','')
        species=str(args[3]).replace('"','')
        match self.community_mode:
            case "bisteps":
                seeds_fact += f'\nseed("{metabolite_id}","{metabolite_flag}","{metabolite_name}","{species}").' 
            # in case of delete superset, we do not need to create seeds fact but we need to add constraints
            case "delsupset":
                # Superset of set of seeds to forget for next search
                if is_supsetconstraint:
                    seeds_fact += f', seed("{metabolite_id}","{metabolite_flag}","{metabolite_name}","{species}"), X!="{metabolite_id}"'
                # Set of seeds to forget for next search
                else:
                    if "seed" in seeds_fact:
                        seeds_fact += ', '
                    seeds_fact += f'seed("{metabolite_id}","{metabolite_flag}","{metabolite_name}","{species}")'
        return seeds_fact
    
    
    def get_seeds_transfers(self, atoms):
        """Get Seeds solution from atoms for all modes and transfers for communtiy mode. 
        For delete superset mode, can create the needed constraints (forbid set of seeds and its super set for next search).
        Return a list of seeds (onlyname), but also list of full seeds (all data from seeds atom), a list of transferred metabolites
        if needed and the complete contraints to add to clingo.

        Args:
            atoms: clingo atoms (returned by solver)
            
        Returns:
            list, list, list, str: seeds, seeds_full, transferred, seed_complete_constraints
        """
        seeds = list()
        seeds_full = list()
        transferred = list()
        seed_constraints=":- "
        seed_superset_constraints=":- seed(X,_,_,_)"
        seed_complete_constraints=""
        transfer_constraints=""
        # For single network search, there is only seed, not transfer
        if not self.network.is_community:
            for a in atoms:
                if a.name == "seed":
                    seeds.append(a.arguments[0].string)
            seeds=list(sorted(seeds))
        else:
            for a in atoms:
                if a.name == "seed":
                    seeds.append(a.arguments[0].string)
                    seeds_full.append(a.arguments)
                    if self.community_mode=="delsupset":
                        seed_constraints = self.convert_seeds_to_fact(a.arguments, seed_constraints)
                        seed_superset_constraints = self.convert_seeds_to_fact(a.arguments, seed_superset_constraints,True)
                elif a.name == "transferred":
                    transferred.append(a.arguments)
            seeds=list(sorted(seeds))
            transferred=list(sorted(transferred))
            if self.all_transfers:
                for transfer in transferred:
                    transfer_constraints+=f", transferred({transfer[0]},{transfer[1]},{transfer[2]},{transfer[3]},{transfer[4]})"
            seed_complete_constraints = seed_constraints+transfer_constraints+".\n"+seed_superset_constraints+"."

        return seeds, seeds_full, transferred, seed_complete_constraints
    

    def complete_solutions(self, solution_list:dict, solution_name:str, size:int, seeds:list, 
                           trans_solution_list:list=None, cobra_flux:dict=None, number_rejected:int=None):
        """Complete the solutions ilst and the solution temporary list to save due to of multiprocessing.
        This function is used for filter and guess_check function, but also for delete superset mode in community
        which also use multiprocessing du create constraints while searching solution

        Args:
            solution_list (dict): Dictionnary of solutions by name (model idx)
            solution_name (str): Current solution name
            size (int): size of set of seeds
            seeds (list): list of seeds
            trans_solution_list (list): list of transfers solution
            cobra_flux (dict, optional): Cobra flux found for solution if exists. Defaults to None.
            number_rejected (int, optional): Number of rejected soution if exists. Defaults to None.

        Returns:
            dict, list: solution_list, solution_temp
        """
        solution_temp=None
        
        seeds=list(sorted(seeds))
        solution = ["size", size] + ["Set of seeds", seeds] 
        if self.network.is_community:
            solution += ["Set of transferred", trans_solution_list] 
        # Solutions from filter and guess check
        if cobra_flux or \
            (self.network.is_community and self.community_mode!="global"):
            if cobra_flux:
                solution += ["Cobra flux", cobra_flux]
            solution_temp = [solution_name, size, seeds, number_rejected, cobra_flux]
            if self.network.is_community:
                solution_temp.append(trans_solution_list)
        solution_list[solution_name]=solution
        return solution_list, solution_temp
    

    def add_diversity(self, ctrl:clingo.Control, seeds:list, avoided:list):
        """This function add diversity for the Gess Check mode by avoiding some metabolites
        from previous solution. For each iteration, half of the avoided metabolites is 
        deleted randomly, and half of metabolites as seeds of the current solution is added randomly

        Args:
            ctrl (clingo.Control): Clingo Control initiated
            seeds (list): List of seeds (one solution)
            avoided (list): List of already avoided metabolites

        Returns:
            ctrl (clingo.Control), avoided (list): Return Clingo control for solving 
                                            and the new list of avoided metabolites for next iteration
        """
        forget = 50 # 0..100: percentage of heuristics to forget at each iteration

        # tune heuristics for diversity
        random.shuffle(avoided)
        clue_to_forget = (len(avoided)*forget)//100
        for a in avoided[:clue_to_forget]:
            ctrl.assign_external(a, False)
        avoided = avoided[clue_to_forget:]


        random.shuffle(seeds)
        seed_to_forget = (len(seeds)*forget)//100
        seeds = seeds[seed_to_forget:]
        
        clues = [clingo.Function("avoidseed", [clingo.String(s)]) for s in seeds]

        for a in clues:
            ctrl.assign_external(a, True)
        avoided.extend(clues)

        return ctrl, avoided
    
    def get_solution_from_temp(self, unsat:bool, is_one_model:bool, full_path:str, suffix:str, search_mode:str):
        """Get the solution written in temporary file during execution fo seed searching while using 
        multiprocessing.

        Args:
            unsat (bool): Determine if the model is unsat
            is_one_model (bool): Determine if the model is the optimum finding model for minimize case
            full_path (str): Path of temporary file
            suffix (str): suffix to add for solution enumeration (filter or guess-check)
            search_mode (str): search_mode needed to add to results (subset minimal or minimize)

        Returns:
            dict, str: list of solutions, number of rejected solution
        """
        solution_list = dict()
        number_rejected = None
        transferred_list = None
        if not unsat and existing_file(full_path):
        # in case of enumeration it is needed to get the results back from the saved temporary
        # file which is saved during the called 
            column_len = 5
            if self.network.is_community:
                column_len = 6
            if not is_one_model:
                try:
                    temp_list = load_tsv(full_path)
                    for solution in temp_list:
                        if len(solution) == column_len:
                            # some line has no data value onlu the number of rejected solution
                            if solution[0]:
                                seeds = solution[2].replace(" ", "")
                                seeds = seeds.replace("\'", "")
                                seeds_list = seeds[1:-1].split(',')

                                sol = ["size", solution[1]] + \
                                    ["Set of seeds",seeds_list]
                                if self.network.is_community:
                                    transferred_list = eval(solution[5]) 
                                    sol += ["Set of transferred", transferred_list]

                                cobra_dict = loads(solution[4].replace("'",'"'))
                                sol += ["Cobra flux",  cobra_dict]
                                solution_list[solution[0]] = sol
                            #get the last occurence pf rejected solutions number
                            number_rejected = solution[3]
                    logger.print_log(f'Rejected solution during process: at least {number_rejected} \n', 'info')
                except Exception as e:
                    logger.print_log(f"An error occured while reading temporary file\n {full_path}:\n {e}", 'error')

                if any(solution_list):
                    for name in solution_list:
                        seeds = solution_list[name][3]
                        self.network.add_result_seeds('REASONING '+suffix, search_mode, name, len(seeds), seeds, transferred_list=transferred_list)
                delete(full_path)
        return solution_list, number_rejected
    


    def solve_hybrid(self, step:str, full_option:list, asp_files:list, search_mode:str, is_one_model:bool):
        """Solve hybrid-cobra mode depending step (filter, guess_check, guess_check_div)

        Args:
            step (str): Hybrid solving mode (filter, guess_check, guess_check_div)
            full_option (list): List of clingo options
            asp_files (list): list of path to asp files
            search_mode (str): Search mode (minimize or subset minimal)
            is_one_model (bool): Determine if the model is the optimum finding model for minimize case

        Returns:
            int, int, dict, str: time_solve, time_ground, solution_list, number_rejected
        """
        # api clingo doesn't have time_limit option
        # to add a time out, it is needed to call the function into a process
        queue = Queue()
        start=time()
        if step == "filter":
            suffix = " FILTER"
            full_path = path.join(self.temp_dir,f"{self.temp_result_file}.tsv")
            p = Process(target=self.filter, args=(queue, full_option, asp_files, search_mode, full_path, is_one_model))
        elif "guess_check" in step:
            suffix = " GUESS-CHECK"
            self.diversity=False
            if step == "guess_check_div":
                suffix += "-DIVERSITY"
                self.diversity=True
            full_path = path.join(self.temp_dir,f"{self.temp_result_file}.tsv")
            p = Process(target=self.guess_check, args=(queue, full_option, asp_files, search_mode, full_path, is_one_model))
        
        p.start()
        try:
            # the time out limit is added here
            obj, solution_list, time_ground, time_solve, number_rejected = queue.get(timeout=self.time_limit)
            #solution_list, number_rejected = self.get_solution_from_temp(unsat, is_one_model, full_path, suffix, search_mode)
            
            # Because of the process, the object is not change (encapsulated and isolated)
            # it is needed to give get the output object and modify the current object
            if "minimize" in search_mode:
                self.optimum_found = obj.optimum_found
                self.optimum = obj.optimum
                self.get_separate_optimum()
            self.network.result_seeds = obj.network.result_seeds 
            if not is_one_model:
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
            
            solution_list, number_rejected = self.get_solution_from_temp(unsat, is_one_model, full_path, suffix, search_mode)
        p.terminate()
        queue.close()

        if is_one_model:
            if not self.optimum_found:
                logger.print_log('Optimum not found', "error") 
        else:
            if not any(solution_list): 
                logger.print_log('Unsatisfiable problem', "error")

        return time_solve, time_ground, solution_list, number_rejected
    

    def print_answer(self, message:str, seeds:list, seeds_full:list, trans_complete:str):
        """Print into terminal the answer (set of seeds and transfers if exists)

        Args:
            message (str): Constructed message to print
            seeds (list): list of seeds
            seeds_full (list): list of seeds wit all data from asp atoms answer (species associated)
            trans_complete (str): List of transfers with all data (metabolite, from, to)
        """
        if not self.network.is_community:
            for s in seeds:
                message += f"{s}, "
            message=message.rstrip(', ')
        else:
            seeds_dict=dict()
            seeds_full = sorted(seeds_full, key=lambda x: x[0])
            for s in seeds_full:
                species = str(s[3]).replace('"','')
                seed = str(s[2]).replace('"','')
                if species in seeds_dict.keys():
                    seeds_dict[species]+= f', {seed}'
                else:
                    seeds_dict[species] = f'{seed}'
            for key, value in sorted(seeds_dict.items()):
                message += color.cyan_dark + f'{key}:' + color.reset
                message += f' {value}'
                message = message.rstrip(', ')
                message += "\n"
            if  trans_complete is None:
                trans_complete=color.yellow+"No transferred metabolites\n"+color.reset
            message += trans_complete #+ "\n"
        print(message)
    
    def temp_rejected(self, number_rejected:int, full_path:str):
        """Save temporary data for rejected number of solution when using cobra hybrid mode

        Args:
            number_rejected (int): _description_
            full_path (str): Path of temporary file
        """
        solution_temp = [None, None, None, number_rejected, None]
        if self.network.is_community:
            solution_temp.append(None)
        save(full_path, "", solution_temp, "tsv", True)

    def filter(self, queue:Queue, full_option:list, asp_files:list, search_mode:str, full_path:str, is_one_model:bool=False):
        """Filter mode. Find a solution with Clingo package, check if the solution has flux on objective reaction.
        This function works with multiprocessing in order to manage time limit.
        It does not interact with the solver, only filter the solutions.

        Args:
            queue (Queue): Queue for multiprocessing program (managing time limit)
            full_option (list): All Clingo option 
            asp_files (list): List of needed ASP files to solve ASP (Clingo package)
            search_mode (str): Optimization selected for the search (submin/minmize and enumeration/optimum)
            full_path (str): Full path for temp file needed to get back solution when time out
            is_one_model (bool, optional): Define if the solution we want is to fin the optimum when minimize is used (before enumration).
                                         Defaults to False.
        """
        solution_list = dict()

        no_limit_solution = False
        if self.number_solution == 0:
            no_limit_solution = True

        full_option_seeds = self.complete_option(full_option,0)
        
        ctrl = self.control_init(full_option_seeds, asp_files)
        solution_idx = 1
        number_rejected = 0
        start_time=time()
        with ctrl.solve(yield_=True) as h:
            for model in h:
                if (len(solution_list) < self.number_solution \
                   and not is_one_model and not no_limit_solution) \
                    or is_one_model or no_limit_solution:
                    atoms = model.symbols(shown=True)
                    seeds, seeds_full, transferred, _ = self.get_seeds_transfers(atoms)
                    size = len(seeds)
                    transf_short, trans_complete, trans_solution_list =self.get_transfers_info(transferred)

                    if not is_one_model:
                        res = self.network.check_seeds(seeds, trans_solution_list)
                        if res[0]:
                            # valid solution
                            logger.print_log(f'CHECK Solution {size} seeds -> OK\n', 'debug')
                            
                            message = color.cyan_light + f"Answer: {solution_idx}{color.reset} ({size} seeds{transf_short})\n"
                            self.print_answer(message, seeds, seeds_full, trans_complete)
                            name = 'model_'+str(solution_idx)
                            
                            solution_list, solution_temp = self.complete_solutions(solution_list, name, size, seeds, 
                                    trans_solution_list, res[1], number_rejected)

                            save(full_path, self.temp_dir, solution_temp, "tsv", True)
                            self.network.add_result_seeds('REASONING FILTER', search_mode, name, size, seeds, flux_cobra=res[1], transferred_list=trans_solution_list)
                            solution_idx +=1
                        else:
                            logger.print_log(f'CHECK Solution {size} seeds -> KO\n', 'debug')
                            number_rejected +=1
                            current_timer = time() - start_time
                            # write all 100 rejected 
                            # or write from 5 minute before finishing the process near to finish  the process
                            if number_rejected%100 == 0 \
                            or (current_timer!=0 and current_timer > self.time_limit_minute*60 - 300):
                                self.temp_rejected(number_rejected, full_path)
                    # This means we are in "is_one_model", we are searching for minimize
                    # there is no minimize with community mode
                    else:
                        res = self.network.check_seeds(seeds, transferred)
                        self.optimum=model.cost
                        self.get_separate_optimum()
                        name = 'model_one_solution'
                        solution_list, solution_temp = self.complete_solutions(solution_list, name, size, seeds, 
                            trans_solution_list, res[1], number_rejected)
                        self.optimum_found = True
                else:
                    break
            
        logger.print_log(f'Rejected solution during process: {number_rejected} \n', "info")

        stats = ctrl.statistics
        total_time = stats["summary"]["times"]["total"]
        time_solve = stats["summary"]["times"]["solve"]
        time_ground = total_time - time_solve

        # Because it is needed to get all answers from clingo to have optimum, we save it after
        # No minimize in community mode
        if is_one_model and self.optimum_found:
            logger.print_log(f"Optimum found.", "info") 
            if self.network.is_subseed:
                logger.print_log(f"Number of producible targets: {- self.opt_prod_tgt}", "info")
            logger.print_log(f"Minimal size of seed set is {self.opt_size}\n", "info")
            save(full_path, self.temp_dir, solution_temp, "tsv", True)               
            self.network.add_result_seeds('REASONING FILTER', search_mode, name, size, seeds, flux_cobra=res[1], transferred_list=trans_solution_list) 

        ctrl.cleanup()
        ctrl.interrupt()
        queue.put([self, solution_list, time_ground, time_solve, number_rejected])
    

    def guess_check_constraints(self, ctrl, atoms, seeds:list, avoided:list):
        """Add constraints to clingo controller for guess Check mode, and supplementary constraints for diversity mode.

        Args:
            ctrl: clingo controller to add constraints
            atoms: clingo atoms
            seeds (list): list of seeds
            avoided (list): list of previous avoided seeds

        Returns:
            clingo controller, str, list: ctrl, mode, avoided (list of new avoided seeds)
        """
        if atoms:
            if self.diversity: 
                ctrl, avoided = self.add_diversity(ctrl, seeds, avoided) 
            # exclude solution and its superset
            ctrl.add("skip", [], f":- {','.join(map(str,atoms))}.")
            ##################################################
            # exclude only solution, keep superset
            # not used because superset are so much that it founds less solutions 
            # than when we delete the superset (more networks work, more solution
            # found per network)
            # code kept in case it is needed

            #ctrl.add("skip", [], f":- {','.join(map(str,atoms))}, #count{{M: seed(M,_)}} = {len(atoms)}.")
            ##################################################
            ctrl.ground([("skip",[])])
        return ctrl, avoided
        

    def get_gc_mode(self):
        mode = 'REASONING GUESS-CHECK'
        if self.diversity: 
            mode =  'REASONING GUESS-CHECK DIVERSITY'
        return mode


    def guess_check(self, queue:Queue, full_option:list, asp_files:list, search_mode:str, full_path:str, is_one_model:bool=False):
        """Guess and Check mode. Find a solution with Clingo package, check if the solution has flux on objective reaction.
        This function works with multiprocessing in order to manage time limit.
        Interacts with ASP solver and exclude supersets of the current tested solution.
        If diversity is asked, the function add_diversity is called.

        Args:
            queue (Queue): Queue for multiprocessing program (managing time limit)
            full_option (list): All Clingo option 
            asp_files (list): List of needed ASP files to solve ASP (Clingo package)
            search_mode (str): Optimization selected for the search (submin/minmize and enumeration/optimum)
            full_path (str): Full path for temp file needed to get back solution when time out
            is_one_model (bool, optional): Define if the solution we want is to fin the optimum when minimize is used (before enumration).
                                         Defaults to False.
        """
        solution_list = dict()
        avoided = []
        all_time_solve = 0
        all_time_ground = 0

        # No limit on number of solution
        no_limit_solution = False
        if self.number_solution == 0:
            no_limit_solution = True

        full_option_seeds = self.complete_option(full_option,0)

        ctrl = self.control_init(full_option_seeds, asp_files, True)
        solution_idx = 1
        number_rejected = 0
        start_time = time()
        while ((len(solution_list) < self.number_solution \
                    and not is_one_model and not no_limit_solution) \
                    or is_one_model or no_limit_solution )\
                and \
                (self.time_limit and float(all_time_ground + all_time_solve) < float(self.time_limit)
                 or not self.time_limit):
            with ctrl.solve(yield_=True) as h:
                seeds = list()
                transferred = list()
                for model in h:
                    atoms = model.symbols(shown=True)
                    
                    seeds, seeds_full, transferred, _ = self.get_seeds_transfers(atoms)
                    size = len(seeds)

                    transf_short, trans_complete, trans_solution_list =self.get_transfers_info(transferred)

                    # is_one_model is for minimize.
                    # Community doesn't have minimize
                    if not is_one_model:
                        break
                    else:
                        self.optimum=model.cost
                if not seeds:
                    if is_one_model:
                        name = 'model_one_solution'
                        solution_list[name] = ["size", 0] + \
                                ["Set of seeds", []]
                        self.optimum_found = True
                    else:
                        if transferred:
                            transf_short, trans_complete, trans_solution_list = self.get_transfers_info(transferred)
                        else:
                            transf_short = trans_complete = "" 
                            trans_solution_list = list()
                    break
            # Sum all grounding time together and all solving time together
            stats = ctrl.statistics
            total_time = stats["summary"]["times"]["total"]
            time_solve = stats["summary"]["times"]["solve"]
            time_ground  = total_time - time_solve

            all_time_solve += float(time_solve)
            all_time_ground += float(time_ground)
            res = self.network.check_seeds(seeds, trans_solution_list)
            if res[0]:
                logger.print_log(f'CHECK Solution {size} seeds -> OK\n', 'debug')
                # valid solution
                if not is_one_model:
                    message = color.cyan_light + f"Answer: {solution_idx}{color.reset} ({size} seeds{transf_short})\n"
                    self.print_answer(message, seeds, seeds_full, trans_complete)
                    name = 'model_'+str(solution_idx)

                    solution_list, solution_temp = self.complete_solutions(solution_list, name, size, seeds, 
                           trans_solution_list, res[1], number_rejected)
                    save(full_path, "", solution_temp, "tsv", True)
                    # exclude solutions and its supersets
                    ctrl, avoided= self.guess_check_constraints(ctrl, atoms, seeds, avoided)
                    mode = self.get_gc_mode()
                    self.network.add_result_seeds(mode, search_mode, name, size, seeds, flux_cobra=res[1], transferred_list=trans_solution_list)
                    solution_idx +=1
                else:
                    name = 'model_one_solution'
                    solution_list, solution_temp = self.complete_solutions(solution_list, name, size, seeds, 
                           trans_solution_list, res[1], number_rejected)
                    logger.print_log(f"Optimum found.", "info") 
                    self.optimum_found = True
                    mode = 'REASONING GUESS-CHECK'
                    # Do not exclude superset because we will rerun the minimize by set the size
                    # and we want to find back this first minimize found
                    if self.diversity: 
                        ctrl, avoided = self.add_diversity(ctrl, seeds, avoided) 
                        mode =  'REASONING GUESS-CHECK DIVERSITY'
                    save(full_path, self.temp_dir, solution_temp, "tsv", True)

                    self.network.add_result_seeds(mode, search_mode, name, size, seeds, flux_cobra=res[1], transferred_list=trans_solution_list)
                    self.get_separate_optimum()
                    if self.network.is_subseed:
                        logger.print_log(f"Number of producible targets: {- self.opt_prod_tgt}", "info")
                    logger.print_log(f"Minimal size of seed set is {self.opt_size}\n", "info")
                    break
                
            else:
                logger.print_log(f'CHECK Solution {size} seeds -> KO\n', 'debug')
                #logger.print_log(f'{seeds}\n', 'debug')
                
                ctrl, avoided= self.guess_check_constraints(ctrl, atoms, seeds, avoided)
                mode = self.get_gc_mode()
                number_rejected +=1

                current_timer = time() - start_time
                # write all 100 rejected 
                # or write from 5 minute before finishing the process near to finish  the process
                if number_rejected%100 == 0 \
                or (current_timer!=0 and current_timer > self.time_limit_minute*60 - 300):
                    self.temp_rejected(number_rejected, full_path)

        # Needed when all solutions are rejected and not 100 solution tested
        # to retrieve the last number rejected and save into temp file        
        if not existing_file(full_path):
            solution_temp = [None, None, None, number_rejected, None, None]

        if not is_one_model:
            save(full_path, "", solution_temp, "tsv", True)
            logger.print_log(f'Rejected solution during process: {number_rejected} \n', 'info')

        ctrl.cleanup()
        ctrl.interrupt()
        queue.put([self, solution_list, all_time_ground, all_time_solve, number_rejected])

    ######################################################## 