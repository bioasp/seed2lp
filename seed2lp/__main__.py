"""entry point for predator.

"""


import argparse, logging

from time import time
from sys import exit
from os import path, listdir
from shutil import copyfile
from .file import is_valid_dir

from . import utils, argument, file
from .sbml import read_SBML_species, check_fbc_support
from .network import Network, Netcom, NET_TITLE
from .reasoning import Reasoning
from .reasoningcom import ComReasoning
from .linear import Hybrid, FBA
from .description import Description 
from .file import load_json
from pathlib import Path
from .scope import Scope
#from . import logger
from .logger import get_logger#, set_log_dir

#Global variable needed
PROJECT_DIR = path.dirname(path.abspath(__file__))
CLEAN_TEMP=True
LOG_DIR:str


####################### FUNCTIONS ##########################
def get_reaction_options(keep_import_reactions:bool, topological_injection:bool, 
                         targets_as_seeds:bool, maximization:bool, mode:str, accumulation:bool,
                         solve:str="", is_partial_delsupset:bool=False, is_extended_transfers:bool=False):
    """Get full options informations into a dictionnary

    Args:
        keep_import_reactions (bool): Import reactions are not removed if True
        topological_injection (bool): Topological injection is used if True
        targets_as_seeds (bool): Target are forbidden seed if True
        maximization (bool): Execute an objective flux maximization if True (Hybrid or FBA)
        mode (str): Witch mode is used (indiv : target, full or fba / community: global, bisteps or delsupset)
        accumulation(bool): Allow accumulations in ASP
        solve(str): which solve mode is used (reasoning, filter, guess_check or guess_check_div)
        is_partial_delsupset(bool): Partial delete superset is used (no post python check of sets)

    Returns:
        dict: list of option used (short value is for filename differentiation)
    """
    options = dict()

    if keep_import_reactions:
        if topological_injection:
            reaction_option = "Topological Injection"
            short_option = "import_rxn_ti"
        else:
            reaction_option = "No Topological Injection"
            short_option = "import_rxn_nti"
    else:
        reaction_option = "Remove Import Reaction"
        short_option = "rm_rxn"

    target_option=""
    match mode:
        case "target":
            network_option = "Target"
            short_option += "_tgt"
            if targets_as_seeds:
                target_option = "Targets are allowed seeds"
            else:
                target_option = "Targets are forbidden seeds"
                short_option += "_taf"
        case "full":
            network_option = "Full network"
            short_option += "_fn"
        case "fba":
            network_option = "FBA"
            short_option += "_fba"
            if targets_as_seeds:
                target_option = "Targets are allowed seeds"
            else:
                target_option = "Targets are forbidden seeds"
                short_option += "_taf"
        case "global":
            network_option = "Community Global"
            short_option += "_com_global"
            if targets_as_seeds:
                target_option = "Targets are allowed seeds"
            else:
                target_option = "Targets are forbidden seeds"
                short_option += "_taf"
        case "bisteps":
            network_option = "Community Bisteps"
            short_option += "_com_bisteps"
            if targets_as_seeds:
                target_option = "Targets are allowed seeds"
            else:
                target_option = "Targets are forbidden seeds"
                short_option += "_taf"
            if is_extended_transfers:
                short_option += "_extend_transf"
        case "delsupset":
            network_option = "Community delete superset"
            short_option += "_com_delsupset"
            if targets_as_seeds:
                target_option = "Targets are allowed seeds"
            else:
                target_option = "Targets are forbidden seeds"
                short_option += "_taf"
            if is_partial_delsupset:
                short_option += "_com_partial_delsupset"
            if is_extended_transfers:
                short_option += "_extend_transf"
        case _:
            network_option = mode
            short_option += f"_{mode.lower()}"

    match solve:
        case 'reasoning':
            solve_option = "REASONING"
            short_option += "_reas"
        case 'hybrid': 
            solve_option = "HYBRID"
            short_option += "_hyb"
        case 'guess_check':
            solve_option = "REASONING GUESS-CHECK"
            short_option += "_gc"
        case 'guess_check_div':
            solve_option = "REASONING GUESS-CHECK DIVERSITY"
            short_option += "_gcd"
        case 'filter':
            solve_option = "REASONING FILTER"
            short_option += "_fil"
        case 'all':
            if mode != "fba":
                solve_option = "ALL"
                short_option += "_all"
            else:
                solve_option = ""
                short_option += ""
    
    if maximization:
        flux_option = "Maximization"
        short_option += "_max"
    else:
        flux_option = "With flux"

    if accumulation:
        accu_option = "Allowed"
        short_option += "_accu"
    else:
        accu_option = "Forbidden"
        short_option += "_no_accu"

    options["short"] = short_option
    options["reaction"] = reaction_option
    options["network"] = network_option
    options["target"] = target_option
    options["flux"] = flux_option
    options["accumulation"] = accu_option
    options["solve"] = solve_option

    return options


