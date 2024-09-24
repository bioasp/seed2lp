# Object Hybrid, herit from Solver, added properties:
#    - temp_dir (str): temporary directory for saving instance file and clingo outputs
#    - instance_file (str): Path of instance file for solving
#               1 -> Atom output
#               2 -> Json output

# Object FBA, herit from Hybrid, no property added

from seed2lp.network import Network
from seed2lp.solver import Solver
from . import clingo_lpx, color, logger


###################################################################
################### Class Hybrid : herit Solver ################### 
###################################################################
class Hybrid(Solver):
    def __init__(self, run_mode:str, run_solve:str, network:Network, 
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None, 
                 intersection:bool=False, union:bool=False,
                 minimize:bool=False, subset_minimal:bool=False, 
                 maximize_flux:bool=False,
                 temp_dir:str=None, short_option:str=None, 
                 verbose:bool=False):
        """Initialize Object Hybrid, herit from Solver

        Args:
            run_mode (str): Running command used (full or target or fba)
            run_solve (str): Solving command used (Hybrid)
            network (Network): Network constructed
            time_limit_minute (float, optional): Time limit given by user in minutes . Defaults to None.
            number_solution (int, optional): Limit number of solutions to find. Defaults to None.
            clingo_configuration (str, optional): Configuration for clingo resolution . Defaults to None.
            clingo_strategy (str, optional): Strategy for clingo resolution. Defaults to None.
            enumeration (bool, optional): Enumerate the solutions limited by the number of solutions. Defaults to True.
            intersection (bool, optional):  Find the intersection of all solutions without limitation (give one solution). Defaults to False.
            union (bool, optional): Find the union of all solutions without limitation (give one solution). Defaults to False.
            minimize (bool, optional): Search the minimal carinality of solutions. Defaults to False.
            subset_minimal (bool, optional):  Search the subset minimal solutions. Defaults to False.
            maximize_flux (bool, optional): Use maximization of flux for calculation. Defaults to False.
            temp_dir (str, optional): Temporary directory for saving instance file and clingo outputs. Defaults to None.
            short_option (str, optional): Short way to write option on filename. Defaults to None.
            verbose (bool, optional): Set debug mode. Defaults to False.
        """
        super().__init__(run_mode, network, time_limit_minute, number_solution, clingo_configuration, 
                         clingo_strategy, intersection, union, minimize, subset_minimal, temp_dir, short_option, run_solve, verbose)

        self.is_linear = True
        self.maximize_flux = maximize_flux
        self.temp_dir = temp_dir
        self.short_option = short_option
        self.get_init_message()
        self._init_clingo_constant()
        self._set_instance_file()
        

    ######################## METHODS ########################
    def get_init_message(self):
        """Get init message to put on terminal
        """
        title_mess = "\n############################################\n" \
            "############################################\n" \
            f"                    {color.bold}HYBRID{color.cyan_light}\n"\
            "############################################\n" \
            "############################################\n"
        logger.print_log(title_mess, "info", color.cyan_light) 

    
    def _init_clingo_constant(self):
        """Init the list of ASP constant command for resolution 
        """
        self.init_const()

        if self.maximize_flux:
            logger.print_log('Flux: MAXIMIZATION', "info")
        else:
            logger.print_log('Flux: NO MAXIMIZATION', "info")
        logger.print_log(f"Time limit: {self.time_limit_minute} minutes", 'info')
        logger.print_log(f"Solution number limit: {self.number_solution}", 'info')


    def search_seed(self): 
        """Launch seed searching 
        """
        if not self.network.objectives:
            self.get_message('optimum error')
            self.get_message('end')
            return
        files = [self.network.instance_file, self.asp.ASP_SRC_SEED_SOLVING, self.asp.ASP_SRC_FLUX]
        if self.maximize_flux:
            files.append(self.asp.ASP_SRC_MAXIMIZE_FLUX)
        if self.subset_minimal:
            self.get_message('subsetmin')
            #logger.print_log("GROUNDING...", "info")
            #self.grounded, timer, err_output, error_code, memory = self.ground(files, self.clingo_constant, self.is_linear, self.verbose)
            self.search_subsetmin(files)
        if self.minimize:
            self.get_message('minimize')
            if self.network.is_subseed:
                files.append(self.asp.ASP_SRC_MAXIMIZE_PRODUCED_TARGET)
                logger.print_log('POSSIBLE SEED: Given', "info")
                logger.print_log('  A subset of possible seed is search \n  maximising the number of produced target', "info")
                self.clingo_constant.append('-c')
                self.clingo_constant.append('subseed=1')  
            files.append(self.asp.ASP_SRC_MINIMIZE)
            #logger.print_log("GROUNDING...", "info")
            #self.grounded, timer, err_output, error_code, memory = self.ground(files, self.clingo_constant, self.is_linear, self.verbose)
            self.search_minimize(files)
            self.get_message('end')
        

    def search_minimize(self, asp_files):
        """Launch seed searching with minimze options
        """
        logger.print_log("Finding optimum...", "info")
        self.solve(asp_files, "minimize-one-model")

        if self.one_model_unsat:
            return
        
        ok_opti = self.optimum_found and (self.opt_size > 0)
        #ok_opti = (self.optimum is not None) and (self.optimum > 0)
        if self.optimum is None:
            opti_message = "Optimum not found."
        elif self.optimum == 0:
            opti_message = "Optimum is 0."

        if self.enumeration: 
            if ok_opti:
                self.get_message('enumeration') 
                self.solve(asp_files, "minimize-enumeration")
            else:
                self.get_message('enumeration')  
                logger.print_log(f"\nNot computed: {opti_message}", "info") 

        if self.intersection:   
            if ok_opti:
                self.get_message('intersection')
                self.solve(asp_files, "minimize-intersection")
            else:
                self.get_message('intersection')
                logger.print_log(f"\nNot computed: {opti_message}", "info")  


    def search_subsetmin(self, asp_files):
        """Launch seed searching with subset minimal options
        """
        if self.enumeration:
            self.get_message('enumeration') 
            self.solve(asp_files, "submin-enumeration")
        else:
            self.number_solution = 1
            logger.print_log("\n--------------- One solution ---------------", "info")  
            self.solve(asp_files, "submin-enumeration")
            

        if self.intersection: 
            self.get_message('intersection')
            self.solve(asp_files, "submin-intersection")


    def add_result_seeds(self,  search_mode:str, model_name:str, len:int, seeds:list, flux_dict:dict):
        """Add a formated resulted set of seeds into the network object

        Args:
            search_mode (str): search mode type
            model_name (str): model name
            len (int): length of a set of seed
            seeds (list): list of seeds
            flux_dict(dict): Dictionnary of all reaction with their LP flux
        """
        self.network.add_result_seeds('HYBRID', search_mode, model_name, len, seeds, flux_dict)


    def get_objectives_flux(self, flux_list):
        """From a list of all reaction and associated LP flux, find objective reactions
        and create a dictionnary to stock the LP flux

        Args:
            flux_list (list): List of all reaction name and associated LP flux

        Returns:
            Dict: A dictionnary of Objective reaction with it associated flux
        """
        obj_flux_dict = dict()
        for line in flux_list:
            reaction = line[0]
            if reaction in self.network.objectives:
                obj_flux_dict[reaction] = line[1]
        return obj_flux_dict
        


    def solve(self, asp_files:list=[], search_mode:str=""):
        """Solve the seed seraching using the launch mode

        Args:
            asp_files (list, optional): List of ASP files used for sovling. Defaults to [].
            search_mode (str, optional): Describe the launch mode. . Defaults to "".
        """
        logger.print_log("SOLVING...\n", "info")
        results = dict()
        solution_list = dict()
        timer = dict()

        full_option, _, model_type, output_type = self.get_solutions_infos(search_mode)
        full_option = self.clingo_constant + full_option
        
        if self.optimum:
            if self.opt_prod_tgt is not None:
                full_option[-1]=full_option[-1]+f",{self.opt_prod_tgt},{self.opt_size}"
            else:
                full_option[-1]=full_option[-1]+f",{self.opt_size}"
        

        match search_mode:
            case "minimize-one-model":
                cmd = clingo_lpx.command(files=asp_files, options=full_option,
                                         time_limit=self.time_limit)
                cmd_str = ' '.join(cmd)
                proc_output, err, error_code, \
                    memory, is_killed = clingo_lpx.solve(cmd, self.time_limit)
                self.get_message("command")
                logger.print_log(f'{cmd_str}', 'debug')
                
                self.get_error(error_code, err)
                output_full_list, unsatisfiable, self.optimum_found, full_timers, opt = clingo_lpx.result_convert(proc_output,
                                                                                           self.network.objectives, 
                                                                                           "", is_killed, False)
                if unsatisfiable:
                    logger.print_log('Unsatisfiable problem', "error") 

                elif self.optimum_found: 
                    logger.print_log("Optimum Found", "info")
                    self.one_model_unsat = False
                    one_model_list=output_full_list[list(output_full_list.keys())[-1]]
                    self.optimum=opt
                    self.get_separate_optimum()
                    #TODO Corrects the producible targets count
                    #if self.network.is_subseed:
                    #    logger.print_log((f"Number of producible targets: {- self.opt_prod_tgt}"), 'info')
                    #TODO END
                    logger.print_log(f"Minimal size of seed set is {self.opt_size}\n", 'info')
                    if self.optimum is not None and self.network.keep_import_reactions:
                        logger.print_log("Try with the option remove import reactions.", "info")
                    solution_list[model_type] = one_model_list
                    #Get obejctives fluxes and add results seeds to network object
                    obj_flux_dict = self.get_objectives_flux(one_model_list[5])
                    self.add_result_seeds(search_mode, model_type, one_model_list[1], one_model_list[3], obj_flux_dict)
                # Satisfiable probleme but optimum not found in given time
                else:
                    logger.print_log('Optimum not found', "error") 

            case "minimize-enumeration":
                cmd = clingo_lpx.command(files=asp_files, options=full_option, nb_model= self.number_solution,
                                         time_limit=self.time_limit)
                cmd_str = ' '.join(cmd)
                proc_output, err, error_code, \
                    memory, is_killed = clingo_lpx.solve(cmd, self.time_limit)
                self.get_message("command")
                logger.print_log(f'{cmd_str}', 'debug')
                self.get_error(error_code, err)
                solution_list, unsatisfiable, _, full_timers, _ = clingo_lpx.result_convert(proc_output,
                                                                            self.network.objectives, "enumeration", is_killed)
                if unsatisfiable:
                    logger.print_log('Unsatisfiable problem', "error") 
                else:
                    for  model_name, solution in solution_list.items():
                        #Get obejctives fluxes and add results seeds to network object
                        obj_flux_dict = self.get_objectives_flux(solution[5])
                        self.add_result_seeds(search_mode, model_name, solution[1], solution[3], obj_flux_dict)

            case "submin-enumeration":
                cmd = clingo_lpx.command(files=asp_files, options=full_option, nb_model= self.number_solution,
                                         time_limit=self.time_limit)
                cmd_str = ' '.join(cmd)
                proc_output, err, error_code, \
                    memory, is_killed = clingo_lpx.solve(cmd, self.time_limit)
                self.get_message("command")
                logger.print_log(f'{cmd_str}', 'debug')
                self.get_error(error_code, err)
                solution_list, unsatisfiable, _, full_timers,_ = clingo_lpx.result_convert(proc_output,
                                                                            self.network.objectives, "enumeration", is_killed)
                if unsatisfiable:
                    logger.print_log('Unsatisfiable problem', "error") 
                else:
                    for  model_name, solution in solution_list.items():
                        #Get obejctives fluxes and add results seeds to network object
                        obj_flux_dict = self.get_objectives_flux(solution[5])
                        self.add_result_seeds(search_mode, model_name, solution[1], solution[3], obj_flux_dict)

            case "minimize-intersection":
                cmd = clingo_lpx.command(files=asp_files, options=full_option,
                                         time_limit=self.time_limit)
                cmd_str = ' '.join(cmd)
                proc_output, err, error_code, \
                    memory, is_killed = clingo_lpx.solve(cmd, self.time_limit)
                self.get_message("command")
                logger.print_log(f'{cmd_str}', 'debug')
                self.get_error(error_code, err)
                output_full_list, unsatisfiable, _, full_timers = clingo_lpx.result_convert(proc_output,
                                                                                self.network.objectives, 'cautious', is_killed)
                if unsatisfiable:
                    logger.print_log('Unsatisfiable problem', "error") 
                elif output_full_list:
                    model = output_full_list[list(output_full_list.keys())[-1]]
                    solution_list[model_type ] = model
                    #Get obejctives fluxes and add results seeds to network object
                    obj_flux_dict = self.get_objectives_flux(model[5])
                    self.add_result_seeds(search_mode, model_type, model[1], model[3], obj_flux_dict)


            case "submin-intersection": 
                cmd = clingo_lpx.command(files=asp_files, options=full_option,
                                         time_limit=self.time_limit)
                cmd_str = ' '.join(cmd)
                proc_output, err, error_code, \
                    memory, is_killed = clingo_lpx.solve(files=asp_files, options=full_option,
                                         time_limit=self.time_limit)
                self.get_message("command")
                logger.print_log(f'{cmd_str}', 'debug')
                self.get_error(error_code, err)
                output_full_list, unsatisfiable, _, full_timers = clingo_lpx.result_convert(proc_output,
                                                                                self.network.objectives, 'cautious', is_killed)
                if unsatisfiable:
                    logger.print_log('Unsatisfiable problem', "error") 
                elif output_full_list:
                    model = output_full_list[list(output_full_list.keys())[-1]]
                    solution_list[model_type] = model
                    #Get obejctives fluxes and add results seeds to network object
                    obj_flux_dict = self.get_objectives_flux(model[5])
                    self.add_result_seeds(search_mode, model_type, model[1], model[3], obj_flux_dict)
        if 'Total' in full_timers:
            timer["Grounding time"] = round(full_timers['Total'] - full_timers['Solve'], 3)
            timer["Solving time"] = round(full_timers['Solve'], 3)   
        else:
            timer["Grounding time"] = "Time out"
            timer["Solving time"] = "Time out"
        results ["Timer"] = timer       
        results ["Memory (GB)"] = memory 
        results['solutions']= solution_list
        self.output[output_type] = results


    def get_error(self,error_code:int, err:bytes):
        """Get and print error

        Args:
            error_code (int): Code error from Python process
            err (bytes): Error text from python process

        Raises:
            ValueError: Raise an error and stop the program when value of code < 0
        """
        if error_code and error_code<0:
            print(f'error_code = {error_code}')
            raise ValueError(err.decode())
        elif err:
            logger.print_log(err.decode(), 'debug')

     ######################################################## 


