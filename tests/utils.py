from os import path
from seed2lp.network import Network
from seed2lp.reasoning import Reasoning
from seed2lp.linear import Hybrid, FBA
from seed2lp.__main__ import get_reaction_options, get_input_datas
from seed2lp import logger
from seed2lp.file import is_valid_dir

################ DIRECTORIES AND FILES ###################
TEST_DIR = path.dirname(path.abspath(__file__))
RESULT_DIR=path.join(TEST_DIR,"results")
TMP_DIR=path.join(TEST_DIR,"tmp")
is_valid_dir(RESULT_DIR)
is_valid_dir(TMP_DIR)
logger.set_log_dir(path.join(TEST_DIR, RESULT_DIR,"logs"))
is_valid_dir(logger.LOG_DIR)
######################################################## 


################### FIXED VARIABLES ####################
TIME_LIMIT = 0
NB_SOLUTION = 0
CLINGO_CONF='jumpy'
CLINGO_STRAT="none"
INTERSECTION=False
UNION=False
VERBOSE=False
######################################################## 

####################### METHODS ########################

# solve values: 'reasoning', 'filter', 'guess_check', 'guess_check_div', 'hybrid'
# optim values: 'submin', 'min'
def search_seed(infile:str, run_mode:str, solve:str, optim:str, targets_as_seeds:bool=False):
    """
    Test FN without accumulation, remove import reaction, for:
        - Remove import reaction
        - No accumulation
        - Subset minimal / Minimize
        - Reasoning / Filter / Guess_Check / Guess_Check_div / Hybrid
        - Maximization
        - No file given, no objectif modification
    """
    reasoning_submin = list()
    filter_submin = list()
    gc_submin = list()
    gcd_submin = list()
    reasoning_min = list()
    filter_min = list()
    gc_min = list()
    gcd_min = list()
    hybrid_submin = list()
    hybrid_min = list()
    fba_submin = list()
    fba_min = list()

    topological_injection= False
    keep_import_reactions= False
    accumulation = False
    maximization = True

    

    match optim:
        case "submin":
            subset_minimal = True
            minimize = False
        case "min":
            subset_minimal = False
            minimize = True
        case _:
            subset_minimal = True
            minimize = True


    options=get_reaction_options(keep_import_reactions,topological_injection,
                                targets_as_seeds,maximization,run_mode,accumulation,solve)

    

    
    network= get_network(infile, run_mode, targets_as_seeds, topological_injection, 
                keep_import_reactions, accumulation, opt_short=options['short'])
    network.convert_to_facts()
    network.simplify()
    
    if run_mode != "fba":
        model = Reasoning(run_mode, solve, network, TIME_LIMIT, NB_SOLUTION, 
                        CLINGO_CONF,CLINGO_STRAT, INTERSECTION, UNION, minimize, subset_minimal, 
                        TMP_DIR, options['short'], VERBOSE)
        model.search_seed()
        
        model = Hybrid(run_mode, solve, network, TIME_LIMIT, NB_SOLUTION, 
                    CLINGO_CONF,CLINGO_STRAT, INTERSECTION, UNION, minimize, subset_minimal,
                    maximization, TMP_DIR, options['short'], VERBOSE)
        model.search_seed()
    else:
        model = FBA(run_mode, network, TIME_LIMIT, NB_SOLUTION, 
                    CLINGO_CONF,CLINGO_STRAT, INTERSECTION, UNION, minimize, subset_minimal,
                    maximization, TMP_DIR, options['short'], VERBOSE)
        model.search_seed()

    for result in network.result_seeds:
        match result.solver_type, result.search_mode,result.search_type:
            case "REASONING","Subset Minimal","Enumeration":
                reasoning_submin.append(result.seeds_list)
            case "REASONING FILTER","Subset Minimal","Enumeration":
                filter_submin.append(result.seeds_list)
            case "REASONING GUESS-CHECK","Subset Minimal","Enumeration":
                gc_submin.append(result.seeds_list)
            case "REASONING GUESS-CHECK DIVERSITY","Subset Minimal","Enumeration":
                gcd_submin.append(result.seeds_list)
            
            case "REASONING","Minimize","Enumeration":
                reasoning_min.append(result.seeds_list)
            case "REASONING FILTER","Minimize","Enumeration":
                filter_min.append(result.seeds_list)
            case "REASONING GUESS-CHECK","Minimize","Enumeration":
                gc_min.append(result.seeds_list)
            case "REASONING GUESS-CHECK DIVERSITY","Minimize","Enumeration":
                gcd_min.append(result.seeds_list)

            case "HYBRID","Subset Minimal","Enumeration":
                hybrid_submin.append(result.seeds_list)
            
            case "HYBRID","Minimize","Enumeration":
                hybrid_min.append(result.seeds_list)

            case "FBA","Subset Minimal","Enumeration":
                fba_submin.append(result.seeds_list)

            case "FBA","Minimize","Enumeration":
                fba_min.append(result.seeds_list)

    # solve value : 'reasoning', 'filter', 'guess_check', 'guess_check_div', 'hybrid', 'all' (-for FBA)
    match solve, optim:
        case 'reasoning','submin':
            return reasoning_submin
        case 'filter','submin':
            return filter_submin
        case 'guess_check','submin':
            return gc_submin
        case 'guess_check_div','submin':
            return gcd_submin
        case 'hybrid','submin':
            return hybrid_submin
        case 'all','submin':
            return fba_submin
        

        case 'reasoning','min':
            return reasoning_min
        case 'filter','min':
            return filter_min
        case 'guess_check','min':
            return gc_min
        case 'guess_check_div','min':
            return gcd_min
        case 'hybrid','min':
            return hybrid_min
        case 'all','min':
            return fba_min


# TODO: Possible seeds, forbidden seeds, seeds, target and obejctive modification
def get_network(infile:str, run_mode:str, targets_as_seeds:bool,
                 topological_injection:bool, keep_import_reactions:bool, accumulation:bool=False,
                 seeds_file:str=None, forbidden_seeds_file:str=None, possible_seeds_file:str=None, 
                 opt_short:str="test"):
    
    logger.get_logger(infile, opt_short, VERBOSE)
    input_dict = get_input_datas(seeds_file, forbidden_seeds_file, possible_seeds_file)
    network = Network(infile, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions,
                    input_dict, accumulation)
    
    if not targets_as_seeds:  
        network.forbidden_seeds += network.targets
    return network
    
######################################################## 