def chek_inputs(sbml_file:str, input_dict:dict):
    """ Checks the presence of elements in the sbml file

    Args:
        sbml_file (str): Network sbml file
        input_dict (dict): Input data ordered in dictionnary

    Raises:
        ValueError: A reaction does not exist in network file
        ValueError: A metabolite does not exist in network file
    """
    model_dict = read_SBML_species(sbml_file)
    for key, list_element in input_dict.items():
        if key == "Objective":
            for reaction in list_element:
                if f'{reaction[1]}' not in model_dict["Reactions"]:
                    raise ValueError(f"Reaction {reaction} does not exist in network file {sbml_file}\n")
        else:
            for metabolite in list_element:
                if metabolite not in model_dict["Metabolites"]:
                    raise ValueError(f"Metabolite {metabolite} does not exist in network file {sbml_file}\n")


def get_input_datas(logger:logging, seeds_file:str=None,
                    forbidden_seeds:str=None, possible_seeds:str=None,
                    forbidden_transfers_file:str=None):
    """Get data from files given by user

    Args:
        seeds_file (str, optional): Files containing mandatory seeds. Defaults to None.
        forbidden_seeds (str, optional): Files containing forbidden seeds . Defaults to None.
        possible_seeds (str, optional): Files containing possible seeds. Defaults to None.

    Returns:
        dict: Dictionnary of all input data given by the user
    """
    input_dict = dict()
    if seeds_file:
        if file.file_is_empty(seeds_file):
            logger.warning(f"\n{seeds_file} is empty.\nPlease check your file and launch again\n")
        else:
            input_dict["Seeds"] = utils.get_ids_from_file(seeds_file, 'seed_user')
    if forbidden_seeds:
        if file.file_is_empty(forbidden_seeds):
            logger.warning(f"\n{forbidden_seeds} is empty.\nPlease check your file and launch again\n")
        else:
            input_dict["Forbidden seeds"] = utils.get_ids_from_file(forbidden_seeds, 'forbidden')
    if possible_seeds:
        if file.file_is_empty(possible_seeds):
            logger.warning(f"\n{possible_seeds} is empty.\nPlease check your file and launch again\n")
            possible_seeds=None
        else:
            input_dict["Possible seeds"] = utils.get_ids_from_file(possible_seeds, 'sub_seed')
    if forbidden_transfers_file:
        if file.file_is_empty(forbidden_transfers_file):
            logger.warning(f"\n{forbidden_transfers_file} is empty.\nPlease check your file and launch again\n")
        #TODO: Finish forbidden transfers file
        #else:
        #    input_dict["Forbidden transfers"] = utils.get_list_transfers(forbidden_transfers_file)
    return input_dict