###################################################################
##################### Class FBA : herit Hybrid #################### 
###################################################################
class FBA(Hybrid):
    def __init__(self,  run_mode:str, network:Network, 
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None, 
                 intersection:bool=False, union:bool=False, 
                 minimize:bool=False, subset_minimal:bool=False, 
                 maximize_flux:bool=False, 
                 temp_dir:str=None, short_option:str=None,
                 verbose:bool=False):
        """Initialize Object Hybrid, herit from Solver

        Args:
            run_mode (str): Running command used (full or target or fba)
            network (Network): Network constructed
            time_limit_minute (float, optional): Time limit given by user in minutes . Defaults to None.
            number_solution (int, optional): Limit number of solutions to find. Defaults to None.
            clingo_configuration (str, optional): Configuration for clingo resolution . Defaults to None.
            clingo_strategy (str, optional): Strategy for clingo resolution. Defaults to None.
            enumeration (bool, optional): Enumerate the solutions limited by the number of solutions. Defaults to True.
            intersection (bool, optional):  Find the intersection of all solutions without limitation (give one solution). Defaults to False.
            union (bool, optional): Find the union of all solutions without limitation (give one solution). Defaults to False.
            minimize (bool, optional): Search the minimal carinality of solutions. Defaults to False.
            subset_minimal (bool, optional):  Search the subset minimal solutions. Defaults to False.
            maximize_flux (bool, optional): Use maximization of flux for calculation. Defaults to False.
            temp_dir (str, optional): Temporary directory for saving instance file and clingo outputs. Defaults to None.
            short_option (str, optional): Short way to write option on filename. Defaults to None.
            verbose (bool, optional): Set debug mode. Defaults to False.
        """
        super().__init__(run_mode, None, network, 
                         time_limit_minute, number_solution, 
                         clingo_configuration, clingo_strategy, 
                         intersection, union, minimize,
                         subset_minimal, maximize_flux, 
                         temp_dir, short_option, 
                         verbose)

    ######################## METHODS ########################

    def get_init_message(self):
        """Get init message to put on terminal
        """
        title_mess = "\n############################################\n" \
            "############################################\n" \
            f"                     {color.bold}FBA{color.cyan_light}\n"\
            "############################################\n" \
            "############################################\n"
        logger.print_log(title_mess, "info", color.cyan_light) 

    def add_result_seeds(self, search_mode:str, model_name:str, len:int, seeds:list, flux_list:list):
        """Add a formated resulted set of seeds into the network object

        Args:
            search_mode (str): search mode type
            model_name (str): model name
            len (int): length of a set of seed
            seeds (list): list of seeds
        """
        self.network.add_result_seeds('FBA', search_mode, model_name, len, seeds, flux_list)
    ########################################################
        
    

