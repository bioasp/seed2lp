# Object Network constitued of
#   - file (str): Path of input network file (sbml)
#   - run_mode (str): Running command used (full or target)
#   - name (str): Species name/ID from file name
#   - targets_as_seeds (bool): Targets can't be seeds and are noted as forbidden
#   - use_topological_injections (bool): Metabolite of import reaction are seeds
#   - keep_import_reactions (bool): Import reactions are removed
#   - reactions (list): List of reactions (object Reaction)
#   - targets (list): List of target (object Metabolite)
#   - seeds (list): List of seed given by the user (object Metabolite)
#   - possible_seeds (list): List of possible seeds given by the user (object Metabolite)
#   - forbiddend_seed (list): List of forbidden seeds (object Metabolite)
#   - facts (str): Conversion sbml into asp facts
#   - fluxes (list): List of flux check on all set of seeds

import os
import pandas as pd
from .reaction import Reaction
import seed2lp.sbml as SBML
from .utils import quoted
from . import flux
from .resmod import Resmod
from time import time
from . import color
from . import logger


FLUX_MESSAGE=\
f""" {color.bold} "Cobra (seeds)" {color.reset} indicates the maximum flux  
obtained in FBA from the seeds after shutting 
off all other exchange reactions. If the maximum 
flux is null, a test is performed opening demand 
reactions for the objective reaction's products, 
in order to test the effect of their accumulation 
({color.bold}"cobra (demands)"{color.reset} ). If this test is not performed, 
"NA" value is indicated.""" 

WARNING_MESSAGE_LP_COBRA=\
f"""Cobra flux and LP flux might be 
different because the option -max/--maximize 
is not used"""