def get_targets(logger:logging,targets_file:str, input_dict:dict, is_community:bool) -> dict :
    """Get metabolites target and objective reaction from file
    Check if the given data exist into SBML file
    ONLY USED WITH TARGET MODE

    Args:
        targets_file (str): Path of target file
        input_dict (dict): Constructed dictionnary of inputs
        is_community (bool): Community mode

    Returns:
        dict: Dictionnary of inputs completed
    """

    if file.file_is_empty(targets_file):
        logger.warning(f"\n{targets_file} is empty.\nPlease check your file and launch again\n")
        exit(1)
    try:
        input_dict["Targets"], input_dict["Objective"] = utils.get_targets_from_file(targets_file, is_community)
    except ValueError as ve:
        logger.error(str(ve))
        logger.warning("Please check your file and launch again\n")
        exit(1)
    except NotImplementedError as nie:
        print(str(nie))
        exit(1)

    return input_dict

def get_objective(objective:str, input_dict:dict):
    """Get metabolites objective reaction from command line
    Check if the given data exist into SBML file
    ONLY USED WITH FULL NETWORK MODE

    Args:
        objective (str): Name of new objective reaction from command line
        input_dict (dict): Constructed dictionnary of inputs

    Returns:
        dict: Dictionnary of inputs completed
    """
    #Working with one objective for now
    objectives = list()
    objectives.append(objective)
    input_dict["Objective"] = objectives
    return input_dict
    
def get_temp_dir(args):
    """Get temporary directory from arguments or by default

    Args:
        args (dict): argument used

    Returns:
        str: path of temporary directory
    """
    if args['temp']:
        temp = Path(args['temp']).resolve()
    else:
        temp = path.join(PROJECT_DIR,'tmp')
    return file.is_valid_dir(temp)


def init_s2pl(log_dir:str, args:dict, run_mode:str, is_community:bool=False):
    """Check and validate input data, and get the options used

    Args:
        args (dict): argument used
        run_mode (str): command used

    Returns:
        options, input_dict, out_dir, temp : options dictionnary, input dictionnary, 
        value of out_dir and temp dir
    """
    if 'maximize_flux' in args:
        maximize = args['maximize_flux']
    else:
        maximize = False

    if 'partial_delete_superset' in args:
        part_del = args['partial_delete_superset']
    else:
        part_del = False

    if 'all_transfers' in args:
        all_transf = args['all_transfers']
    else:
        all_transf = False

    options = \
        get_reaction_options(args['keep_import_reactions'], args['topological_injection'],
                             args['targets_as_seeds'], maximize,
                             run_mode, args['accumulation'], args['solve'], part_del, all_transf)
    
    if 'infile' in args:
        infile=args['infile']
    elif 'comfile' in args:
        infile=args['comfile']


    #logger=get_logger(infile, options["short"], args['verbose'])
    #get_logger(infile, options["short"], LOG_DIR, args['verbose'])
    logger, log_path = get_logger(
        log_dir=log_dir,
        sbml_file=infile,
        short_option= options["short"],
        verbose=args['verbose']
    )
    
    temp = get_temp_dir(args)

    out_dir = args['output_dir'] 
    file.is_valid_dir(out_dir)

    ###############################################################
    ################### Only for community mode ###################
    ###############################################################
    if 'forbidden_transfers_file' in args:
        forbidden_transfers_file = args['forbidden_transfers_file']
    else:
        forbidden_transfers_file=None
    ###############################################################
    ###############################################################

    # Getting the networks from sbml file
    input_dict = get_input_datas(logger, args['seeds_file'], args['forbidden_seeds_file'], 
                                 args['possible_seeds_file'],forbidden_transfers_file)
    if 'targets_file' in args and args['targets_file']: # only in target mode
        input_dict = get_targets(logger, args['targets_file'], input_dict, is_community)
    if 'objective' in args and args['objective']: # only in full network mode
        input_dict = get_objective(args['objective'], input_dict)
    return options, input_dict, out_dir, temp, logger, log_path


