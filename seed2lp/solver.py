# Object Solver constitued of 
#    - run_mode (str): Running command used (full or target)
#    - network (Network): Object Network
#    - time_limit_minute (float): Time limit given by user in minutes 
#    - time_limit (int): Time limit converted in seconds for resolutions
#    - number_solution (int): Limit number of solutions to find
#    - clingo_configuration (str): Configuration for clingo resolution (jumpy or not, or other)
#    - clingo_strategy (str): Strategy for clingo resolution (usc,oll or not, other)
#    - enumeration (bool): Enumerate the solutions limited by the number of solutions
#    - intersection (bool): Find the intersection of all solutions without limitation (give one solution)
#    - union (bool): Find the union of all solutions without limitation (give one solution)
#    - minimize (bool): Search the minimal carinality of solutions
#    - subset_minimal (bool): Search the subset minimal solutions
#    - clingo_constant (str): Set the value of constant in lp file for search 
#    - one_model_unsat (bool): Set if the minimze solution is unsatisfiable
#    - optimum (int): Value of minimal cardinality if not unsatisfiable
#    - output (dict): List of all solutions
#    - timer_list (dict): List of all timers to find solution
#    - verbose (bool): Set debug mode

from os import path
from .network import  Network
from .file import write_instance_file
from dataclasses import dataclass
from . import logger
from . import color



@dataclass
class ASP_CLINGO:
    SRC_DIR = path.dirname(path.abspath(__file__))
    ASP_SRC_SEED_SOLVING = path.join(SRC_DIR, 'asp/seed-solving.lp')
    ASP_SRC_MINIMIZE = path.join(SRC_DIR, 'asp/minimize.lp')
    ASP_SRC_FLUX = path.join(SRC_DIR, 'asp/flux.lp')
    ASP_SRC_MAXIMIZE_FLUX = path.join(SRC_DIR, 'asp/maximize_flux.lp')
    ASP_SRC_MAXIMIZE_PRODUCED_TARGET = path.join(SRC_DIR, 'asp/maximize_produced_target.lp')
    CLINGO_CONFIGURATION = {
            'minimize-enumeration': ['--project=show', '--opt-mode=enum'],
            'minimize-union':  ['--enum-mode=brave', '--opt-mode=enum'],
            'minimize-intersection': ['--enum-mode=cautious', '--opt-mode=enum'],
            'minimize-one-model': None,
            'submin-enumeration': ['--heuristic=Domain', '--enum-mode=domRec', '--dom-mod=5,16'],
            'submin-intersection': ['--heuristic=Domain', '--enum-mode=cautious', '--dom-mod=5,16'],
            }
    ASW_FLAG, OPT_FLAG, OPT_FOUND = 'Answer: ', 'Optimization: ', 'OPTIMUM FOUND'