class Network:
    def __init__(self, file:str, run_mode:str=None, targets_as_seeds:bool=False, use_topological_injections:bool=False, 
                 keep_import_reactions:bool=True, input_dict:dict=None, accumulation:bool=False, to_print:bool=True, 
                 write_sbml:bool=False):
        """Initialize Object Network

        Args:
            run_mode (str): Running command used (full or target)
            file (str): Path of input network file (sbml)
            targets_as_seeds (bool): Targets can't be seeds and are noted as forbidden
            use_topological_injections (bool): Metabolite of import reaction are seeds
            keep_import_reactions (bool): Import reactions are not removed
            accumulation (bool, optional): Is accumulation authorized. Defaults to False.
            to_print (bool, optional): Write messages into console if True. Defaults to True.
            write_sbml (bool, optional): Is a writing SBML file mode or not. Defaults to False.
        """
        self.file = file
        self.run_mode = run_mode
        self.file_extension = ""
        self._set_file_extension(file)
        self._set_name()

        self.sbml, self.sbml_first_line = SBML.get_root(self.file)
        self.model = SBML.get_model(self.sbml)
        self.fbc = SBML.get_fbc(self.sbml)
        self.parameters = SBML.get_listOfParameters(self.model)

        self.targets_as_seeds = targets_as_seeds
        self.use_topological_injections = use_topological_injections
        self.keep_import_reactions = keep_import_reactions
        self.reactions = list()
        # list of reaction having reactants and products switched
        self.meta_modified_reactions = dict()
        # list of reaction having the reversibility changed
        self.reversible_modified_reactions = dict()
        # list of reaction deleted because boudaries [0,0]
        self.deleted_reactions = dict()
        # list of exchange reaction
        self.exchanged_reactions = dict()
        

        self.objectives = list()
        self.is_objective_error = False
        self.targets=list()
        self.seeds = list()
        self.possible_seeds = list()
        self.is_subseed = False
        self.forbidden_seeds = list()
        self.facts = ""
        self.meta_exchange_list = list()
        self.meta_transport_list = list()
        # metabolite of import reaction having multiple metabolite such as None -> A+B
        self.meta_multiple_import_list = list()
        self.accumulation = accumulation

        self.instance_file=str()

        if self.run_mode is not None:
            self.init_with_inputs(input_dict)
        self.get_network(to_print, write_sbml)
        self.result_seeds=list()
        self.fluxes = pd.DataFrame()


    ######################## GETTER ########################
    def _get_reactions(self):
        return self.reactions
    
    def _get_objectives(self):
        return self.objectives

    def _get_result_seeds(self):
        return self.result_seeds
    ########################################################

    ######################## SETTER ########################
    def _set_file_extension(self, file:str):
        ext = os.path.splitext(file)[1]
        self.file_extension = ext

    def _set_name(self):
        n = f'{os.path.splitext(os.path.basename(self.file))[0]}'
        self.name = n
        print(f"Network name: {n}")

    def _set_reactions(self, reactions:list):
        self.reactions = reactions
    
    def _set_result_seeds(self, result_seeds:list):
        self.result_seeds = result_seeds
    ########################################################

    ######################## METHODS ########################
    def get_objective_reactant(self):
        """Get the objective reactants from SBML file
        """
        logger.log.info("Finding list of reactants from opbjective reaction...")
        for obj in self.objectives:
            reactants = SBML.get_listOfReactants_from_name(self.model, obj)
            for reactant in reactants:
                react_name = reactant.attrib.get('species')
                if react_name not in self.targets:
                    self.targets.append(react_name)
        logger.log.info("... DONE")

    def get_boundaries(self, reaction):
        """Get Boundaries of a reaction

        Args:
            reaction (etree line): Reaction from etree package

        Returns:
            lbound (float), ubound (float): lower and uppper boundaries value
        """
        lower_bound = self.parameters[reaction.attrib.get('{'+self.fbc+'}lowerFluxBound')] \
                    if type(reaction.attrib.get('{'+self.fbc+'}lowerFluxBound')) is not float \
                    else '"'+reaction.attrib.get('{'+self.fbc+'}lowerFluxBound')+'"'
        lbound = round(float(lower_bound),10)
        upper_bound = self.parameters[reaction.attrib.get('{'+self.fbc+'}upperFluxBound')] \
                    if type(reaction.attrib.get('{'+self.fbc+'}upperFluxBound')) is not float \
                    else '"'+reaction.attrib.get('{'+self.fbc+'}upperFluxBound')+'"'
        ubound = round(float(upper_bound),10)
        return lbound, ubound

    def find_objectives(self, input_dict:dict):
        """Find the objective reaction from SBML file
        If mode Target and no target set : put reactant of objective
        as targets

        Args:
            input_dict (dict): Constructed dictionnary of inputs

        Raises:
            ValueError: Multiple objective reaction with coefficient 1 found
            ValueError: No objective reaction found or none has coefficient 1
        """
        logger.print_log("\n Finding objective ...", "info")
        objectives = SBML.get_listOfFluxObjectives(self.model, self.fbc)
        obj_found = None
        is_reactant_found = False
        for obj in objectives:
            coef=float(obj[1])
            if obj_found is None:
                #For now works with only one objective
                if coef == 1:
                    obj_found = obj[0]
                    reaction = obj[2]
                    lbound, ubound = self.get_boundaries(reaction)
            # multiple objectives found with coefficient 1
            else:
                if coef == 1:
                    objectives = None
                    obj_found = None
                    self.is_objective_error = True
                    raise ValueError(f"Multiple objective reaction with coefficient 1 found\n")
                
        if not obj_found:
            self.is_objective_error = True
            raise ValueError(f"No objective reaction found or none has coefficient 1\n")
        else:
            # Works for 1 objective reation for now
            logger.print_log(f'Objective found : {color.bold}{obj_found}{color.reset}\n', "info")
            if lbound == 0 and ubound == 0:
                self.is_objective_error = True
                raise ValueError(f"Lower and upper boundaries are [0,0] \nfor objetive reaction {obj_found}\n")
            self.objectives = [obj_found]
            if (self.run_mode == "target" or self.run_mode == "fba")\
              and ('Targets' not in input_dict or not input_dict["Targets"]):
                self.get_objective_reactant()
                is_reactant_found = True
        return is_reactant_found


    def init_with_inputs(self, input_dict:dict):
        """Init Network object with user inputs data
        Construct the init messages

        Args:
            input_dict (dict): Constructed dictionnary of inputs
        """
        tgt_message = ""
        if self.run_mode == "target":
            tgt_message = "Targets set:\n"
        elif self.run_mode == "fba":
            tgt_message = "Targets detected for option \"target as seeds\":\n"
        else:
            tgt_message = "Targets set:\nAll metabolites as target\n"
        obj_message = f"Objective set:\n"
        kir_mess = "Import reaction: "
        ti_inject = "Product of import reaction set as seed: "
        tas_mess = "Targets can be seeds: "
        accu_mess =  "Accumulation: "
        
        # init network with input data
        if input_dict:
            if "Targets" in input_dict and input_dict["Targets"]:
                self.targets = input_dict["Targets"]
                tgt_message += "    Metabolites from target file\n"
            if "Seeds" in input_dict:
                self.seeds = input_dict["Seeds"]
            if "Possible seeds" in input_dict:
                self.possible_seeds = input_dict["Possible seeds"]
                self.is_subseed = True
            if "Forbidden seeds" in input_dict:
                self.forbidden_seeds = input_dict["Forbidden seeds"]
            # Objective given in target file (mode target) 
            # or command line (mode full)
            if "Objective" in input_dict and input_dict["Objective"]:
                self.objectives = input_dict["Objective"]
                if self.run_mode == "target":
                    obj_message += "    Objective reaction from target file\n"
                else:
                    obj_message += "    Objective reaction from command line\n"
                obj_string = " ".join([str(item) for item in self.objectives])
                obj_message += f'\n\nObjective : {obj_string}'
                # Reactant of objective set as target on target mode
                # No needed on full mode (all metabolite are set as target)
                if self.run_mode != "full":
                    self.get_objective_reactant()
                    tgt_message +=  "    Reactant of objective reaction\n    from target file\n"
        
        # Find objective into sbml file if not given by user        
        if self.objectives is None or not self.objectives:
            try:
                is_reactant_found = self.find_objectives(input_dict) 
                obj_message += "    Objective reaction from SBML file"
                obj_string = " ".join([str(item) for item in self.objectives])
                obj_message += f'\n\nObjective : {obj_string}'
                if self.run_mode != "full" \
                  and is_reactant_found:
                    tgt_message +=  "    Reactant of objective reaction\n    from SBML file\n"
            except ValueError as e:
                if self.run_mode == "target" \
                  and (self.targets is None or not self.targets):
                    tgt_message += "    No target found"
                obj_message += "    No objective reaction found"
                logger.log.error(str(e))
            
        if self.keep_import_reactions:
            kir_mess += " Kept"
        else:
            kir_mess += " Removed"

        if self.use_topological_injections:
            ti_inject += " Yes"
        else:
            ti_inject += " No"

        if self.run_mode != "full"  and self.targets_as_seeds:
            tas_mess += " Yes"
        elif self.run_mode == "full":
            tas_mess = None
        else:
            tas_mess += " No"

        if self.accumulation:
            accu_mess += " Allowed"
        else:
            accu_mess += " Forbidden"

        self.write_cases_messages(tgt_message, obj_message, [kir_mess, ti_inject, tas_mess, accu_mess])
    

    def add_reaction(self, reaction:Reaction):
        """Add a reaction into the Network list of reaction

        Args:
            reaction (Reaction): Object reaction
        """
        reactions_list = self._get_reactions()
        reactions_list.append(reaction)
        self._set_reactions(reactions_list)

    def add_objective(self, reaction_name:str):
        """Add a reaction into objecive list

        Args:
            reaction_name (str): Reaction to add as objective
        """
        objectives_list = self._get_objectives()
        objectives_list.append(reaction_name)
        self.objectives = objectives_list

    def get_network(self, to_print:bool=True, write_sbml:bool=False):
        """Get the description of the Network from SBML file
        Construct list of reactants and products
        Correct the reversibility based on boundaries
        For import or export reaction, if reversibilité is corrected
        correct also reactants and products by exchanging them
        When writing SBML, delete Import reaction

        Args:
            to_print (bool, optional): _description_. Defaults to True.
            write_sbml (bool, optional): Is a writing SBML file mode or not. Defaults to False.
        """
        reactions_list = SBML.get_listOfReactions(self.model)
        warning_message = ""
        info_message = ""
        for r in reactions_list:
            reaction = Reaction(r.attrib.get("id"))
            reaction.is_exchange=False
            source_reversible = False if r.attrib.get('reversible') == 'false' else True           
            # Treating reverserbility separately, lower bound can stay to 0
            reaction.lbound, reaction.ubound = self.get_boundaries(r)

            # If the reaction can never have flux, meaning lower_bound = 0 and upper_bound = 0
            # The reaction is deleted from the network
            if reaction.lbound == 0 and reaction.ubound == 0:
                self.deleted_reactions[reaction.name] = len(self.reactions)
                warning_message += f"\n - {reaction.name}: Deleted.\n     Boundaries was: [{reaction.lbound} ; {reaction.ubound}]\n"
                # Not added not reaction list of the network
                continue

            reactants = SBML.get_listOfReactants(r)
            products = SBML.get_listOfProducts(r)

            # uses the definition of boundaries as cobra
            # a reaction is in boundaries (so exchange reaction)
            # when a reaction has only one metabolite and 
            # does not have reactants or products
            if not (reactants and products):
                if (reactants and len(reactants) == 1) \
                    or (products and len(products) == 1):
                    # Cobra deifinition of exchange reaction
                    reaction.is_exchange=True
                    self.exchanged_reactions[reaction.name] = len(self.reactions) 
                elif not reactants and not products:
                    # Reaction with boundaries [0,0] is deleted on the network for reasoning part.
                    # But it is not deleted on sbml file when rewritten (command network otion rewrite file).
                    warning_message += f" - {reaction.name} deleted. No reactants and no products.\n"
                    continue
                else:
                    self.exchanged_reactions[reaction.name] = len(self.reactions) 
                    # A reaction is multiple exchange
                    # when None -> A + B || A + B -> None || None <-> A + B || A + B <-> None
                    warning_message += f" - {reaction.name} is multiple (more than 1) metabolites import/export reaction. "
                    if not self.keep_import_reactions:
                        warning_message += "\n\tDeleted as it is an import reaction.\n"
                    else:
                        warning_message += "\n"


            # Check if transport reactions
            if len(reactants)==1 and len(products)==1:
                if reactants[0][0].rsplit('_', 1)[0] == products[0][0].rsplit('_', 1)[0]:
                    reaction.is_transport=True


            # import reactions to remove 

            # For each reaction check if the lower and upper bounds 
            # have the same sign (not reversible) 
            # Cases : [-1000,-10] , [-1000,0], [0, 1000], [10,1000]
            if reaction.lbound*reaction.ubound >= 0:
                reaction.reversible=False
                # Reaction written backwards
                # M -> None, with boundaries [-1000, -10] is import reaction case
                # R -> P, with boundaries [-1000, -10] is P -> R
                # None -> M, with boundaries [-1000, -10] is export reaction case
                # import reactions removed, needs no reactant
                # exchange reactants and products
                if reaction.ubound <= 0:
                    warning_message += f" - {reaction.name}: Reactants and products switched.\n     Boundaries was: [{reaction.lbound} ; {reaction.ubound}]\n"
                    meta = products
                    products = reactants
                    reactants = meta
                    reaction.is_meta_modified = True
                    # Index of reaction needed for network rewriting
                    self.meta_modified_reactions[reaction.name] = len(self.reactions)

                    # Change the bounds
                    if reaction.ubound != 0:
                        bound = - reaction.ubound
                    else:
                        bound = reaction.ubound
                    if reaction.lbound != 0:
                        reaction.ubound = - reaction.lbound
                    else:
                        reaction.ubound = reaction.lbound
                    reaction.lbound = bound
            # The upper and lower bound does not have the same sign
            # The reaction is reversible
            # Cases: [-1000,10], [-10,1000], ...
            else:
                reaction.reversible = True
            react_exchange_list,react_transport_list = reaction.add_metabolites_from_list(reactants,"reactant", 
                                                                self.meta_exchange_list, self.meta_transport_list)
            self.meta_exchange_list.extend(y for y in react_exchange_list if y not in self.meta_exchange_list)
            self.meta_transport_list.extend(y for y in react_transport_list if y not in self.meta_transport_list)
            
            prod_exchange_list, prod_transpor_list = reaction.add_metabolites_from_list(products,"product", 
                                                                self.meta_exchange_list, self.meta_transport_list) 
            self.meta_exchange_list.extend(y for y in prod_exchange_list if y not in self.meta_exchange_list)
            self.meta_transport_list.extend(y for y in prod_transpor_list if y not in self.meta_transport_list)

            reaction.is_reversible_modified = source_reversible != reaction.reversible

            if reaction.is_reversible_modified:
                # Index of reaction needed for network rewriting
                self.reversible_modified_reactions[reaction.name] = len(self.reactions)
                info_message += f"\n - {reaction.name}: Reversibility modified."
            self.add_reaction(reaction)

        # Because of the order of reaction, the metabolites can be found as exchanged
        # after another reaction, it is needed to correct that
        for reaction in self.reactions:
            for metabolite in reaction.products:
                if metabolite.name in self.meta_exchange_list and not metabolite.type == "exchange":
                    metabolite.type = "exchange"
                if metabolite.name in self.meta_transport_list and not metabolite.type == "transport":
                    metabolite.type = "transport"
            for metabolite in reaction.reactants:
                if metabolite.name in self.meta_exchange_list and not metabolite.type == "exchange":
                    metabolite.type = "exchange"
                if metabolite.name in self.meta_transport_list and not metabolite.type == "transport":
                    metabolite.type = "transport"
            # Change boundaries for rewritting sbml
            # this part is not needed for the ASP writing because we need the original value of boundaries
            # for hybrid-lpx to reopen the import boundaries to its origin value and not max
            if write_sbml and reaction.is_exchange and not self.keep_import_reactions:
                if len(reaction.reactants) == 0:
                    reaction.ubound=0
                if len(reaction.products) == 0:
                    reaction.lbound=0
        if (to_print):
            if warning_message:
                logger.log.warning(warning_message)
            if info_message:
                logger.log.info(info_message)
        else:
            logger.log.info(warning_message)
            logger.log.info(info_message)
            print("____________________________________________\n")

    
    def convert_to_facts(self):
        """Convert the corected Network into ASP facts
        """
        logger.log.info("Converting Network into ASP facts ...")
        facts = ""
        # Upper bound does not change on forward reaction
        
        for reaction in self.reactions:
            facts += reaction.convert_to_facts(self.keep_import_reactions, 
                                                  self.use_topological_injections)
                

        for objective in self.objectives:
            facts += '\nobjective("'+objective+'").'
        for seed in self.seeds:
            facts += f'\nseed_user({quoted(seed)}).' 
        for target in self.targets:
            facts += f'\ntarget({quoted(target)}).'
        for forbidden in self.forbidden_seeds:
            facts += f'\nforbidden({quoted(forbidden)}).'
        for possible in self.possible_seeds:
            facts += f'\np_seed({quoted(possible)}).'
            
        self.facts = facts
        logger.log.info("... DONE")

    def simplify(self):
        """Lighten the Network Object, only facts needed
        """
        self.model = None
        self.sbml = None
        self.reactions = None
        self.seeds = None
        self.forbidden_seeds = None

    
    def add_result_seeds(self, solver_type:str, search_info:str, model_name:str, 
                         size:int, seeds:list, flux_lp:dict=None, flux_cobra:float=None):
        """Add a formated resulted set of seeds into a list

        Args:
            solver_type (str): Type of solver (Reasoning / FBA / Hybrid)
            search_mode (str): search mode type (Minimize / Submin 
                            containing search type enumeration / union /intersection)
            model_name (str): model name
            len (int): length of a set of seed
            seeds (list): list of seeds
            flux_lp (dict, optional): Dictionnary of all reaction with their LP flux. Defaults to None.
            flux_cobra (float, optional): Cobra flux calculated (mode Filter, Guess Check). Defaults to None.
        """
        result_seeds_list = self._get_result_seeds()
        match search_info:
            # FROM SOLVER
            case "minimize-one-model":
                search_mode="Minimize"
                search_type="Optimum"
            case "minimize-intersection":
                search_mode="Minimize"
                search_type="Intersection"
            case "minimize-union":
                search_mode="Minimize"
                search_type="Union"
            case "minimize-enumeration":
                search_mode="Minimize"
                search_type="Enumeration"
            case "submin-enumeration":
                search_mode="Subset Minimal"
                search_type="Enumeration"
            case "submin-intersection":
                search_mode="Subset Minimal"
                search_type="Intersection"
            # FROM RESULT FILE
            case'MINIMIZE OPTIMUM':
                search_mode = 'Minimize'
                search_type = 'Optimum'
            case 'MINIMIZE INTERSECTION' \
                | 'MINIMIZE INTERSECTION FILTER' \
                | 'MINIMIZE INTERSECTION GUESS-CHECK' \
                | 'MINIMIZE INTERSECTION GUESS-CHECK-DIVERSITY':
                search_mode = 'Minimize'
                search_type = 'Intersection'
            case 'MINIMIZE UNION' \
                | 'MINIMIZE UNION FILTER' \
                | 'MINIMIZE UNION GUESS-CHECK' \
                | 'MINIMIZE UNION GUESS-CHECK-DIVERSITY':
                search_mode = 'Minimize'
                search_type = 'Union'
            case 'MINIMIZE ENUMERATION'\
                | 'MINIMIZE ENUMERATION FILTER' \
                | 'MINIMIZE ENUMERATION GUESS-CHECK' \
                | 'MINIMIZE ENUMERATION GUESS-CHECK-DIVERSITY':
                search_mode = 'Minimize'
                search_type = 'Enumeration'
            case 'SUBSET MINIMAL ENUMERATION' \
                | 'SUBSET MINIMAL ENUMERATION FILTER' \
                | 'SUBSET MINIMAL ENUMERATION GUESS-CHECK' \
                | 'SUBSET MINIMAL ENUMERATION GUESS-CHECK-DIVERSITY':
                search_mode = 'Subset Minimal'
                search_type = 'Enumeration'
            case 'SUBSET MINIMAL INTERSECTION'\
                | 'SUBSET MINIMAL INTERSECTION FILTER' \
                | 'SUBSET MINIMAL INTERSECTION GUESS-CHECK' \
                | 'SUBSET MINIMAL INTERSECTION GUESS-CHECK-DIVERSITY':
                search_mode = 'Subset Minimal'
                search_type = 'Intersection'
            case _:
                search_mode = 'Other'
                search_type = 'Enumeration'
        result = Resmod(model_name, self.objectives, solver_type, search_mode, search_type, size, seeds, flux_lp, flux_cobra, self.run_mode, self.accumulation)
        result_seeds_list.append(result)
        self._set_result_seeds(result_seeds_list)


    
    def check_fluxes(self, maximize:bool):
        """Calculate the flux using Cobra and get the flux from lp for all solutions (set of seed).
        Store information and data into dataframe

        Args:
            maximize (bool): Determine if Maximize option is used
        """
        dtypes = {'species':'str',
                  'biomass_reaction':'str',
                  'solver_type':'str',
                  'search_mode':'str',
                  'search_type':'str',
                  'accumulation':'str',
                  'model':'str',
                  'size':'int',
                  'lp_flux':'float',
                  'cobra_flux_init':'float',
                  'cobra_flux_no_import':'float',
                  'cobra_flux_seeds':'float',
                  'cobra_flux_demands':'float',
                  'has_flux':'str',
                  'has_flux_seeds':'str',
                  'has_flux_demands':'str',
                  'timer':'float'
                 }
        fluxes = pd.DataFrame(columns=['species','biomass_reaction', 'solver_type', 'search_mode', 'search_type',
                                       'accumulation', 'model', 'size', 'lp_flux', 'cobra_flux_init', 'cobra_flux_no_import',
                                       'cobra_flux_seeds', 'cobra_flux_demands', 'has_flux','has_flux_seeds',
                                       'has_flux_demands', 'timer'])
        fluxes = fluxes.astype(dtypes)
        
        if self.objectives:
            if self.result_seeds:
                logger.log.info("Check fluxes Starting")
                model = flux.get_model(self.file)
                fluxes_init = flux.get_init(model, self.objectives)
                if not self.keep_import_reactions:
                    fluxes_no_import = flux.stop_flux(model, self.objectives)
                self.model = model
                print(color.purple+"\n____________________________________________")
                print("____________________________________________\n"+color.reset)
                print("RESULTS".center(44))
                print(color.purple+"____________________________________________")
                print("____________________________________________\n"+color.reset)

                print(FLUX_MESSAGE)

                prev_solver_type=None
                prev_search_mode=None
                has_warning=False

                for result in self.result_seeds :
                    if prev_search_mode == None or result.search_mode != prev_search_mode:
                        if has_warning:
                            print("\n")
                            logger.log.warning(WARNING_MESSAGE_LP_COBRA)
                        print(color.yellow+"\n____________________________________________")
                        print("____________________________________________\n"+color.reset)
                        print(result.search_mode.center(44))
                        prev_search_mode = result.search_mode
                        prev_solver_type=None
                    if prev_solver_type == None or result.solver_type != prev_solver_type:
                        print(color.yellow+"--------------------------------------------"+color.reset)
                        print(result.solver_type.center(44))
                        print(color.yellow+". . . . . . . . . . ".center(44)+color.reset)
                        prev_solver_type=result.solver_type
                        type_column = "name | cobra (seeds) | cobra (demands)"
                        separate_line="-----|---------------|-----------------"
                        has_warning=False
                        if result.solver_type=="HYBRID" or result.solver_type=="FBA":
                            type_column+=" | LP"
                            separate_line+="|----"
                        print(type_column)
                        print(separate_line)

                    flux_time = time()
                    result.check_flux(self.model)

                    warn = print_flux(result,maximize)
                    if warn:
                        has_warning=True
                   

                    flux_time = time() - flux_time
                    flux_time=round(flux_time, 3)
                    flux_init = fluxes_init[result.tested_objective]
                    if self.keep_import_reactions:
                        flux_no_import = None
                    else:
                        flux_no_import = fluxes_no_import[result.tested_objective]
                    result_flux =  pd.DataFrame([[self.name, result.tested_objective, result.solver_type, result.search_mode,
                                                 result.search_type, str(self.accumulation), result.name, result.size, result.chosen_lp, flux_init, 
                                                 flux_no_import, result.objective_flux_seeds, result.objective_flux_demands,
                                                 str(result.OK), str(result.OK_seeds), str(result.OK_demands), flux_time]],
                                        columns=['species','biomass_reaction', 'solver_type', 'search_mode', 
                                                 'search_type', 'accumulation', 'model', 'size', 'lp_flux', 'cobra_flux_init', 
                                                 'cobra_flux_no_import', 'cobra_flux_seeds', 'cobra_flux_demands', 
                                                 'has_flux','has_flux_seeds', 'has_flux_demands', 'timer'])
                    result_flux = result_flux.astype(dtypes)
                    fluxes = pd.concat([fluxes, result_flux], ignore_index=True)
                
                if has_warning:
                    print("\n")
                    logger.log.warning(WARNING_MESSAGE_LP_COBRA)
                print(color.yellow+"\n____________________________________________\n"+color.reset)
            else:
                print(color.red_bright+"No solution found"+color.reset)
        else:
            print(color.red_bright+"No objective found, can't run cobra optimization"+color.reset)
        self.fluxes = fluxes

         
    def convert_data_to_resmod(self, data):
        """Convert json data into Resmod object in order to add the list to Netork object.

        Args:
            data (dict): Json data from previous seed2lp result file
        """
        logger.log.info("Converting data from result file ...")
        reaction_option = data["OPTIONS"]["REACTION"]
        match reaction_option:
            case "Remove Import Reaction":
                self.keep_import_reactions = False
                self.use_topological_injections = False
            case "Topological Injection":
                self.keep_import_reactions = True
                self.use_topological_injections = True
            case "No Topological Injection":
                self.keep_import_reactions = True
                self.use_topological_injections = False

        if data["OPTIONS"]["ACCUMULATION"] == "Allowed":
            self.accumulation = True
        else:
            self.accumulation = False

        self.objectives = data["NETWORK"]["OBJECTIVE"]

        match data["NETWORK"]["SEARCH_MODE"]:
            case "Target":
                self.run_mode = "target"
            case "FBA":
                self.run_mode = "fba"
            case "Full network":
                self.run_mode = "full"
            case _ :
                self.run_mode =  data["NETWORK"]["SEARCH_MODE"]

        if data["OPTIONS"]["FLUX"] == "Maximization":
            maximize = True
        else:
            maximize = False

        match data["NETWORK"]["SOLVE"]:
            case "REASONING":
                solve = 'reasoning'
            case "HYBRID":
                solve = 'hybrid'
            case "REASONING GUESS-CHECK":
                solve = 'guess_check'
            case "REASONING GUESS-CHECK DIVERSITY":
                solve = 'guess_check_div'
            case "REASONING FILTER":
                solve = 'filter'
            case "ALL" | _:
                solve = 'all'
        
        for solver_type in data["RESULTS"]:
            for search_info in data["RESULTS"][solver_type]: 
                solver_type_transmetted = solver_type
                if data["NETWORK"]["SOLVE"] !="ALL":
                    if "REASONING" in solver_type:
                        solver_type_transmetted = data["NETWORK"]["SOLVE"]
                elif solver_type == "REASONING":
                    if "DIVERSITY" in search_info:
                        solver_type_transmetted = "REASONING GUESS-CHECK DIVERSITY"
                    elif 'GUESS-CHECK' in search_info:
                        solver_type_transmetted = "REASONING GUESS-CHECK"
                    elif 'FILTER' in search_info:
                        solver_type_transmetted = "REASONING FILTER"
                    
                if "solutions" in data["RESULTS"][solver_type][search_info]:
                    for solution in data["RESULTS"][solver_type][search_info]["solutions"]:
                        name = solution
                        size = data["RESULTS"][solver_type][search_info]["solutions"][solution][1]
                        seeds_list = data["RESULTS"][solver_type][search_info]["solutions"][solution][3]
                        obj_flux_lp = dict()
                        if solver_type == "FBA" or solver_type == "HYBRID":
                            for flux in data["RESULTS"][solver_type][search_info]["solutions"][solution][5]:
                                reaction = flux[0]
                                if reaction in self.objectives:
                                    obj_flux_lp[reaction] = flux[1]
                        self.add_result_seeds(solver_type_transmetted, search_info, name, size, seeds_list,
                                              obj_flux_lp)
        logger.log.info("... DONE")
        return maximize, solve

                   
    def write_cases_messages(self, tgt_message:str, obj_message:str, 
                             net_mess:list):
        """Write terminal messages depending on 
             - target file data for target mode
             - command line for full mode

        Args:
            tgt_message (str): The message to show for target
            obj_message (str): The message to show for objective
            net_mess ([str]): The message to show for network
        """
        print("\n____________________________________________\n")  
        print(f"TARGETS".center(44)) 
        print(f"FOR TARGET MODE AND FBA".center(44)) 
        print("____________________________________________\n") 
        logger.print_log(tgt_message, "info")

        print("\n____________________________________________\n")
        print(f"OBJECTVE".center(44)) 
        print(f"FOR HYBRID".center(44)) 
        print("____________________________________________\n") 
        logger.print_log(obj_message, "info")
        print("\n")


        print("\n____________________________________________\n")
        print(f"NETWORK".center(44)) 
        print("____________________________________________\n")
        logger.print_log(net_mess[0], "info")
        if self.keep_import_reactions:
            logger.print_log(net_mess[1], "info")
        if self.run_mode != "full":
            logger.print_log(net_mess[2], "info")
        if self.run_mode != "fba":
            logger.print_log(net_mess[3], "info")
        print("\n")



    def check_seeds(self, seeds:list):
        """Check flux into objective reaction for a set of seeds.

        Args:
            seeds (list): Set of seeds to test

        Returns:
            bool: Return if the objective reaction has flux (True) or not (False)
        """

        model = flux.get_model(self.file)
        flux.get_init(model, self.objectives, False)
        flux.stop_flux(model, self.objectives, False)

        result = Resmod(None, self.objectives, 
                        None, None, None, len(seeds), seeds, None, None)

        # This mode has to work with the seeds directly
        # that's whiy wi do not want to try "on demands" the flux
        result.check_flux(model, False)
        return result.OK, result.objective_flux_seeds