def initiate_results(logger:logging, network:Network, options:dict, args:dict, run_mode:str):
    """Initiate the result dictionnary with users options and given data such as forbidden seed,
    possible seed and defined seeds.

    Args:
        network (Network): Network object define froms sbml file and given data from user
        options (dict): Dictionnary containing the used options
        args (dict): List or arguments
        run_mode (str): Run mode used

    Returns:
        dict: A dictionnay containing all data used for solving 
    """
    results=dict()
    res_option = dict()
    user_data = dict()
    net = dict()

    if network.targets:
        user_data['TARGETS'] = network.targets
    if network.seeds:
        user_data['SEEDS'] = network.seeds
    if network.forbidden_seeds:
        user_data['FORBIDDEN SEEDS'] = network.forbidden_seeds
    if network.possible_seeds:
        if args['mode'] == 'minimize' or args['mode'] == 'all':
            user_data['POSSIBLE SEEDS'] = network.possible_seeds
        else:
            logger.error("Possible seed can be used only with minimize mode")
            exit(1)
    
    res_option['REACTION'] = options['reaction']
    if run_mode == "target" or run_mode == 'fba':
        res_option['TARGET'] = options['target']
    res_option['FLUX'] = options['flux']

    ###############################################################
    ################### Only for community mode ###################
    ###############################################################
    if run_mode == "community":
        if args['equality_flux']:
            res_option['FLUX EQUALITY'] = True
        else:
            res_option['FLUX EQUALITY'] =  False
    ###############################################################
    ###############################################################

    res_option['ACCUMULATION'] = options['accumulation']
    results["OPTIONS"]=res_option
    net["NAME"] = network.name
    if run_mode == "community":
        net["SPECIES"]=network.species
    net["OBJECTIVE"] = network.objectives
    net["SEARCH_MODE"] = options['network']
    net["SOLVE"] = options["solve"]
    results["NETWORK"] = net
    
    results["USER DATA"] = user_data
    
    if not args['targets_as_seeds']:
        network.forbidden_seeds += [t for t in network.targets if t not in network.meta_authorized_seed_list]

    return results
    
############################################################


############################################################
####################### COMMANDS ###########################
############################################################


