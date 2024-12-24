import argparse
import yaml
from sys import argv
from os import path
from ._version import  __version__
from .file import existant_path, is_valid_dir

DESCRIPTION = """
Seed detection in metabolic networks.
"""
LICENSE = """
            GNU GENERAL PUBLIC LICENSE
              Version 3, 29 June 2007
 """

############################################################
##################### COMMAND PARSER #######################
############################################################

def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "Seed2LP",
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + f"{__version__} \n{LICENSE}")


    pp_verbose = argparse.ArgumentParser(add_help=False)
    pp_verbose.add_argument(
        '--verbose', '-v', action='store_true',
        help="Print every process steps. Debug mode."
    )

    #----------------------- POSITIONNAL ---------------------------
    
    # run / Calculate flux / Network representations
    pp_network = argparse.ArgumentParser(add_help=False)
    pp_network.add_argument(
        dest="infile",
        help="SBML or ASP file containing the graph data.",
        type=existant_path
    )
    # Calculate flux
    pp_result = argparse.ArgumentParser(add_help=False)
    pp_result.add_argument(
        dest="result_file",
        help="Seed2lp result file containing results.",
        type=existant_path
    )
    # Network representations
    pp_output_dir = argparse.ArgumentParser(add_help=False)
    pp_output_dir.add_argument(
        dest="output_dir",
        help="Output directory path",
        type=is_valid_dir
    )

    #--------------------- PARSERS -------------------------
    
    #-------------------------------------------------------
    #          Supplementary data given by user
    #-------------------------------------------------------
    pp_targets_file = argparse.ArgumentParser(add_help=False)
    pp_targets_file.add_argument(
        "-tf", "--targets-file", dest="targets_file", 
        type=existant_path, default=None,
        help="file containing one target per line",
        required=False
    )
    pp_seeds_file = argparse.ArgumentParser(add_help=False)
    pp_seeds_file.add_argument(
        "-sf","--seeds-file", dest="seeds_file", 
        type=existant_path, default=None,
        help="file containing one seed per line",
        required=False
    )
    pp_possible_seeds_file = argparse.ArgumentParser(add_help=False)
    pp_possible_seeds_file.add_argument(
        '-psf', '--possible-seeds-file', dest="possible_seeds_file", 
        type=existant_path, default=None,
        help="file containing a set of compounds in which seed selection will be performed (greedy mode only)",
        required=False
    )
    pp_forbidden_seeds_file = argparse.ArgumentParser(add_help=False)
    pp_forbidden_seeds_file.add_argument(
        '-fsf', '--forbidden-seeds-file', dest="forbidden_seeds_file", 
        type=existant_path, default=None,
        help="file containing one forbidden seed per line",
        required=False
    )
    pp_objective = argparse.ArgumentParser(add_help=False)
    pp_objective.add_argument(
        "-o","--objective", dest="objective", 
        type=str, default=[],
        help="objective reaction to activate in the graph",
        required=False
    )

    #-------------------------------------------------------
    #                      Set mode
    #-------------------------------------------------------
    pp_mode = argparse.ArgumentParser(add_help=False, formatter_class=argparse.RawTextHelpFormatter)
    pp_mode.add_argument(
        '-m', '--mode', dest="mode", 
        type=str, default='subsetmin',  choices=['minimize', 'subsetmin', 'all'], 
        help="""Choose a mode for comuting solutions: \n \
               - minimize : The smallest set of seed \n \
               - subsetmin : All the minimal solution included into solutions (subset minimal)\n \
               - all: Compute subsetmin then minimize""",
        required=False
    )
    pp_solve = argparse.ArgumentParser(add_help=False, formatter_class=argparse.RawTextHelpFormatter)
    pp_solve.add_argument(
        '-so', '--solve', dest="solve", 
        type=str, default='reasoning',  choices=['reasoning', 'filter', 'guess_check', 'guess_check_div', 'hybrid', 'all'], 
        help="Select the solving mode\n \
               - reasoning : Only reasoning, no linear calcul \n \
               - hybrid : Reasoning and linar calcul\n \
               - guess_check : Only reasoning with guess and check results using cobra (adapts rules) \n \
               - guess_check_div : Only reasoning with guess and check results using cobra (adapts rules) and add diversity \n \
               - filter : Only reasoning with a cobra filter validation during search (do not adapt rules)  \n \
               - all : Compute reasoning then hybrid then fba",
        required=False
    )  
    pp_intersection = argparse.ArgumentParser(add_help=False)
    pp_intersection.add_argument(
        '-i', '--intersection', dest="intersection", 
        action='store_true',
        help="Compute intersection of solutions",
        required=False
    )
    pp_union = argparse.ArgumentParser(add_help=False)
    pp_union.add_argument(
        '-u', '--union', dest="union", 
        action='store_true',
        help="Compute union of solutions",
        required=False
    )

    #-------------------------------------------------------
    #               Set of seed restrictions
    #-------------------------------------------------------
    pp_targets_as_seeds = argparse.ArgumentParser(add_help=False)
    pp_targets_as_seeds.add_argument(
        '-tas', '--targets-as-seeds', dest="targets_as_seeds", 
        action='store_true',
        help="Targets are allowed as seeds",
        required=False
    )
    pp_topological_injection = argparse.ArgumentParser(add_help=False)
    pp_topological_injection.add_argument(
        '-ti', '--topological-injection', dest="topological_injection", 
        action='store_true',
        help="Use topological injection found in sbml data",
        required=False
    )
    pp_keep_import_reactions = argparse.ArgumentParser(add_help=False)
    pp_keep_import_reactions.add_argument(
        '-kir', '--keep-import-reactions', dest="keep_import_reactions", 
        action='store_true',
        help="Keep import reactions found in sbml file",
        required=False
    )
    pp_accumulation = argparse.ArgumentParser(add_help=False)
    pp_accumulation.add_argument(
        '-accu', '--accumulation', dest="accumulation", 
        action='store_true',
        help="Accumulation allowed",
        required=False
    )


    #-------------------------------------------------------
    #                   Flux options
    #-------------------------------------------------------
    pp_check_flux= argparse.ArgumentParser(add_help=False)
    pp_check_flux.add_argument(
        '-cf', '--check-flux', dest="check_flux", 
        action='store_true',
        help="Run a flux check on a resulted set of seeds using cobra.py",
        required=False
    )
    pp_maximize_flux = argparse.ArgumentParser(add_help=False)
    pp_maximize_flux.add_argument(
        '-max', '--maximize-flux', dest="maximize_flux", 
        action='store_true',
        help="Maximize the flux of objective reaction",
        required=False
    )

    #-------------------------------------------------------
    #             clingo parameters for solving 
    #-------------------------------------------------------
    pp_clingo_configuration = argparse.ArgumentParser(add_help=False)
    pp_clingo_configuration.add_argument(
        '-cc', '--clingo-configuration', dest="clingo_configuration", 
        type=str, default='jumpy', choices=['jumpy', 'none'],
        help="Changing clingo configuration: jumpy / none",
        required=False
    )
    pp_clingo_strategy = argparse.ArgumentParser(add_help=False)
    pp_clingo_strategy.add_argument(
        '-cs', '--clingo-strategy', dest="clingo_strategy", 
        type=str, default='none', choices=['usc,oll', 'none'],
        help="Changing clingo strategy: usc,oll / none",
        required=False
    )
    pp_time_limit = argparse.ArgumentParser(add_help=False)
    pp_time_limit.add_argument(
        '-tl', '--time-limit', dest="time_limit", 
        type=float, default=0,
        help="Add a time limit in minutes for finding seeds. By default 0, meaning no limit",
        required=False
    )
    pp_number_solution = argparse.ArgumentParser(add_help=False)
    pp_number_solution.add_argument(
        '-nbs', '--number-solution', dest="number_solution", 
        type=int, default=-1,
        help="Change the number of solution limit. By default:-1. \
             \n0 solution means no limit. \
             \n-1 means no enumeration",
        required=False
    )

    #-------------------------------------------------------
    #                ASP Facts storage 
    #-------------------------------------------------------
    pp_instance = argparse.ArgumentParser(add_help=False)
    pp_instance.add_argument(
        '-in', '--instance', dest="instance", 
        type=str,  default=None,
        help="export the ASP instance of input data and quit",
        required=False
    )
    pp_temp = argparse.ArgumentParser(add_help=False)
    pp_temp.add_argument(
        '-tmp', '--temp', dest="temp", 
        type=str,
        help="Temporary directory for hybrid or fba mode.",
        required=False
    )
    
    #-------------------------------------------------------
    #                Network description
    #-------------------------------------------------------
    pp_visualize = argparse.ArgumentParser(add_help=False)
    pp_visualize.add_argument(
        '-vi', '--visualize', dest="visualize", 
        action='store_true',
        help="Render the input graph in png (default: don't render)",
        required=False
    )

    pp_visualize_without_reactions = argparse.ArgumentParser(add_help=False)
    pp_visualize_without_reactions.add_argument(
        '-vir', '--visualize-without-reactions', dest="visualize_without_reactions", 
        action='store_true',
        help="Render the input graph  without reactions in png (default: don't render)",
        required=False
    )
    pp_network_details = argparse.ArgumentParser(add_help=False)
    pp_network_details.add_argument(
        '-nd', '--network-details', dest="network_details", 
        action='store_true',
        help="Render the description fo the network from lp and with cobra",
        required=False
    )
    pp_write_file = argparse.ArgumentParser(add_help=False)
    pp_write_file.add_argument(
        '-wf', '--write-file', dest="write_file", 
        action='store_true',
        help="Write the network into a sbml file after applying modifications on it for simplifying reasoning.",
        required=False
    )

    #-------------------------------------------------------
    #                     Config file
    #-------------------------------------------------------
    pp_config = argparse.ArgumentParser(add_help=False)
    pp_config.add_argument(
        '-conf', '--config-file', dest="config_file", 
        type=str,
        help="Configuration file to use.",
        required=False
    )

    #-------------------------------------------------------
    #                Commands commposition
    #-------------------------------------------------------
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands:',
        dest="cmd",)

    subparsers.add_parser(
        "target",
        help="Run seeds detection focusing on targets.",
        parents=[
            pp_verbose,
            pp_network, pp_output_dir,
            pp_targets_file, 
            pp_seeds_file, 
            pp_possible_seeds_file, 
            pp_forbidden_seeds_file,
            pp_mode, pp_solve, pp_intersection, pp_union,
            pp_targets_as_seeds, pp_topological_injection, pp_keep_import_reactions, 
            pp_clingo_configuration, pp_clingo_strategy, pp_time_limit, pp_number_solution, 
            pp_instance, pp_temp, pp_check_flux, pp_maximize_flux,
            pp_config, pp_accumulation
        ],
        description=
        """
        Seed Searching mode focusing on reachability of targetted metabolites (reactants of objective reaction).
        It is possible to add targets or change the objective reaction by using the option -tf/--targets-file.
        Multiple solving mode (-so/--solve) are available:
          - reasoning: Only focus in reachability of metabolites using Network Expanion
          - filter: First uses Network Expanion, then check the flux with COBRApy inferred by seeds
          - guess_check: Uses Network Expanion, check flux with COBRApy and return results to solver to dismiss superset of results
          - guess_check_div: Guess check but also forbids subset of seed as next result in order to reduce intersection of solutions
          - hybrid: First uses Network Expansion then calculate FBA constraints with clingo-lpx
        """,
        usage="""
        seed2lp target network_file  output_dir \n 
        """
    )

    subparsers.add_parser(
        "full",
        help="Run seeds detection focusing on full network.",
        parents=[
            pp_verbose,
            pp_network, pp_output_dir,
            pp_objective,
            pp_seeds_file, 
            pp_possible_seeds_file, 
            pp_forbidden_seeds_file,
            pp_mode, pp_solve, pp_intersection, pp_union, 
            pp_topological_injection, pp_keep_import_reactions, 
            pp_clingo_configuration, pp_clingo_strategy, pp_time_limit, pp_number_solution, 
            pp_instance, pp_temp, pp_check_flux, pp_maximize_flux,
            pp_config,  pp_accumulation
        ],
        description=
        """
        Seed Searching mode focusing on reachability of all metabolites of the GSMN.
        It is possible to change the objective reaction by using the option -o/--objective for flux checking.
        Multiple solving mode (-so/--solve) are available:
          - reasoning: Only focus in reachability of metabolites using Network Expanion
          - filter: First uses Network Expanion, then check the flux with COBRApy inferred by seeds
          - guess_check: Uses Network Expanion, check flux with COBRApy and return results to solver to dismiss superset of results
          - guess_check_div: Guess check but also forbids subset of seed as next result in order to reduce intersection of solutions
          - hybrid: First uses Network Expansion then calculate FBA constraints with clingo-lpx
        """,
        usage="""
        seed2lp full network_file output_dir \n 
        """
    )

    subparsers.add_parser(
        "fba",
        help="Run seeds detection in aleatory way focusing on fba.",
        parents=[
            pp_verbose,
            pp_network, pp_output_dir,
            pp_objective,
            pp_seeds_file, 
            pp_possible_seeds_file, 
            pp_forbidden_seeds_file,
            pp_mode, pp_intersection, pp_union, 
            pp_targets_as_seeds, pp_topological_injection, pp_keep_import_reactions, 
            pp_clingo_configuration, pp_clingo_strategy, pp_time_limit, pp_number_solution, 
            pp_instance, pp_temp, pp_check_flux, pp_maximize_flux,
            pp_config
        ],
        description=
        """
        Random Seed Searching mode focusing in FBA constraints using clingo-lpx solver.
        It is possible to change the objective reaction by using the option -o/--objective for flux checking.
        """,
        usage="""
        seed2lp fba network_file  \n 
        """
    )
    
    subparsers.add_parser(
        "network",
        help="Give Network Details with reactions, create graph of Network, rewrite network sbml file",
        parents=[
            pp_verbose,
            pp_network, pp_output_dir,
            pp_keep_import_reactions, 
            pp_visualize, pp_visualize_without_reactions,
            pp_network_details, pp_write_file
        ],
        description=
        """
        This functionnality aims to help people with the networks by:
          - Creating a graph with or without the reactions boxes (-vi/--visualize or -vir/--visualize-without-reaction)
          - Creating a file with list and formula of reactions from original GSMN, the normalized one and a diff file (-nd/--network-details)
          - Writing the normalized sbml file (-wf/--write-file)
        """,
        usage="""
        seed2lp network [network_file] [output_dir] --visualize \n 
        """
    )

    subparsers.add_parser(
        "flux",
        help="Calculate cobra flux from seed2lp result file, using sbml file",
        parents=[
            pp_verbose, pp_network, pp_result, pp_output_dir
        ],
        description=
        """
        From Seed2lp seed searching results json file, this functionnality calculate fluxes inferred by seeds for all models using COBRApy.
        Can be used for other tool results if the results file has the same json structure.
        """,
        usage="""
        seed2lp flux [sbml_file] [seed2lp_result_file] [output_directory] \n 
        """
    )

    subparsers.add_parser(
        "scope",
        help="From seeds determine scope of the network.",
        parents=[
            pp_verbose, pp_network, pp_result, pp_output_dir, pp_temp
        ],
        description=
        """
        From Seed2lp seed searching results json file, this functionnality detemine scope inferred by seeeds using Network Expansion.
        Can be used for other tool results if the results file has the same json structure.
        The scope calculation is done with MeneTools.
        """,
        usage="""
        seed2lp scope [sbml_file] [seed2lp_result_file] [output_directory] \n 
        """
    )

    subparsers.add_parser(
        "conf",
        help="Copy and save a conf file. ",
        parents=[
            pp_output_dir
        ],
        description=
        """
        Copy the internal configuration fil an dsave it. 
        The configuration file saved can be modified and reused for all seed searching methods with the option -tmp/--temp
        """,
        usage="""
        seed2lp conf [output_directory] \n 
        """
    )

    subparsers.add_parser(
        "objective_targets",
        help="Get the objective reaction reactants metabolites and write them into a file",
        parents=[
            pp_verbose, pp_network, pp_objective, pp_output_dir
        ],
        description=
        """
        From an sbml file, either :
          - Find the objective and write the reactants into a file
          - Write the reactants of the given objectve (-o/--objective) into a file
        """,
        usage="""
        seed2lp conf [output_directory] \n 
        """
    )

    return parser