def print_flux(result:Resmod, maximize:bool):
    """Print fluxes data as a table

    Args:
        result (Resmod): Current result to write
        maximize (bool): Determine if Maximize option is used

    Returns:
        warning (bool): Is a warning has to be raised or not
    """
    warning=False
    if result.name != "model_one_solution":
        if result.OK_seeds:
            if (result.solver_type=="HYBRID" or result.solver_type=="FBA") \
            and  abs(result.chosen_lp - result.objective_flux_seeds) < 0.1:
                color_seeds = color_lp =color.green_light
            else:
                color_seeds = color_lp =color.cyan_light
                if (result.solver_type=="HYBRID" or result.solver_type=="FBA") \
                    and not maximize and abs(result.chosen_lp - result.objective_flux_seeds) > 0.1:
                    warning = True
        else:
            color_seeds=color.red_bright
        
        if result.OK_demands:
            if (result.solver_type=="HYBRID" or result.solver_type=="FBA") \
            and  abs(result.chosen_lp - result.objective_flux_seeds) < 0.1:
                color_demands=color.green_light
            else:
                color_demands=color.cyan_light
                if (result.solver_type=="HYBRID" or result.solver_type=="FBA") \
                    and not maximize and abs(result.chosen_lp - result.objective_flux_seeds) > 0.1:
                    warning = True
        elif not result.OK_seeds:
            color_demands=color.red_bright
        else:
            color_demands=color.reset
        concat_result = f"{result.name} | " 
        
        if not result.infeasible_seeds:
            concat_result += color_seeds + f"{result.objective_flux_seeds}" + color.reset + " | "  
        else:
            concat_result += f"Infeasible" + " | "  
        if not result.infeasible_demands:
            flux_demand = result.objective_flux_demands
            if flux_demand == None:
                flux_demand = "NA"

            concat_result += color_demands + f"{flux_demand}" + color.reset
        else:
            concat_result += f"Infeasible" 
        
        if result.solver_type=="HYBRID"  or result.solver_type=="FBA":
            lp_flux_rounded = round(result.chosen_lp,4)
            concat_result += " | " + color_lp + f"{lp_flux_rounded}" + color.reset
        print(concat_result)
    return warning