#----------------------- SEED2LP ---------------------------
def run_seed2lp(args:dict, run_mode, log_dir:str):
    """Launch seed searching for one network after normalising it.

    Args:
        args (argparse): List or arguments
    """
    minimize=False
    subset_minimal=False
    solutions = dict()

    options, input_dict, out_dir, temp, logger, log_path = init_s2pl(log_dir, args, run_mode)
    # Verify if input data exist into sbml file
    try:
        chek_inputs(args['infile'], input_dict)
    except ValueError as e :
        logger.error(str(e))
        exit(1)

    time_data_extraction = time()
    network = Network(args['infile'], run_mode, args['targets_as_seeds'], 
                    args['topological_injection'], args['keep_import_reactions'],
                    input_dict, args['accumulation'], verbose=args['verbose'])

    
    time_data_extraction = time() - time_data_extraction


    results = initiate_results(logger, network,options,args,run_mode)
    network.convert_to_facts()

    if args['instance']:
        with open(args['instance'], "w") as f:
            f.write(network.facts)
        exit(1)
        
    network.simplify()

    if args['mode'] == 'minimize' or args['mode'] == 'all':
        minimize = True
    if args['mode'] == 'subsetmin' or args['mode'] == 'all':
        subset_minimal = True

    # Global seed searching time    
    time_seed_search = time()

    match run_mode:
        case "target" |  "full":
            run_solve = args['solve'] 
            if run_solve != "hybrid" or run_solve == 'all':
                # In target mode we need objective reaction to detect targets from file if not given by user
                # we force this whatever it is given or not
                if network.is_objective_error and (run_solve != "reasoning" or run_mode == "target"):
                    end_message = " aborted! No Objective found.\n"
                    match run_solve,run_mode:
                        case _,"target":
                            logger.error(f"Mode Target {end_message}")
                        case 'filter','full':
                            logger.error(f"Solve Filter {end_message}")
                        case 'guess_check','full':
                            logger.error(f"Solve Guess Check {end_message}")
                        case 'guess_check_div','full':
                            logger.error(f"Solve Guess Check Diversity {end_message}")
                        # In reasoning classic, in Full Network, no need to have an objective reaction (event it is deleted)
                        case 'all','full': # | 'reasoning','target':
                            model = Reasoning(run_mode, "reasoning", network, log_path, args['time_limit'], args['number_solution'], 
                                            args['clingo_configuration'], args['clingo_strategy'], 
                                            args['intersection'], args['union'], minimize, subset_minimal, 
                                            temp, options['short'],
                                            args['verbose'])
                            model.search_seed()
                            solutions['REASONING'] = model.output
                            results["RESULTS"] = solutions
                            # Intermediar saving in case of hybrid mode fails 
                            file.save(f'{network.name}_{options["short"]}_results',out_dir, results, 'json')
                            logger.error(f"Solve Filter / Guess Check / Guess Check Diversity {end_message}")
                            solutions['REASONING-OTHER'] = "No objective found"
                elif run_mode == "target" and not network.targets:
                    logger.error(f"Mode REASONING aborted! No target found")
                    solutions['REASONING'] = "No target found"
                else:
                    model = Reasoning(run_mode, run_solve, network, log_path, args['time_limit'], args['number_solution'], 
                                    args['clingo_configuration'], args['clingo_strategy'], 
                                    args['intersection'], args['union'], minimize, subset_minimal, 
                                    temp, options['short'],
                                    args['verbose'])
                    model.search_seed()
                    solutions['REASONING'] = model.output
                    results["RESULTS"] = solutions
                    # Intermediar saving in case of hybrid mode fails 
                    file.save(f'{network.name}_{options["short"]}_results',out_dir, results, 'json')

            if run_solve == "hybrid"  or run_solve == 'all':
                if not network.objectives or network.is_objective_error:
                    logger.error(f"Mode HYBRID aborted! No objective found")
                    solutions['HYBRID'] = "No objective found"
                else:
                    model = Hybrid(run_mode, run_solve, network, log_path, args['time_limit'], args['number_solution'], 
                                args['clingo_configuration'], args['clingo_strategy'],  
                                args['intersection'], args['union'], minimize, subset_minimal,
                                args['maximize_flux'], temp, 
                                options['short'], args['verbose'])
                    model.search_seed()
                    solutions['HYBRID'] = model.output
                    results["RESULTS"] = solutions
        case "fba":
            if not network.objectives or network.is_objective_error:
                logger.error(f"Mode FBA aborted! No objective found")
                solutions['FBA'] = "No objective found" 
            else:
                model = FBA(run_mode, network, log_path, args['time_limit'], args['number_solution'], 
                            args['clingo_configuration'], args['clingo_strategy'],
                            args['intersection'], args['union'], minimize, subset_minimal,
                            args['maximize_flux'], temp, 
                            options['short'], args['verbose'])
                model.search_seed()
                solutions['FBA'] = model.output
    results["RESULTS"] = solutions
    time_seed_search = time() - time_seed_search

    # Show the timers
    timers = {'DATA EXTRACTION': time_data_extraction} |\
        {'TOTAL SEED SEARCH': time_seed_search,
        'TOTAL': time_data_extraction + time_seed_search
    }

    namewidth = max(map(len, timers))
    time_mess=""
    for name, value in timers.items():
        value = value if isinstance(value, str) else f'{round(value, 3)}s'
        time_mess += f'\nTIME {name.center(namewidth)}: {value}'
    
    print(time_mess)
    logger.info(time_mess)
    print("\n")    

    # Save the result into json file
    file.save(f'{network.name}_{options["short"]}_results',out_dir, results, 'json')

    # Save all fluxes into tsv file
    if args['check_flux']:
        network.check_fluxes(args['maximize_flux'])
        file.save(f'{network.name}_{options["short"]}_fluxes', out_dir, network.fluxes, 'tsv')
    
    if CLEAN_TEMP:
        file.delete(network.instance_file)
        
    return results, timers


