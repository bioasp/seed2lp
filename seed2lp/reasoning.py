# Object Reasoning, herit from Solver, added properties:
#    - grounded (str): All rules grounded before solving to save time

import clyngor
from time import time
from .network import Network
from .reasoninghybrid import HybridReasoning
from . import color, logger


###################################################################
############ Class Reasoning : herit HybridReasoning ############## 
###################################################################
class Reasoning(HybridReasoning):
    def __init__(self, run_mode:str, run_solve:str, network:Network,
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None, 
                 intersection:bool=False, union:bool=False, 
                 minimize:bool=False, subset_minimal:bool=False, 
                 temp_dir:str=None, short_option:str=None, 
                 verbose:bool=False, community_mode:str=None,
                 all_transfers:bool=False):
        """Initialize Object Reasoning, herit from HybridReasoning

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
                         temp_dir, short_option, run_solve, verbose, community_mode, all_transfers)

        self.is_linear = False
        title_mess = "\n############################################\n" \
            "############################################\n" \
            f"                   {color.bold}REASONING{color.cyan_light}\n"\
            "############################################\n" \
            "############################################\n"
        logger.print_log(title_mess, "info", color.cyan_light) 
        self._set_clingo_constant()
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
        self.asp_files.append(self.asp.ASP_SRC_SHOW_SEEDS)
        
        timer=dict()
        # Subset minimal mode: By default the sub_seeds search from possible seed given is deactivated
        if self.subset_minimal:
            self.get_message('subsetmin')
            if self.ground: 
                timer = self.reasoning_ground(self.asp_files)
            if self.run_solve == "reasoning" or self.run_solve ==  "all":
                self.get_message('classic')
                self.search_subsetmin(timer, 'classic')

            if self.run_solve == "filter" or self.run_solve ==  "all":
                self.get_message('filter')
                self.search_subsetmin(timer, 'filter')

            if self.run_solve == "guess_check" or self.run_solve ==  "all":
                self.get_message('guess_check')
                self.search_subsetmin(timer, 'guess_check')

            if self.run_solve == "guess_check_div" or self.run_solve ==  "all":
                self.get_message('guess_check_div')
                self.search_subsetmin(timer, 'guess_check_div')


        if self.minimize:
            self.get_message('minimize')
            if self.network.is_subseed:
                self.asp_files.append(self.asp.ASP_SRC_MAXIMIZE_PRODUCED_TARGET)
                logger.print_log('POSSIBLE SEED: Given\n  A subset of possible seed is search \n  maximising the number of produced target', 'info')
                self.clingo_constant.append('-c')
                self.clingo_constant.append('subseed=1') 
            self.asp_files.append(self.asp.ASP_SRC_MINIMIZE)

            if self.ground: 
                timer = self.reasoning_ground(self.asp_files)

            if self.run_solve == "reasoning" or self.run_solve ==  "all":
                self.get_message('classic')
                self.search_minimize(timer, 'classic')
                self.reinit_optimum()

            if self.run_solve == "filter" or self.run_solve ==  "all":
                self.get_message('filter')
                self.search_minimize(timer, 'filter')
                self.reinit_optimum()

            if self.run_solve == "guess_check" or self.run_solve ==  "all":
                self.get_message('guess_check')
                self.search_minimize(timer, 'guess_check')
                self.reinit_optimum()


            if self.run_solve == "guess_check_div" or self.run_solve ==  "all":
                self.get_message('guess_check_div')
                self.search_minimize(timer, 'guess_check_div')
                self.reinit_optimum()
            self.get_message('end')


    
    def reasoning_ground(self, asp_files:list):
        """Ground the ASP files to create all facts from rules

        Args:
            asp_files (list): List of ASP files, included th network asp file saved in temp directory
        """
        timer = dict()
        logger.print_log('self.groundING...', 'info')
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
    

    def search_minimize(self,  timer:dict, step:str="classic"):
        """Launch seed searching with minimze options

        Args:
            timer (dict): Timer dictionnary containing grouding time
            step (str, optional): step solving mode (classic, filter, guess_check, guess_check_div). Defaults to "classic".
        """
        logger.print_log("Finding optimum...", "info")
        self.solve("minimize-one-model", timer, self.asp_files, step, True)

        if not self.optimum_found:
            return
        
        if self.optimum == 0 or self.optimum == (0,0): # without or with possible seeds file
            opti_message = "Optimum is 0."

        ok_opti = self.optimum_found and (self.opt_size > 0)
        if self.intersection:    
            if ok_opti:
                self.get_message('intersection')
                self.solve("minimize-intersection", timer, self.asp_files, step)
            else:
                self.get_message('intersection')
                logger.print_log(f"\nNot computed: {opti_message}", "error") 
            
        if self.union:       
            if ok_opti:
                self.get_message('union')
                self.solve("minimize-union", timer, self.asp_files, step)
            else:
                self.get_message('union')
                logger.print_log(f"\nNot computed: {opti_message}", "error") 

        if self.enumeration: 
            if ok_opti:
                self.get_message('enumeration')  
                self.solve("minimize-enumeration", timer, self.asp_files, step)
            else:
                self.get_message('enumeration') 
                logger.print_log(f"\nNot computed: {opti_message}", "error")


    def search_subsetmin(self, timer:dict, step:str="classic"):
        """Launch seed searching with subset minimal options

        Args:
            timer (dict): Timer dictionnary containing grouding time
            step (str, optional): step solving mode (classic, filter, guess_check, guess_check_div). Defaults to "classic".
        """
        if self.enumeration:
            self.get_message('enumeration') 
            self.solve("submin-enumeration", timer, self.asp_files, step)
        else:
            self.number_solution = 1
            self.get_message('One solution')   
            self.solve("submin-enumeration", timer, self.asp_files, step)

        if self.intersection: 
            self.get_message('intersection')
            logger.print_log("SOLVING...\n", "info")
            self.solve("submin-intersection", timer, self.asp_files, step)
        

    def get_suffix(self, step:str):
        """Get the corresponding uffix of step solving mode (classic, filter, guess_check, guess_check_div)

        Args:
            step (str): step solving mode (classic, filter, guess_check, guess_check_div)

        Returns:
            str: Corresponding suffix to add into solution
        """
        suffix=""
        if step == "filter":
            suffix = " FILTER"
        elif step == "guess_check":
            suffix = " GUESS-CHECK"
        elif step ==  "guess_check_div":
            suffix = " GUESS-CHECK-DIVERSITY"
        return suffix


    def solve(self, search_mode:str, timer:dict, asp_files:list=None, step:str="classic", is_one_model:bool=False):
        """Solve the seed searching using the launch mode


        Args:
            search_mode (str):  Describe the launch mode.
            timer (dict): Timer dictionnary containing grouding time.
            asp_files (list, optional): List of asp files needed for clingo solving. Defaults to None.
            step (str, optional): step solving mode (classic, filter, guess_check, guess_check_div). Defaults to "classic".
            is_one_model (bool, optional): Define if it is the minimizing one model we are searching. Defaults to False.
        """

        logger.print_log("SOLVING...\n", "info")
        results = dict()
        one_model = None
        number_rejected = None
        solution_list = dict()
        full_option, mode_message, model_type, output_type = self.get_solutions_infos(search_mode)
        
        str_option,full_option = self.construct_string_option(full_option)

        suffix=self.get_suffix(step)

        match search_mode, step:
            # CLASSIC MODE (NO FILTER, NO GUESS-CHECK)   
            case "minimize-one-model", "classic":
                time_solve = time()
                if self.ground:
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
                            if self.network.possible_seeds:
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
                if self.ground:
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
                    
                    message = color.cyan_light  + f"Answer: {mode_message}{color.reset} ({size} seeds) \n{', '.join(map(str, seeds))}\n"
                    print(message)

                    solution_list, _ = self.complete_solutions(solution_list, 'model_'+ model_type, len(seeds), seeds)
                    self.network.add_result_seeds('REASONING', search_mode, model_type, len(seeds), seeds)
                else:
                    logger.print_log('Unsatisfiable problem', "error") 

            # FILTER OR GUESS-CHECK mode
            #TODO redo intersection and union mode
            case _, "filter"| "guess_check" | "guess_check_div":
                   time_solve, time_ground, solution_list, number_rejected = self.solve_hybrid(step, full_option, asp_files, search_mode, is_one_model)

        #TODO: Intersection and union not needed with filter and guess check but 
        # do with python the union and intersection of resulted soluion of filer or guess check

        if step == "filter" or "guess_check" in step:
            if time_ground != -1:
                timer["Grounding time"] = round(time_ground, 3)
            else:
                timer["Grounding time"] = "Time out"
        results = self.get_constructed_result(time_solve, timer, results, solution_list, number_rejected)
        self.output[output_type+suffix] = results



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
        transfers_complete=""
        transf_short=""
        trans_solution_list=None

        if self.ground:
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
                seeds_full=list(model.get('seed', ()))
                seeds=list(sorted(seeds))
                size = len(seeds)

                # In order to reuse this solve_enumeration function for global community mode,
                # meaning a subset minimal on both seeds and transfers, we need to add the retrieving
                # and completing messages here
                # This allow us to not rewrite the full function on reasoningcom.py
                if self.network.is_community:
                    transferred = model.get('transferred', ())
                    transferred=list(sorted(transferred))
                    transf_short, transfers_complete, trans_solution_list = self.get_transfers_info(transferred)
                message = color.cyan_light  + f"Answer: {idx}{color.reset} ({size} seeds{transf_short}) \n"
                self.print_answer(message, seeds, seeds_full, transfers_complete)
                solution_list, _ = self.complete_solutions(solution_list, 'model_'+str(idx), size, seeds, 
                           trans_solution_list)
                self.network.add_result_seeds('REASONING', search_mode, 'model_'+str(idx), size, seeds, transferred_list=trans_solution_list)
                idx += 1
        else:
            logger.print_log('Unsatisfiable problem', "error")
        return solution_list


       
    def construct_string_option(self, full_option:list, use_clingo_constant:bool=True):
        """Construct the string containing options for clingo solving and complete the full_option list

        Args:
            full_option (list): List of all options for clingo solving
            use_clingo_constant (bool, optional): Add value of clingo constant if needed. Defaults to True.

        Returns:
            str, list: construct_option, full_option
        """
        if not self.ground and use_clingo_constant:
            full_option = self.clingo_constant + full_option
        if self.optimum:
            # This option is for possible seed given by user
            # We need to optimise on both producible targets and seeds
            if self.opt_prod_tgt is not None:
                full_option[-1]=full_option[-1]+f",{self.opt_prod_tgt},{self.opt_size}"
            else:
                full_option[-1]=full_option[-1]+f",{self.opt_size}"

        construct_option = ' '.join(full_option)
        return construct_option, full_option
    