def parse_args(args: iter = None) -> dict:
    return cli_parser().parse_args(args)


####################### FUNCTIONS ##########################


def get_config(args:argparse.Namespace, project_source):
    dict_check = {"--verbose" : "-v",
                    "--mode" : "-m",
                    "--solve" : "-so",
                    "--intersection" : "-i",
                    "--union" : "-u",
                    "--targets-as-seeds" : "-tas",
                    "--topological-injection" : "-ti",
                    "--keep-import-reactions" : "-kir",
                    "--check-flux" : "-cf",
                    "--maximize-flux" : "-max",
                    "--clingo-configuration" : "-cc",
                    "--clingo-strategy" : "-cs",
                    "--time-limit" : "-tl",
                    "--number-solution" : "-nbs",
                    "--temp" : "-tmp",
                    "--accumulation" : "-accu"}
    
    conf_argparse = vars(args)
    conf_file=None
    # Get config file path
    if "config_file" not in args:
        cfg = conf_argparse
    elif args.config_file == None:
        conf_file = path.join(project_source,'config.yaml')
    else:
        conf_file = args.config_file

    # Get configs from file
    if conf_file is not None:
        with open(conf_file, "r") as ymlfile:
            cfg_file = yaml.load(ymlfile, Loader=yaml.FullLoader)

    # Overwrite configs with cli argument
    match args.cmd:
        case "target" | "full" | "fba":
            for key, value in conf_argparse.items():
                cfg = cfg_file['seed2lp']
                if key not in cfg:
                    cfg[key] = value
                else:
                    for long , short in dict_check.items():
                        if long in argv or short in argv:
                            long = long.lstrip("-")
                            long = long.replace("-","_")
                            cfg[long] = conf_argparse[long]           

    return cfg