#------------------ COMMUNITY SEED SEARCHING -------------------
def community(args:argparse, run_mode, log_dir:str):
    """Launch seed searching for a community after merging Networks and normalising it

    Args:
        args (argparse): List or arguments
    """
    solutions = dict()
    community_mode = args['community_mode']
    run_solve = args['solve'] 

    options, input_dict, out_dir, temp, logger, log_path = init_s2pl(log_dir, args, community_mode, is_community=True)


    time_data_extraction = time()

    network=Netcom(args["comfile"], args["sbmldir"], temp, run_mode, run_solve, community_mode, args['targets_as_seeds'], args['topological_injection'], 
           args['keep_import_reactions'], input_dict, args['accumulation'], to_print=True, 
           write_sbml=True, equality_flux=args["equality_flux"], verbose=args['verbose'])
    time_data_extraction = time() - time_data_extraction
    
    results = initiate_results(logger, network,options,args,run_mode)
    network.convert_to_facts()


    # Global seed searching time    
    time_seed_search = time()


    # The community mode works like target mode and need objective reaction to detect targets from file if not given by user
    # we force this whatever it is given or not
    if network.is_objective_error and (run_solve != "reasoning" or run_mode == "community"):
        end_message = " aborted! \nMissing objective at least for one network.\n"
        logger.error(f"Mode community {end_message}")

    else:
        model = ComReasoning(run_mode, run_solve, network, log_path, args['time_limit'], args['number_solution'], 
                        args['clingo_configuration'], args['clingo_strategy'], 
                        args['intersection'], args['union'],
                        temp, options['short'],
                        args['verbose'], 
                        community_mode, args['partial_delete_superset'], args['all_transfers'],
                        args['not_shown_transfers'], args['limit_transfers'])
        model.search_seed()
        solutions['REASONING'] = model.output
        results["RESULTS"] = solutions
        
    file.save(f'{network.name}_{options["short"]}_results',out_dir, results, 'json')

        
    results["RESULTS"] = solutions
    time_seed_search = time() - time_seed_search

    # Show the timers
    timers = {'DATA EXTRACTION': time_data_extraction} |\
        {'TOTAL SEED SEARCH': time_seed_search,
        'TOTAL': time_data_extraction + time_seed_search
    }

    namewidth = max(map(len, timers))
    time_mess=""
    for name, value in timers.items():
        value = value if isinstance(value, str) else f'{round(value, 3)}s'
        time_mess += f'\nTIME {name.center(namewidth)}: {value}'
    
    print(time_mess)
    logger.info(time_mess)
    print("\n")

    # Save all fluxes into tsv file
    if args['check_flux']:
        # There is no maximisation when Hybrid lpx is not used (and community mode do not solve in hybrid lpx)
        network.check_fluxes(False)
        file.save(f'{network.name}_{options["short"]}_fluxes', out_dir, network.fluxes, 'tsv')

    if CLEAN_TEMP:
        file.delete(network.instance_file)
        file.delete(network.file)

    return results, timers