###################################################################
########################## Class  Solver ########################## 
###################################################################
class Solver:
    def __init__(self, run_mode:str, network:Network, 
                 time_limit_minute:float=None, number_solution:int=None, 
                 clingo_configuration:str=None, clingo_strategy:str=None,
                 intersection:bool=False, union:bool=False, 
                 minimize:bool=False, subset_minimal:bool=False,
                 temp_dir:str=None, short_option:str=None, run_solve:str=None,
                 verbose:bool=False):
        """"Initialize Object Solver

        Args:
            run_mode (str): Running command used (full or target)
            network (Network): Network constructed
            time_limit_minute (float, optional): Time limit given by user in minutes . Defaults to None.
            number_solution (int, optional): Limit number of solutions to find. Defaults to 100. if -1, no enumeration
            clingo_configuration (str, optional): Configuration for clingo resolution . Defaults to None.
            clingo_strategy (str, optional): Strategy for clingo resolution. Defaults to None.
            intersection (bool, optional):  Find the intersection of all solutions without limitation (give one solution). Defaults to False.
            union (bool, optional): Find the union of all solutions without limitation (give one solution). Defaults to False.
            minimize (bool, optional): Search the minimal carinality of solutions. Defaults to False.
            subset_minimal (bool, optional):  Search the subset minimal solutions. Defaults to False.
            temp_dir (str, optional): Temporary directory for saving instance file and clingo outputs. Defaults to None.
            short_option (str, optional): Short way to write option on filename. Defaults to None.
            run_solve (str, optional): Solving run used (reasoning, filter, guess-check, guess-check-div)
            verbose (bool, optional): Set debug mode. Defaults to False.
        """

        self.is_linear:bool
        self.asp = ASP_CLINGO()
        self.run_mode = run_mode
        self.network = network
        self.time_limit_minute = time_limit_minute
        self.set_time_limit()
        self.number_solution = number_solution
        self._set_clingo_configuration(clingo_configuration)
        self._set_clingo_strategy(clingo_strategy)
        self.enumeration = True
        if(number_solution == -1):
            self.enumeration = False
        self.intersection = intersection
        self.union = union
        self.minimize = minimize
        self.subset_minimal = subset_minimal
        self.clingo_constant = list()
        self.one_model_unsat = True
        self.optimum = tuple()
        self.optimum_found = False
        self.opt_prod_tgt = None
        self.opt_size = None
        self.output = dict()
        self.timer_list =  dict()
        self.verbose = verbose
        self.messages = list()
        self.temp_dir = temp_dir
        self.short_option = short_option
        self.run_solve = run_solve
        if self.run_solve == "guess_check_div":
            self.diversity = True
        else: 
            self.diversity = False
        self.grounded = str()
        self.temp_result_file = str()
        

    
    ######################## SETTER ########################
    def set_time_limit(self):
        """Convert time limit minute into seconds for resolutions
        """
        if self.time_limit_minute != 0:
            self.time_limit=self.time_limit_minute*60
        else:
            self.time_limit=None

    
    def _set_clingo_configuration(self, clingo_configuration:str):
        """Prepare configuration command option for resolution

        Args:
            clingo_configuration (str): configuration mode
        """
        if clingo_configuration != "none":
            self.clingo_configuration = f"--configuration={clingo_configuration}"
        else:
            self.clingo_configuration = ""
    
    def _set_clingo_strategy(self, clingo_strategy:str):
        """Prepare strategy command option for resolution

        Args:
            clingo_strategy (str): strategy mode
        """
        if clingo_strategy != "none":
            self.clingo_strategy = f"--opt-strategy={clingo_strategy}"
        else:
            self.clingo_strategy = ""

    def _set_instance_file(self):
        """Prepare ASP instance filename for saving into temporary directory file
        """
        filename = f'instance_{self.network.name}_{self.short_option}'
        self.network.instance_file = path.join(self.temp_dir,f'{filename}.lp')
        write_instance_file(self.network.instance_file, self.network.facts)
        logger.log.info(f"Instance file written: {self.network.instance_file}")

    
    def _set_temp_result_file(self):
        self.temp_result_file = f'temp_{self.network.name}_{self.short_option}'

    ########################################################

    ######################## METHODS ########################


    def get_solutions_infos(self, search_mode:str=""):
        """Get infos of solving mode for messsages and outputs.

        Args:
            search_mode (str, optional): Describe the mode of resolution. Defaults to "".

        Returns:
            str, str, str: mode_message, model_type, output_type
        """
        mode_message = ""
        model_type = ""
        output_type = ""
        match search_mode:
            case "minimize-one-model":
                mode_message="Minimize optimum"
                model_type="model_one_solution"
                output_type = 'MINIMIZE OPTIMUM'
            case "minimize-intersection":
                mode_message="Minimize intersection"
                model_type="model_intersection"
                output_type = 'MINIMIZE INTERSECTION'
            case "minimize-union":
                mode_message="Minimize union"
                model_type="model_union"
                output_type = 'MINIMIZE UNION'
            case "minimize-enumeration":
                output_type = 'MINIMIZE ENUMERATION'
            case "submin-enumeration":
                output_type = 'SUBSET MINIMAL ENUMERATION'
            case "submin-intersection":
                mode_message="Subset Minimal intersection"
                model_type="model_intersection"
                output_type = 'SUBSET MINIMAL INTERSECTION'
                
            
        full_option=[self.clingo_configuration, self.clingo_strategy]
        greedy_clingo_option=self.asp.CLINGO_CONFIGURATION[search_mode]
        if greedy_clingo_option:
            full_option = [*full_option, *greedy_clingo_option]
        full_option = list(filter(None, full_option))
        return full_option, mode_message, model_type, output_type


    def init_const(self):
        """ Inititate ASP constants
        """
        self.clingo_constant = ['-c']
        match self.run_mode:
            case 'target':
                logger.print_log("Mode : TARGET", "info")
                if not self.network.targets_as_seeds:  
                    logger.print_log('Option: TARGETS ARE FORBIDDEN SEEDS', "info")
                logger.print_log(f'Search seeds validating the {len(self.network.targets)} targets…','debug')
                self.clingo_constant.append('run_mode=target')
            case 'full':
                logger.print_log("Mode : FULL NETWORK", "info")
                logger.print_log("Search seeds validating all metabolites as targets…",'debug')
                self.clingo_constant.append('run_mode=full')
            case 'fba':
                logger.print_log("Mode : FBA", "info")
                if not self.network.targets_as_seeds:  
                    logger.print_log('Option: TARGETS ARE FORBIDDEN SEEDS', "info")
                    logger.print_log('Info: Targets are reactant of objective', "info")
                logger.print_log("Search seeds aleatory…",'debug')
                self.clingo_constant.append('run_mode=fba')

        if self.network.accumulation:
            logger.print_log('ACCUMULATION: Authorized', "info")
            self.clingo_constant.append('-c')
            self.clingo_constant.append('accu=1')
        else:
            logger.print_log('ACCUMULATION: Forbidden', "info")
            self.clingo_constant.append('-c')
            self.clingo_constant.append('accu=0')
    
    def get_separate_optimum(self):
        """This function separate the optimisations if possible: 
            Maximization of produced target (rank 2)
            Minimization of set of seeds (rank 1)
        When using multiple optimization with clingo, the solver gives back
        a list of optimality found in order of importance in the asp files .
        A higher rank means a higher importance. 
        """
        if len(self.optimum)==1:
            self.opt_prod_tgt = None
            self.opt_size = self.optimum[0]
        else:
            self.opt_prod_tgt = self.optimum[0]
            self.opt_size = self.optimum[1]    
    
    def get_message(self, mode:str=None):
        """Get messages to put on terminal

        Args:
            mode (str, optional): witch kind of messages to chose. Defaults to None.
        """
        match mode:
            case 'subsetmin':
                logger.print_log("\n____________________________________________","info",color.purple)  
                logger.print_log("____________________________________________\n", "info",color.purple)
                logger.print_log(f"Sub Mode: {color.bold}SUBSET MINIMAL{color.reset}".center(55), "info")
                logger.print_log("____________________________________________", "info",color.purple)
                logger.print_log("____________________________________________\n", "info",color.purple)
            case "minimize":
                logger.print_log("\n____________________________________________","info",color.purple)
                logger.print_log("____________________________________________\n", "info",color.purple)   
                logger.print_log(f"Sub Mode: {color.bold}MINIMIZE{color.reset}".center(55), "info")
                logger.print_log("____________________________________________", "info",color.purple) 
                logger.print_log("____________________________________________\n", "info",color.purple) 
            case "one solution":
                logger.print_log(f"\n~~~~~~~~~~~~~~~ {color.bold}One solution{color.reset} ~~~~~~~~~~~~~~~", "info") 
            case "intersection":
                logger.print_log(f"\n~~~~~~~~~~~~~~~ {color.bold}Intersection{color.reset} ~~~~~~~~~~~~~~~", "info") 
            case "enumeration":
                logger.print_log(f"\n~~~~~~~~~~~~~~~~ {color.bold}Enumeration{color.reset} ~~~~~~~~~~~~~~~", "info")
            case "union":
                logger.print_log(f"\n~~~~~~~~~~~~~~~~~~~ {color.bold}Union{color.reset} ~~~~~~~~~~~~~~~~~~", "info") 
            case "end":
                logger.print_log('############################################\n\n', "info", color.cyan_light)
            case "optimum error":
                logger.print_log("\n____________________________________________","info") 
                logger.print_log('ABORTED: No objective funcion found \
                                    \nPlease correct the SBML file to contain either \
                                    \n    - a function with "BIOMASS" (not case sensiive) in the name \
                                    \n    - a function in the objective list', "error")
            case "command":
                logger.print_log("                Command", "debug")
            case "classic":
                logger.print_log(f"\n················ {color.bold}Classic mode{color.reset} ···············", "info") 
            case "filter":
                logger.print_log(f"\n················ {color.bold}Filter mode{color.reset} ···············", "info")  
            case "guess_check":
                logger.print_log(f"\n·············· {color.bold}Guess-Check mode{color.reset} ············", "info")  
            case "guess_check_div":
                logger.print_log(f"\n····· {color.bold}Guess-Check with diversity mode{color.reset} ······", "info")  

   
