from . import flux
from cobra.core import Model

class Resmod:
    def __init__(self, name:str, objectives:list, solver_type:str, search_mode:str, search_type:str,
                 size:int, seeds_list:list, flux_lp:dict, flux_cobra:float=None, run_mode:str=None, accu:bool=False):
        """Initialize Object Resmod

        Args:
            name (str): Name of the solution
            objectives (list): List of objective reaction names
            solver_type (str): Type of solver (Reasoning / FBA / Hybrid)
            search_mode (str): search mode type (Minimize / Submin)
            search_type (str): search type (enumeration / union /intersection)
            size (int): Size of set of seeds
            seeds_list (list): List of seeds
            flux_lp (dict): Dictionnary of all reaction with their LP flux
            flux_cobra (float, optional): Cobra flux calculated (mode Filter, Guess Check). Defaults to None.
            run_mode (str, optional): Running command used (full or target). Defaults to None.
            accu (bool, optional): Is accumulation allowed. Defaults to False.
        """
        self.name = name
        self.objectives = objectives
        self.solver_type = solver_type
        self.search_mode = search_mode
        self.search_type = search_type
        self.size = size
        self.seeds_list = seeds_list
        self.flux_lp = flux_lp
        self.chosen_lp = None
        self.tested_objective = None
        self.objective_flux_seeds = None
        self.objective_flux_demands = None
        self.OK_seeds = False
        self.OK_demands = False
        self.OK = False
        self.run_mode = run_mode
        self.accu = accu
        self.flux_cobra = flux_cobra


   
    ######################## METHODS ########################
    def check_flux(self, model_cobra:Model, try_demands:bool=True):
        """Execute flux calculation usng cobra and store data

        Args:
            model_cobra (Model): Cobra model
            show_messages (bool, optional): Option to show the messages on console. 
                                            Defaults to True. False for hybrid with cobra.
            try_demands (bool, optional): Option to try to add demands if seeds failed.
                                         Defaults to True. False for hybrid with cobra.
        """
        with model_cobra as m:
            flux_output, objective, lp_flux = \
                        flux.calculate(m, self.objectives, self.seeds_list, self.flux_lp, try_demands)
        if flux_output:
            self.tested_objective = objective
            self.chosen_lp = lp_flux
            self.objective_flux_seeds = flux_output['objective_flux_seeds']
            self.objective_flux_demands = flux_output['objective_flux_demands']
            self.OK_seeds = flux_output['OK_seeds']
            self.OK_demands = flux_output['OK_demands']
            self.OK = flux_output['OK']
            self.infeasible_seeds = flux_output['infeasible_seeds']
            self.infeasible_demands = flux_output['infeasible_demands']

    ########################################################