#---------------------- NETWORK ---------------------------
def network_rendering(args:argparse, log_dir:str):
    """Launch rendering as Network description (reaction formula)
    or as Graphs

    Args:
        args (argparse): List or arguments
    """
    if args["keep_import_reactions"]:
        reac_status="import_rxn_"
    else:
        reac_status="rm_rxn_"

    #logger.get_logger(args['infile'], f"{reac_status}network_render", args['verbose'])
    #get_logger(args['infile'], f"{reac_status}network_render", LOG_DIR, args['verbose'])
    logger, log_path = get_logger(
        log_dir=log_dir,
        sbml_file=args['infile'],
        short_option=  f"{reac_status}network_render",
        verbose=args['verbose']
    )

    network = Description(args['infile'], args['keep_import_reactions'], 
                          args['output_dir'], details = args['network_details'],
                          visu = args['visualize'], 
                          visu_no_reaction = args['visualize_without_reactions'],
                          write_file = args['write_file'],)
    
    if network.details:
        network.get_details()
    if network.visu or network.visu_no_reaction:
        time_rendering = time()
        print('Rendering…')
        network.render_network()
        time_rendering = time() - time_rendering
    if network.write_file:
        network.rewrite_sbml_file()
   



#---------------------- FLUX ---------------------------
def network_flux(args:argparse, log_dir:str):
    """Check the Network flux using cobra from a seed2lp result file.
    Needs the sbml file of the network.
    Write the file in output directory.

    Args:
        args (argparse): List or arguments
    """
    # logger.get_logger(args['infile'], "check_fluxes", args['verbose'])
    #get_logger(args['infile'], "check_fluxes", LOG_DIR, args['verbose'])
    logger, log_path = get_logger(
        log_dir=log_dir,
        sbml_file=args['infile'],
        short_option= "check_fluxes",
        verbose=args['verbose']
    )

    input_dict=dict()

    data = load_json(args['result_file'])
    input_dict["Objective"] = data["NETWORK"]["OBJECTIVE"][0][1]

    network = Network(args['infile'], to_print=False, input_dict=input_dict, verbose=args['verbose'])
    maximize, solve = network.convert_data_to_resmod(data)
    network.check_fluxes(maximize,  args["flux_parallel"])

    options = \
        get_reaction_options(network.keep_import_reactions, network.use_topological_injections,
                             network.targets_as_seeds, maximize, network.run_mode, network.accumulation, solve)

    file.save(f'{network.name}_{options["short"]}_fluxes_from_result', args['output_dir'], network.fluxes, 'tsv')


def network_flux_community(args:argparse, log_dir:str):
    """Check the Network flux using cobra from a seed2lp result file.
    Needs a community file containing a list of networks and the sbml directory.
    Write the file in output directory.

    Args:
        args (argparse): List or arguments
    """
    # logger.get_logger(args['comfile'], "check_fluxes", args['verbose'])
    #get_logger(args['comfile'], "check_fluxes", LOG_DIR, args['verbose'])
    logger, log_path = get_logger(
        log_dir=log_dir,
        sbml_file=args['comfile'],
        short_option= "check_fluxes",
        verbose=args['verbose']
    )

    input_dict=dict()

    data = load_json(args['result_file'])
    input_dict["Objective"] = data["NETWORK"]["OBJECTIVE"]


    if data["NETWORK"]["SOLVE"] in NET_TITLE.CONVERT_TITLE_SOLVE:
        run_solve = NET_TITLE.CONVERT_TITLE_SOLVE[data["NETWORK"]["SOLVE"]]
    else:
        run_solve = data["NETWORK"]["SOLVE"]

    temp = get_temp_dir(args)
    
    network=Netcom(args["comfile"], args["sbmldir"], temp, run_solve=run_solve, input_dict=input_dict, to_print=False, 
                   write_sbml=True, equality_flux=args["equality_flux"], verbose=args['verbose'])

    maximize, solve = network.convert_data_to_resmod(data)

    network.check_fluxes(maximize, args['flux_parallel'])
    options = \
        get_reaction_options(network.keep_import_reactions, network.use_topological_injections,
                             network.targets_as_seeds, maximize, network.run_mode, network.accumulation, solve)
    
    file.save(f'{network.name}_{options["short"]}_fluxes_from_result', args['output_dir'], network.fluxes, 'tsv')


