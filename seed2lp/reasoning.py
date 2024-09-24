# Object Reasoning, herit from Solver, added properties:
#    - grounded (str): All rules grounded before solving to save time

import clyngor
import clingo
from time import time
from .network import Network
from .solver import Solver
import random
from multiprocessing import Process, Queue
from .file import save, delete, load_tsv, existing_file
from os import path
from . import color, logger


#TODO: CLEAN GROUND MODE IF NOT USED
GROUND = False


###################################################################
################# Class Reasoning : herit Solver ################## 
###################################################################
class Reasoning(Solver):
    def __init__(self, run_mode:str, run_solve:str, network:Network,
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None, 
                 intersection:bool=False, union:bool=False, 
                 minimize:bool=False, subset_minimal:bool=False, 
                 temp_dir:str=None, short_option:str=None, 
                 verbose:bool=False):
        """Initialize Object Reasoning, herit from Solver

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
                         temp_dir, short_option, run_solve, verbose)

        self.is_linear = False
        title_mess = "\n############################################\n" \
            "############################################\n" \
            f"                   {color.bold}REASONING{color.cyan_light}\n"\
            "############################################\n" \
            "############################################\n"
        logger.print_log(title_mess, "info", color.cyan_light) 
        self._set_clingo_constant()
        self._set_instance_file()
        self._set_temp_result_file()



    ######################## SETTER ########################
    def _set_clingo_constant(self):
        """Prepare ASP constant command for resolution
        """
        self.init_const()
        logger.print_log(f"Time limit: {self.time_limit_minute} minutes", "info")
        logger.print_log( f"Solution number limit: {self.number_solution}", "info")
    ########################################################  


    ######################## METHODS ########################
    def reinit_optimum(self):
        """Reinit optimum data to launch all modes
        """
        self.optimum = None
        self.optimum_found = False
        self.opt_prod_tgt = None
        self.opt_size = None

    def search_seed(self):  
        """Launch seed searching 
        """
        files = [self.network.instance_file, self.asp.ASP_SRC_SEED_SOLVING]
        timer=dict()
        # Subset minimal mode: By default the sub_seeds search from possible seed given is deactivated
        if self.subset_minimal:
            self.get_message('subsetmin')
            if GROUND: 
                timer = self.reasoning_ground(files)
            if self.run_solve == "reasoning" or self.run_solve ==  "all":
                self.get_message('classic')
                self.search_subsetmin(timer, files, 'classic')

            if self.run_solve == "filter" or self.run_solve ==  "all":
                self.get_message('filter')
                self.search_subsetmin(timer, files, 'filter')

            if self.run_solve == "guess_check" or self.run_solve ==  "all":
                self.get_message('guess_check')
                self.search_subsetmin(timer, files, 'guess_check')

            if self.run_solve == "guess_check_div" or self.run_solve ==  "all":
                self.get_message('guess_check_div')
                self.search_subsetmin(timer, files, 'guess_check_div')


        if self.minimize:
            self.get_message('minimize')
            if self.network.is_subseed:
                files.append(self.asp.ASP_SRC_MAXIMIZE_PRODUCED_TARGET)
                logger.print_log('POSSIBLE SEED: Given\n  A subset of possible seed is search \n  maximising the number of produced target', 'info')
                self.clingo_constant.append('-c')
                self.clingo_constant.append('subseed=1')                
            files.append(self.asp.ASP_SRC_MINIMIZE)

            if GROUND: 
                timer = self.reasoning_ground(files)

            if self.run_solve == "reasoning" or self.run_solve ==  "all":
                self.get_message('classic')
                self.search_minimize(timer, files, 'classic')
                self.reinit_optimum()

            if self.run_solve == "filter" or self.run_solve ==  "all":
                self.get_message('filter')
                self.search_minimize(timer, files, 'filter')
                self.reinit_optimum()

            if self.run_solve == "guess_check" or self.run_solve ==  "all":
                self.get_message('guess_check')
                self.search_minimize(timer, files, 'guess_check')
                self.reinit_optimum()


            if self.run_solve == "guess_check_div" or self.run_solve ==  "all":
                self.get_message('guess_check_div')
                self.search_minimize(timer, files, 'guess_check_div')
                self.reinit_optimum()
            self.get_message('end')


    
    def reasoning_ground(self, asp_files:list):
        """Ground the ASP files to create all facts from rules

        Args:
            asp_files (list): List of ASP files, included th network asp file saved in temp directory
        """
        timer = dict()
        logger.print_log('GROUNDING...', 'info')
        time_ground = time()
        const_option = ""
        const_option = ' '.join(self.clingo_constant)
        self.grounded = clyngor.grounded_program(asp_files, options=const_option)
        time_ground = time() - time_ground
        timer["Grounding time"] = round(time_ground, 3)
        return timer
    

        
    def write_one_model_solution(self, one_model:dict):
        """Construct the outpu for minimize one model solution (finding optimum step)

        Args:
            one_model (dict): Solution of finding opimum step

        Returns:
            solution_list (dict): Constructed output
        """
        solution_list = dict()
        seeds = list()
        
        if self.optimum is None:
            logger.print_log('\tNo seed found', 'info')
        else: 
            self.get_separate_optimum()
            logger.print_log(f"Optimum found.", "info") 
            if self.network.is_subseed:
                logger.print_log((f"Number of producible targets: {- self.opt_prod_tgt}"), 'info')
            logger.print_log(f"Minimal size of seed set is {self.opt_size}\n", 'info')
            if self.opt_size > 0:
                seeds = [args[0] for args in one_model.get('seed', ())]
                seeds=list(sorted(seeds))
            else:
                seeds = []
                if self.network.keep_import_reactions:
                    logger.print_log("Try with the option remove import reactions.", 'info')
            #logger.print_log(f"\nOne solution:\n{', '.join(map(str, seeds))}\n", 'info')
            solution_list['model_one_solution'] = ["size", self.opt_size] + \
                                    ["Set of seeds", seeds]

        return solution_list, seeds
    

    def search_minimize(self,  timer:dict, asp_files:list=None, step:str="classic"):
        """Launch seed searching with minimze options

        Args:
            timer (dict): Timer dictionnary containing grouding time
        """
        logger.print_log("Finding optimum...", "info")
        self.solve("minimize-one-model", timer, asp_files, step, True)

        if not self.optimum_found:
            return
        
        if self.optimum == 0:
            opti_message = "Optimum is 0."

        ok_opti = self.optimum_found and (self.opt_size > 0)
        if self.intersection:    
            if ok_opti:
                self.get_message('intersection')
                self.solve("minimize-intersection", timer, asp_files, step)
            else:
                self.get_message('intersection')
                logger.print_log(f"\nNot computed: {opti_message}", "error") 
            
        if self.union:       
            if ok_opti:
                self.get_message('union')
                self.solve("minimize-union", timer, asp_files, step)
            else:
                self.get_message('union')
                logger.print_log(f"\nNot computed: {opti_message}", "error") 

        if self.enumeration: 
            if ok_opti:
                self.get_message('enumeration')  
                self.solve("minimize-enumeration", timer, asp_files, step)
            else:
                self.get_message('enumeration') 
                logger.print_log(f"\nNot computed: {opti_message}", "error")


    def search_subsetmin(self, timer:dict, asp_files:list=None, step:str="classic"):
        """Launch seed searching with subset minimal options

        Args:
            timer (dict): Timer dictionnary containing grouding time
        """
        if self.enumeration:
            self.get_message('enumeration') 
            self.solve("submin-enumeration", timer, asp_files, step)
        else:
            self.number_solution = 1
            self.get_message('One solution')   
            self.solve("submin-enumeration", timer, asp_files, step)

        if self.intersection: 
            self.get_message('intersection')
            logger.print_log("SOLVING...\n", "info")
            self.solve("submin-intersection", timer, asp_files, step)
        


    def solve(self, search_mode:str, timer:dict, asp_files:list=None, step:str="classic", is_one_model:bool=False):
        """Solve the seed searching using the launch mode

        Args:
            search_mode (str, optional): Describe the launch mode.
            timer (dict): Timer dictionnary containing grouding time
        """
        logger.print_log("SOLVING...\n", "info")
        results = dict()
        one_model = None
        number_rejected = None
        solution_list = dict()
        full_option, mode_message, model_type, output_type = self.get_solutions_infos(search_mode)
        
        if not GROUND:
            full_option = self.clingo_constant + full_option

        if self.optimum:
            if self.opt_prod_tgt is not None:
                full_option[-1]=full_option[-1]+f",{self.opt_prod_tgt},{self.opt_size}"
            else:
                full_option[-1]=full_option[-1]+f",{self.opt_size}"

        str_option = ' '.join(full_option)
        suffix=""
        if step == "filter":
            suffix = " FILTER"
        elif step == "guess_check":
                suffix = " GUESS-CHECK"
        match search_mode, step:
            # CLASSIC MODE (NO FILTER, NO GUESS-CHECK)   
            case "minimize-one-model", "classic":
                time_solve = time()
                if GROUND:
                    models = clyngor.solve_from_grounded(self.grounded, options=str_option, 
                                    time_limit=self.time_limit).discard_quotes.by_predicate
                else:
                    models = clyngor.solve(files=asp_files, options=str_option, 
                                    time_limit=self.time_limit).discard_quotes.by_predicate
                time_solve = time() - time_solve
                self.get_message("command")
                logger.print_log(f'{models.command}', 'debug')
                for model, opt, optimum_found in models.by_arity.with_optimality:
                    if optimum_found:
                        self.optimum_found = True
                        one_model = model
                        if one_model.get('seed'):
                            self.optimum = opt
                        else:
                            self.optimum = 0
                if not self.optimum_found:
                    logger.print_log('Optimum not found', "error") 
                else:
                    solution_list, seeds = self.write_one_model_solution(one_model)
                    self.network.add_result_seeds('REASONING', search_mode, model_type, len(seeds), seeds)

            case "minimize-enumeration" | "submin-enumeration", "classic":
                time_solve = time()
                solution_list = self.solve_enumeration(str_option, solution_list, 
                                                        search_mode, asp_files)
                time_solve = time() - time_solve


            case _, "classic":
                time_solve = time()
                if GROUND:
                    models = clyngor.solve_from_grounded(self.grounded, options=str_option, 
                                    time_limit=self.time_limit).discard_quotes.by_predicate
                else:
                    models = clyngor.solve(files=asp_files, options=str_option, 
                                    time_limit=self.time_limit).discard_quotes.by_predicate
                time_solve = time() - time_solve
                self.get_message("command")
                logger.print_log(f'{models.command}', 'debug')
                has_solution=False
                for model in models:
                    has_solution=True
                    _models = [model]
                if has_solution:
                    models = _models
                    seeds = [args[0] for args in models[0].get('seed', ())]
                    seeds=list(sorted(seeds))
                    size = len(seeds)
                    print(f"Answer: {mode_message} ({size} seeds) \n{', '.join(map(str, seeds))}\n")
                    solution_list[model_type] = ["size", len(seeds)] + \
                                ["Set of seeds", seeds]
                    self.network.add_result_seeds('REASONING', search_mode, model_type, len(seeds), seeds)
                else:
                    logger.print_log('Unsatisfiable problem', "error") 

            # FILTER OR GUESS-CHECK mode
            #TODO redo intersection and union mode
            case _, "filter"| "guess_check" | "guess_check_div":
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

      
        #TODO: Intersection and union not needed with filter and guess check but 
        # do with python the union and intersection of resulted soluion of filer or guess check

        if step == "filter" or "guess_check" in step:
            if time_ground != -1:
                timer["Grounding time"] = round(time_ground, 3)
            else:
                timer["Grounding time"] = "Time out"
        if time_solve != -1:
            timer["Solving time"] = round(time_solve, 3)
        else:
            timer["Solving time"] = "Time out"      
        results["Timer"] = timer.copy()
        results['solutions'] = solution_list
        if number_rejected:
            results['rejected'] = number_rejected
        self.output[output_type+suffix] = results


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
            List: list of solutions
        """
        solution_list = dict()
        number_rejected = None

        if not unsat and existing_file(full_path):
        # in case of enumeration it is needed to get the results back from the saved temporary
        # file which is saved during the called 
            if not is_one_model:
                try:
                    temp_list = load_tsv(full_path)
                    for solution in temp_list:
                        if len(solution) == 5:
                            # some line has no data value onlu the number of rejected solution
                            if solution[0]:
                                seeds = solution[2].replace(" ", "")
                                seeds = seeds.replace("\'", "")
                                seeds_list = seeds[1:-1].split(',')
                                solution_list[solution[0]] = ["size", solution[1]] + \
                                    ["Set of seeds",seeds_list] + ["Cobra flux",  float(solution[4])]
                            #get the last occurence pf rejected solutions number
                            number_rejected = solution[3]
                    logger.print_log(f'Rejected solution during process: at least {number_rejected} \n', 'info')
                except Exception as e:
                    logger.print_log(f"An error occured while reading temporary file\n {full_path}:\n {e}", 'error')

                if any(solution_list):
                    for name in solution_list:
                        seeds = solution_list[name][3]
                        self.network.add_result_seeds('REASONING '+suffix, search_mode, name, len(seeds), seeds)
                delete(full_path)
        return solution_list, number_rejected


    def solve_enumeration(self, construct_option:str, solution_list:dict, 
                          search_mode:str, asp_files:list=None):
        """Solve enumeration for Reasoning Classic mode using Clyngor

        Args:
            construct_option (str): Constructed option for clingo
            solution_list (dict): A dictionnary of all found solutions
            search_mode (str): Optimization selected for the search (submin-enumeration / minimze-enumeration)
            asp_files (list, optional): List of needed ASP files to solve ASP with Clyngor

        Returns:
            solution_list (dict): a dictionnary of all found solutions
        """
        if GROUND:
            models = clyngor.solve_from_grounded(self.grounded, options=construct_option, 
                                time_limit=self.time_limit, nb_model=self.number_solution).discard_quotes.by_predicate
        else:
            models = clyngor.solve(files=asp_files, options=construct_option, 
                                time_limit=self.time_limit, nb_model=self.number_solution).discard_quotes.by_predicate
        self.get_message("command")
        logger.print_log(f'{models.command}', 'debug')
        idx = 1
        m = models
        models_list = list(m).copy()
        size_answers = len(models_list)
        if size_answers != 0:
            for model in models_list:
                seeds = [args[0] for args in model.get('seed', ())]
                seeds=list(sorted(seeds))
                repr_seeds = ', '.join(map(str, seeds))
                size = len(seeds)

                print(f"Answer: {idx} ({size} seeds) \n{repr_seeds}\n")
                solution_list['model_'+str(idx)] = ["size", size] + \
                            ["Set of seeds", seeds]
                self.network.add_result_seeds('REASONING', search_mode, 'model_'+str(idx), size, seeds)
                idx += 1
        else:
            logger.print_log('Unsatisfiable problem', "error")
        return solution_list



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
        number_solution = self.number_solution

        ctrl = self.control_init(full_option, asp_files, True)
        solution_idx = 1
        number_rejected = 0
        while ((len(solution_list) < number_solution \
                    and not is_one_model and not no_limit_solution) \
                    or is_one_model or no_limit_solution )\
                and \
                (self.time_limit and float(all_time_ground + all_time_solve) < float(self.time_limit)
                 or not self.time_limit):
            with ctrl.solve(yield_=True) as h:
                seeds = None
                for model in h:
                    atoms = model.symbols(shown=True)
                    seeds = {a.arguments[0].string for a in atoms}
                    seeds=list(sorted(seeds))
                    size = len(seeds)
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
                    break
            # Sum all grounding time together and all solving time together
            stats = ctrl.statistics
            total_time = stats["summary"]["times"]["total"]
            time_solve = stats["summary"]["times"]["solve"]
            time_ground  = total_time - time_solve

            all_time_solve += float(time_solve)
            all_time_ground += float(time_ground)
            res = self.network.check_seeds(seeds)
            if res[0]:
                logger.print_log(f'CHECK Solution {size} seeds -> OK\n', 'debug')
                # valid solution
                if not is_one_model:
                    message = f"Answer: {solution_idx} ({size} seeds)\n"
                    for s in seeds:
                        message += f"{s}, "
                    message=message.rstrip(', ')
                    print(message + "\n")
                    name = 'model_'+str(solution_idx)
                    solution_list[name] = ["size", size] + \
                                ["Set of seeds", seeds] + ["Cobra flux",  res[1]]
                    solution_temp = [name, size, seeds, number_rejected, res[1]]
                    save(full_path, "", solution_temp, "tsv", True)
                    # exclude solutions and its supersets
                    ctrl.add("skip", [], f":- {','.join(map(str,atoms))}.")
                    mode = 'REASONING GUESS-CHECK'
                    if self.diversity:
                        ctrl, avoided = self.add_diversity(ctrl, seeds, avoided)
                        mode =  'REASONING GUESS-CHECK DIVERSITY'
                    ctrl.ground([("skip",[])])
                    self.network.add_result_seeds(mode, search_mode, name, size, seeds, flux_cobra=res[1])
                    solution_idx +=1
                else:
                    name = 'model_one_solution'
                    solution_list[name] = ["size", size] + \
                                ["Set of seeds", seeds] + ["Cobra flux",  res[1]]
                    logger.print_log(f"Optimum found.", "info") 
                    self.optimum_found = True
                    if self.diversity: 
                        ctrl, avoided = self.add_diversity(ctrl, seeds, avoided) 
                    solution_temp = [name, size, seeds, number_rejected, res[1]]
                    save(full_path, self.temp_dir, solution_temp, "tsv", True)
                    mode = 'REASONING GUESS-CHECK'
                    if self.diversity:
                        mode =  'REASONING GUESS-CHECK DIVERSITY'
                    self.network.add_result_seeds(mode, search_mode, name, size, seeds, flux_cobra=res[1])
                    self.get_separate_optimum()
                    if self.network.is_subseed:
                        logger.print_log(f"Number of producible targets: {- self.opt_prod_tgt}", "info")
                    logger.print_log(f"Minimal size of seed set is {self.opt_size}\n", "info")
                    break
                
            else:
                logger.print_log(f'CHECK Solution {size} seeds -> KO\n', 'debug')
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
                number_rejected +=1

                if number_rejected%100 == 0:
                    solution_temp = [None, None, None, number_rejected, None]
                    save(full_path, "", solution_temp, "tsv", True)
                
        if number_rejected > 0:
            logger.print_log(f'Rejected solution during process: {number_rejected} \n', 'info')

        ctrl.cleanup()
        ctrl.interrupt()
        queue.put([self, solution_list, all_time_ground, all_time_solve, number_rejected])


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
        full_option.append(f'-n 0')
        number_solution = self.number_solution

        ctrl = self.control_init(full_option, asp_files)

        solution_idx = 1
        number_rejected = 0
        with ctrl.solve(yield_=True) as h:
            for model in h:
                seeds = None
                if (len(solution_list) < number_solution \
                   and not is_one_model and not no_limit_solution) \
                    or is_one_model or no_limit_solution:
                    atoms = model.symbols(shown=True)
                    seeds = {a.arguments[0].string for a in atoms}
                    seeds=list(sorted(seeds))
                    size = len(seeds)
                    #if not seeds:
                    #    print("No seeds")
                    #    if is_one_model:
                    #        name = 'model_one_solution'
                    #        solution_list[name] = ["size", 0] + \
                    #                ["Set of seeds", []]
                    #        self.optimum_found = True
                    #    break

                    if not is_one_model:
                        res = self.network.check_seeds(seeds)
                        if res[0]:
                        # valid solution
                            logger.print_log(f'CHECK Solution {size} seeds -> OK\n', 'debug')
                            message = f"Answer: {solution_idx} ({size} seeds)\n"
                            for s in seeds:
                                message += f"{s}, "
                            message=message.rstrip(', ')
                            print(message + "\n")
                            name = 'model_'+str(solution_idx)
                            solution_list[name] = ["size", size] + \
                                        ["Set of seeds", seeds] + ["Cobra flux",  res[1]]
                            solution_temp = [name, size, seeds, number_rejected, res[1]]
                            save(full_path, self.temp_dir, solution_temp, "tsv", True)
                            self.network.add_result_seeds('REASONING FILTER', search_mode, name, size, seeds, flux_cobra=res[1])
                            solution_idx +=1
                        else:
                            logger.print_log(f'CHECK Solution {size} seeds -> KO\n', 'debug')
                            number_rejected +=1
                            if number_rejected%100 == 0:
                                solution_temp = [None, None, None, number_rejected, None]
                                save(full_path, "", solution_temp, "tsv", True)
                    else:
                        res = self.network.check_seeds(seeds)
                        self.optimum=model.cost
                        self.get_separate_optimum()
                        name = 'model_one_solution'
                        solution_list[name] = ["size", self.opt_size] + \
                                    ["Set of seeds", seeds] + ["Cobra flux",  res[1]]
                        self.optimum_found = True
                else:
                    break
                
        if number_rejected > 0:
            logger.print_log(f'Rejected solution during process: {number_rejected} \n', "info")

        stats = ctrl.statistics
        total_time = stats["summary"]["times"]["total"]
        time_solve = stats["summary"]["times"]["solve"]
        time_ground = total_time - time_solve

        # Because it is needed to get all answers from clingo to have optimum, we save it after
        if is_one_model and self.optimum_found:
            logger.print_log(f"Optimum found.", "info") 
            if self.network.is_subseed:
                logger.print_log(f"Number of producible targets: {- self.opt_prod_tgt}", "info")
            logger.print_log(f"Minimal size of seed set is {self.opt_size}\n", "info")
            solution_temp = [name, size, seeds, number_rejected, res[1]]
            save(full_path, self.temp_dir, solution_temp, "tsv", True)               
            self.network.add_result_seeds('REASONING FILTER', search_mode, name, size, seeds, flux_cobra=res[1]) 

        ctrl.cleanup()
        ctrl.interrupt()
        queue.put([self, solution_list, time_ground, time_solve, number_rejected])



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