#---------------------- SCOPE ---------------------------
def scope(args:argparse, log_dir:str):
    """Check the Network flux using cobra from a seed2lp result file.
    Needs the sbml file of the network.
    Write the file in output directory.

    Args:
        args (argparse): List or arguments
    """
    # logger.get_logger(args['infile'], "scope", args['verbose'])
    #get_logger(args['infile'], "scope", LOG_DIR, args['verbose'])
    logger, log_path = get_logger(
        log_dir=log_dir,
        sbml_file=args['infile'],
        short_option= "scope",
        verbose=args['verbose']
    )

    input_dict=dict()
    network = Network(args['infile'], to_print=False, input_dict=input_dict, verbose=args['verbose'])
    data = load_json(args['result_file'])
    network.convert_data_to_resmod(data)
    scope = Scope(args['infile'], network, args['output_dir'])
    scope.execute()
   


#------------------- CONF FILE ------------------------
def save_conf(args:argparse):
    """Save internal configuration file into output directory

    Args:
        args (argparse): List or arguments
    """
    conf_path = path.join(PROJECT_DIR,'config.yaml')
    new_pah = path.join(args['output_dir'], 'config.yaml')
    copyfile(conf_path, new_pah)


#------------------ WRITE TARGETS ----------------------
def get_objective_targets(args:argparse, log_dir:str):
    """Get the metabolites reactant of objective reaction or found 

    Args:
        args (argparse): List or arguments
    """
    # logger.get_logger(args['infile'], "objective_targets", args['verbose'])
    #get_logger(args['infile'], "objective_targets", LOG_DIR, args['verbose'])
    logger, log_path = get_logger(
        log_dir=log_dir,
        sbml_file=args['infile'],
        short_option= "objective_targets",
        verbose=args['verbose']
    )

    input_dict = get_input_datas(logger)
    if 'objective' in args and args['objective']: # only in full network mode
        input_dict = get_objective(args['objective'], input_dict)
    try:
        chek_inputs(args['infile'], input_dict)
    except ValueError as e :
        logger.error(str(e))
        exit(1)
    network = Network(args['infile'], run_mode="target", input_dict=input_dict, to_print=False, verbose=args['verbose'])

    print("List of targets: ",[*network.targets])
    file.save(f"{network.name}_targets", args['output_dir'],[*network.targets],"txt")





############################################################


def main():
    global LOG_DIR
    args = argument.parse_args()
    cfg = argument.get_config(args, PROJECT_DIR)

    # LOG_DIR =path.join(args.output_dir,"logs")
    # is_valid_dir(LOG_DIR)
    log_dir=path.join(args.output_dir,"logs")
    is_valid_dir(log_dir)

    try:
        if args.cmd in ("community", "fluxcom"):
            for filename in listdir(cfg['sbmldir']):
                check_fbc_support(path.join(cfg['sbmldir'], filename))
        elif args.cmd != "conf":
            check_fbc_support(cfg['infile'])
    except ValueError as e:
        sbml_file = cfg['infile'] if 'infile' in cfg else cfg['comfile']
        logger, _ = get_logger(
            log_dir=log_dir,
            sbml_file=sbml_file,
            short_option=args.cmd,
            verbose=cfg['verbose']
        )
        logger.error(str(e))
        exit(1)

    match args.cmd:
        case "target" | "full" | "fba":
            run_seed2lp(cfg, args.cmd, log_dir)
        case "network":
            network_rendering(cfg, log_dir)
        case "flux":
            network_flux(cfg, log_dir)
        case "scope":
            scope(cfg, log_dir)
        case "conf":
            save_conf(cfg)
        case "objective_targets":
            get_objective_targets(cfg, log_dir)
        case "community":
            community(cfg, args.cmd, log_dir)
        case "fluxcom":
            network_flux_community(cfg, log_dir)
    
if __name__ == '__main__':
    main()
    