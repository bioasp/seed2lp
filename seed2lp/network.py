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
from .utils import quoted, prefix_id_network
from . import flux
from .resmod import Resmod
from time import time
from . import color
from . import logger
from .file import existant_path
import xml.etree.ElementTree as ET
import copy
from dataclasses import dataclass
from tqdm import tqdm
from concurrent.futures import as_completed

from concurrent.futures import ProcessPoolExecutor, as_completed

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

@dataclass
class NET_TITLE:
    CONVERT_TITLE_SOLVE={"REASONING":'reasoning',
                    "REASONING FILTER":'filter',
                    "REASONING GUESS-CHECK":'guess_check',
                    "REASONING GUESS-CHECK DIVERSITY":'guess_check_div',
                    "HYBRID":'hybrid',
                    "ALL":'all'}
    
    CONVERT_TITLE_MODE={"Target":'target',
                    "Full network":'full',
                    "FBA":'fba',
                    "Community Global":'global',
                    "Community Bisteps":'bisteps',
                    "Community delete superset":'delsupset'}

###################################################################
########################## Class NetBase ########################## 
###################################################################
class NetBase:
    def __init__(self, targets_as_seeds:bool=False, use_topological_injections:bool=False, 
                 keep_import_reactions:bool=True, accumulation:bool=False, equality_flux:bool=False):
        """Initialize Object NetBase

        Args:
            targets_as_seeds (bool): Targets can't be seeds and are noted as forbidden
            use_topological_injections (bool): Metabolite of import reaction are seeds
            keep_import_reactions (bool): Import reactions are not removed
            accumulation (bool, optional): Is accumulation authorized. Defaults to False.
        """
        self.targets_as_seeds = targets_as_seeds
        self.use_topological_injections = use_topological_injections
        self.keep_import_reactions = keep_import_reactions
        self.reactions = list()
        self.model=dict()
        # list of reaction having reactants and products switched
        self.switched_meta_reactions = dict()
        # list of reaction having the reversibility changed
        self.reversible_modified_reactions = dict()
        # list of reaction deleted because boudaries [0,0]
        self.deleted_reactions = dict()
        # list of exchange reaction
        self.exchanged_reactions = dict()
        
        self.fbc=dict()
        self.parameters = dict()
        self.objectives = list()
        self.objectives_reaction_name = list()
        self.is_objective_error = False
        self.targets=dict()
        self.seeds = list()
        self.possible_seeds = list()
        self.is_subseed = False
        self.forbidden_seeds = list()
        self.facts = ""
        self.meta_exchange_list = list()
        self.meta_transport_list = list()
        self.meta_other_list = list()
        # metabolite of import reaction having multiple metabolite such as None -> A+B
        self.meta_multiple_import_list = list()
        self.accumulation = accumulation

        self.instance_file=str()

        self.result_seeds=list()
        self.fluxes = pd.DataFrame()

        self.is_community=False
        self.species=list()

        # dictionnary of used metabolites containing list of reactions where
        # they are used
        self.used_meta = dict()

        self.equality_flux=equality_flux

    ######################## GETTER ########################
    def _get_reactions(self):
        return self.reactions
    

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

    def get_objective_reactant(self, ojective_name:str, species:str):
        """Get the objective reactants from SBML file
        """
        logger.log.info("Finding list of reactants from opbjective reaction...")
        reactants = SBML.get_listOfReactants_from_name(self.model[species], ojective_name)
        for reactant in reactants:
            react_name = prefixed_name = reactant.attrib.get('species')
            prefixed_name = prefix_id_network(self.is_community, react_name, species, "metabolite")

            if react_name not in self.targets:
                self.targets[react_name] = [prefixed_name]
            else:
                self.targets[react_name].append(prefixed_name)
        logger.log.info("... DONE") 


    def get_boundaries(self, reaction, species:str):
        """Get Boundaries of a reaction

        Args:
            reaction (etree line): Reaction from etree package

        Returns:
            lbound (float), ubound (float): lower and uppper boundaries value
        """
        lower_bound = self.parameters[species][reaction.attrib.get('{'+self.fbc[species]+'}lowerFluxBound')] \
                    if type(reaction.attrib.get('{'+self.fbc[species]+'}lowerFluxBound')) is not float \
                    else '"'+reaction.attrib.get('{'+self.fbc[species]+'}lowerFluxBound')+'"'
        lbound = round(float(lower_bound),10)
        upper_bound = self.parameters[species][reaction.attrib.get('{'+self.fbc[species]+'}upperFluxBound')] \
                    if type(reaction.attrib.get('{'+self.fbc[species]+'}upperFluxBound')) is not float \
                    else '"'+reaction.attrib.get('{'+self.fbc[species]+'}upperFluxBound')+'"'
        ubound = round(float(upper_bound),10)
        return lbound, ubound


    def find_objectives(self, input_dict:dict, species:str=""):
        """Find the objective reaction from SBML file
        If mode Target and no target set : put reactant of objective
        as targets

        Args:
            input_dict (dict): Constructed dictionnary of inputs

        Raises:
            ValueError: Multiple objective reaction with coefficient 1 found
            ValueError: No objective reaction found or none has coefficient 1
        """
        objectives = SBML.get_listOfFluxObjectives(self.model[species], self.fbc[species])
        
        obj_found_name = None
        is_reactant_found = False
        for obj in objectives:
            coef=float(obj[1])
            if obj_found_name is None:
                #For now works with only one objective
                if coef == 1:
                    obj_found_name = obj[0]
                    reaction = obj[2]
                    lbound, ubound = self.get_boundaries(reaction, species)
            # multiple objectives found with coefficient 1
            else:
                if coef == 1:
                    objectives = None
                    obj_found_name = None
                    self.is_objective_error = True
                    raise ValueError(f"Multiple objective reaction with coefficient 1 found\n")

        if not obj_found_name:
            self.is_objective_error = True
            raise ValueError(f"No objective reaction found or none has coefficient 1\n")
        else:
            logger.print_log(f'Objective found for {species}: {color.bold}{obj_found_name}{color.reset}', "info")
            if lbound == 0 and ubound == 0:
                self.is_objective_error = True
                raise ValueError(f"Lower and upper boundaries are [0,0] \nfor objetive reaction {obj_found_name}\n")
            obj_found_id = prefix_id_network(self.is_community, obj_found_name, species, "reaction")
            self.objectives.append([species, obj_found_id])
            self.objectives_reaction_name.append(obj_found_id)
            if (self.run_mode == "target" or self.run_mode == "fba" or self.run_mode == "community")\
              and ('Targets' not in input_dict or not input_dict["Targets"]):
                if not self.is_community:
                    species = self.name
                self.get_objective_reactant(obj_found_name, species)
                is_reactant_found = True
        return is_reactant_found


    def check_objectives(self, input_dict:dict):
        """Check if objectives reaction is given by user

        Args:
            input_dict (dict): The input dictionnary

        Returns:
            bool: Boolean determining if objectives is given by user
        """
        is_user_objective = False
        if input_dict and "Objective" in input_dict and input_dict["Objective"]:
            self.objectives = input_dict["Objective"]
            is_user_objective = True
        return is_user_objective
    

    def init_with_inputs(self, input_dict:dict, is_reactant_found:bool, objective_error:bool,
                         is_user_objective:bool):
        """Initiate Networks with inputs given by user and arguments. Find objectives reaction
        if not given by user. Show messages on termminal about the Network.

        Args:
            input_dict (dict): The input dictionnary
            is_reactant_found (bool): Define if the reactant are found in sbml or given by user as targets (all modes except Full Network mode)
            objective_error (bool): Define if the objective reaction was in error (not found) to write the corresponding warning message
        """
        tgt_message = ""

        match self.run_mode:
            case "target" | "community":
                tgt_message = "Targets set:\n"
            case "target" | "fba":
                tgt_message = "Targets detected for option \"target as seeds\":\n"
            case _:
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
            if is_user_objective:
                if self.run_mode == "target":
                    obj_message += "-    Objective reaction from target file\n"
                else:
                    obj_message += "-    Objective reaction from command line\n"
                suff_plurial=""
                if len(self.objectives) > 1:
                    suff_plurial = "s"
                # Reactant of objective set as target on target mode
                # No needed on full mode (all metabolite are set as target)
                if self.run_mode != "full":
                    for obj in self.objectives:
                        if self.is_community:
                            species=obj[0]
                        else:
                            species = self.name
                        self.get_objective_reactant(ojective_name=obj[1], species=species)
                        obj[1]=prefix_id_network(self.is_community, obj[1], obj[0], "reaction")
                        self.objectives_reaction_name.append(obj[1])
                    obj_string = " | ".join([str(item[1]) for item in self.objectives])
                    obj_message += f'        Objective{suff_plurial} : {obj_string}'
                    tgt_message +=  "    Reactant of objective reaction\n    from target file\n"
                else:
                    obj_string = " | ".join([str(item[1]) for item in self.objectives])
                    obj_message += f'\n        Objective{suff_plurial} : {obj_string}'

        # Find objective into sbml file if not given by user      
        if not is_user_objective:
            if not objective_error :
                obj_message += "-    Objective reaction from SBML file"
                suff_plurial=""
                if len(self.objectives) > 1:
                    suff_plurial = "s"
                obj_string = " | ".join([str(item[1]) for item in self.objectives])
                obj_message += f'\n        Objective{suff_plurial} : {obj_string}'
                if self.run_mode != "full" \
                  and is_reactant_found:
                    tgt_message +=  "    Reactant of objective reaction\n    from SBML file\n"
            else:
                if self.run_mode == "target" \
                  and (self.targets is None or not self.targets):
                    tgt_message += "    No target found"
                obj_message += "    No objective reaction found"
        else:
            if len(self.objectives)<len(self.species):
                obj_message += "\n\n-    Objective reaction from SBML file"
                suff_plurial = "s"
                obj_found_string = ""
                added_species = set()
                for species in self.species:
                    if species not in [obj[0] for obj in self.objectives]:
                        added_species.add(species)
                        is_reactant_found = self.find_objectives(input_dict, species)
                for item in self.objectives:
                    if item[0] in added_species:
                        obj_found_string = obj_found_string + item[1] + " | " 
                        self.objectives_reaction_name.append(item[1])
                obj_found_string = obj_found_string.removesuffix(" | ")
                obj_message += f'\n        Objective{suff_plurial} : {obj_found_string}'
            
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


    # def prefix_id_network(self, name:str, species:str="", type_element:str=""):
    #     """Prefix Reaction or Metbolite by the network name (filename) if the tool is used for community.
    #     For single network, nothing is prefixed.

    #     Args:
    #         name (str): ID of the element
    #         species (str, optional): Network name (from filename). Defaults to "".
    #         type_element: (str, optional): "reaction" or "metabolite" or no type. Defaults to "".

    #     Returns:
    #         str: The name prfixed by the network if needed
    #     """
    #     match self.is_community, type_element:
    #         case True,"reaction":
    #             return sub("^R_", f"R_{species}_",name)
    #         case True,"metabolite":
    #             return sub("^M_", f"M_{species}_",name)
    #         case True,"metaid":
    #             return sub("^meta_R_", f"meta_R_{species}_",name)
    #         case True,_:
    #             return f"{species}_{name}"
    #         case _,_:
    #             return name


    def get_network(self, species:str, to_print:bool=True, 
                    write_sbml:bool=False):
        """Get the description of the Network from SBML file
        Construct list of reactants and products
        Correct the reversibility based on boundaries
        For import or export reaction, if reversibilité is corrected
        correct also reactants and products by exchanging them
        When writing SBML, delete Import reaction

        Args:
            species (str): Network name (from filename)
            to_print (bool, optional): Print messages on terminal. Defaults to True.
            write_sbml (bool, optional): Is a writing SBML file mode or not. Defaults to False.
        """
        reactions_list = SBML.get_listOfReactions(self.model[species])
        if self.is_community:
            warning_message = f"{species}"
        else:
            warning_message = ""

        info_message = ""

        for r in reactions_list:
            reaction_id= r.attrib.get("id")
            if self.is_community:
                reaction_id = prefix_id_network(self.is_community, reaction_id, species, "reaction")
            reaction = Reaction(reaction_id, species=species)
            reaction.is_exchange=False
            source_reversible = False if r.attrib.get('reversible') == 'false' else True           
            # Treating reverserbility separately, lower bound can stay to 0
            reaction.lbound, reaction.ubound = self.get_boundaries(r,species)

            # delete prefix species on name for community mode
            if self.is_community:
                reaction_origin_name = reaction.name.replace(f"_{species}", "")
            else:
                reaction_origin_name = reaction.name

            # If the reaction can never have flux, meaning lower_bound = 0 and upper_bound = 0
            # The reaction is deleted from the network
            if reaction.lbound == 0 and reaction.ubound == 0:
                self.deleted_reactions[reaction.name] = len(self.reactions)
                warning_message += f"\n - {reaction_origin_name}: Deleted.\n     Boundaries was: [{reaction.lbound} ; {reaction.ubound}]"
                # Not added not reaction list of the network
                continue

            reactants, list_react_names = SBML.get_listOfReactants(r,species,self.is_community)
            products, list_product_names = SBML.get_listOfProducts(r,species,self.is_community)
            # uses the definition of boundaries as cobra
            # a reaction is in boundaries (so exchange reaction)
            # when a reaction has only one metabolite and 
            # does not have reactants or products
            if not (reactants and products):
                if (reactants and len(reactants) == 1) \
                    or (products and len(products) == 1):
                    # Cobra definition of exchange reaction
                    reaction.is_exchange=True
                    self.exchanged_reactions[reaction.name] = len(self.reactions) 
                elif not reactants and not products:
                    # Reaction with boundaries [0,0] is deleted on the network for reasoning part.
                    # But it is not deleted on sbml file when rewritten (command network option rewrite file).
                    warning_message += f"\n - {reaction_origin_name} deleted. No reactants and no products."
                    continue
                else:
                    self.exchanged_reactions[reaction.name] = len(self.reactions) 
                    # A reaction is multiple exchange
                    # when None -> A + B || A + B -> None || None <-> A + B || A + B <-> None
                    warning_message += f" - {reaction_origin_name} is multiple (more than 1) metabolites import/export reaction. "
                    if not self.keep_import_reactions:
                        warning_message += "\n\tDeleted as it is an import reaction."
                    else:
                        warning_message += "\n"

            # Check if transport reactions
            # The same metabolites are involved in both reactants and products to be defined as Transport
            # The list contains only the name of metabolite without the compartiment
            # both list must be the same 
            if set(list_react_names) == set(list_product_names):
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
                    if "- R_" not in warning_message:
                        warning_message +="\n"
                    warning_message += f"\n - {reaction_origin_name}: Reactants and products switched.\n     Boundaries was: [{reaction.lbound} ; {reaction.ubound}]"
                    meta = products
                    products = reactants
                    reactants = meta
                    reaction.is_meta_modified = True
                    # Index of reaction needed for network rewriting
                    self.switched_meta_reactions[reaction.name] = len(self.reactions)

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
            self.meta_exchange_list, self.meta_transport_list, self.used_meta = reaction.add_metabolites_from_list(reactants,"reactant", 
                                                                self.meta_exchange_list, self.meta_transport_list, self.used_meta)
            
            self.meta_exchange_list, self.meta_transport_list, self.used_meta = reaction.add_metabolites_from_list(products,"product", 
                                                                self.meta_exchange_list, self.meta_transport_list, self.used_meta) 
            
            if reaction.is_exchange and not self.keep_import_reactions:
                # We already review the order of reaction and product regarding boudaries
                # there is some cases to take into account : 
                # None <-> P [-1000, 1000] : reactant and product has to be exchanged to then put lbound to 0 and transform it into export only 
                # R <-> None [-1000, 1000] : lbound set to 0 and it will become an export only
                # None -> P [0,1000] : Is an import only reaction and has to be deleted 
                # R -> None [0,1000] : OK no modifications
                if products and not reactants:
                    if reaction.lbound >= 0:
                        # Index of reaction needed for network rewriting
                        self.deleted_reactions[reaction.name] = len(self.reactions)
                        warning_message += f"\n - {reaction_origin_name}: Deleted.\n     Not reversible import reaction."
                    else:
                        reaction.is_meta_modified = True
                        meta = products
                        products = reactants
                        reactants = meta
                        # Index of reaction needed for network rewriting
                        self.switched_meta_reactions[reaction.name] = len(self.reactions)
                        warning_message += f"\n - {reaction_origin_name}: Reactants and products switched.\n     Exchanged reaction became export only."
                # The reaction is no more reversible
                reaction.reversible = False
                reaction.has_rm_prefix = True
            
            reaction.is_reversible_modified = source_reversible != reaction.reversible

            if reaction.is_reversible_modified:
                # Index of reaction needed for network rewriting
                self.reversible_modified_reactions[reaction.name] = len(self.reactions)
                info_message += f"\n - {reaction.name}: Reversibility modified."
            self.add_reaction(reaction)

        # Because of the order of reaction, the metabolites can be found as exchanged
        # after another reaction, it is needed to correct that
        for reaction in self.reactions:
            self.review_tag_metabolite(reaction.is_transport , reaction.products, reaction.reactants)
            self.review_tag_metabolite(reaction.is_transport , reaction.reactants, reaction.products)

            if  write_sbml and reaction.is_exchange and not self.keep_import_reactions:
                self.update_network_sbml(reaction)

        if (to_print):
            if warning_message :
                if not self.is_community or ( self.is_community and warning_message != species):
                    warning_message += "\n"
                    logger.log.warning(warning_message)
            if info_message:
                logger.log.info(info_message)
        else:
            logger.log.info(warning_message)
            logger.log.info(info_message)
            print("____________________________________________\n")


    def review_tag_metabolite(self, is_transport:bool , meta_list:list, meta_list_opposite:list):
        """Review all metabolite tag that can be not well tagues because of the order of reaction writen into source SBML fil
        Indeed the metabolites can be found as exchanged later, the previous reaction needs to tag the metabolite as exchanged too.
        Also corrects the transport tag, change it into "other" tag when a metabolite is only involve in one reaction (the transport reaction)

        Args:
            reaction (Reaction): object Reaction
            meta_list (list): List of metabolite (reactants or products)
            meta_list_opposite (list): list of opposite metabolite(products or reactants respectively to previous list)
        """
        for metabolite in meta_list:
            if metabolite.id_meta in self.meta_exchange_list and not metabolite.type == "exchange":
                metabolite.type = "exchange"
            if metabolite.id_meta in self.meta_transport_list and not metabolite.type == "transport":
                metabolite.type = "transport"
            # In this case, we can have some metabolite that are all tagged transport and none of them will be used 
            # as seed on asp. We need to find the node that doesn't have any parent (no reaction incoming or outgoing)
            # This also means that a metabolite is only involved in one reaction (one transport reaction only)
            # Example : 
            # R1: C_m <-> C_c  |  R2: C_g <-> C_c  |  R3: C_e  <->  C_g  |   R4: C_m + A <-> B
            # Here C_e is involved in only 1 tranport reaction R3, there is no exchange reaction, it will be
            # tagged other while the other will be taggued exchange
            # used_meta is a dictionnary with all metabolite used in key, and having a list of reation where thy are involved
            # as a value. 
            # We need to check this only for transport reaction
            if is_transport and metabolite.type == "transport" and len(self.used_meta[metabolite.id_meta])==1:
                # Before changing the value, we have to check ih the other metabolite is also a transport.
                # There is no need to untaged both of them as transport.
                # When the reaction is a trasport reaction, there is only one metabolite involved in reactant
                # and product as defined in get_network() function
                if meta_list_opposite[0].type == "transport":
                    metabolite.type = "other"
                    self.meta_transport_list.remove(metabolite.id_meta)


    def convert_to_facts(self):
        """Convert the corrected Network into ASP facts
        """
        logger.log.info("Converting Network into ASP facts ...")
        facts = ""
        # Upper bound does not change on forward reaction
        
        for reaction in self.reactions:
            facts += reaction.convert_to_facts(self.keep_import_reactions, 
                                                  self.use_topological_injections)
                

        for objective in self.objectives_reaction_name:
            facts += '\nobjective("'+objective+'").'
        for seed in self.seeds:
            facts += f'\nseed_user({quoted(seed)}).' 
        for target in self.targets:
            for metabolite in self.targets[target]:
                facts += f'\ntarget({quoted(target)},{quoted(metabolite)}).'
        for forbidden in self.forbidden_seeds:
            facts += f'\nforbidden({quoted(forbidden)}).'
        for possible in self.possible_seeds:
            facts += f'\np_seed({quoted(possible)}).'

        self.facts = facts
        logger.log.info("... DONE")


    def simplify(self):
        """Lighten the Network Object, only facts needed
        """
        self.sbml = None
        self.reactions = None
        self.seeds = None
        self.forbidden_seeds = None

    
    def add_result_seeds(self, solver_type:str, search_info:str, model_name:str, 
                         size:int, seeds:list, flux_lp:dict=None, flux_cobra:dict=None,
                         transferred_list:list=None):
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
        result = Resmod(model_name, self.objectives_reaction_name, solver_type, search_mode, search_type, 
                        size, seeds, flux_lp, flux_cobra, self.run_mode, self.accumulation,
                        self.is_community, transferred_list)
        result_seeds_list.append(result)
        self._set_result_seeds(result_seeds_list)


    def format_flux_result(self, result:Resmod, fluxes_init:dict, fluxes_no_import:dict=None):
        """Formating Result data (Resmod object) with Network data and flux check
        Args:
            result (Resmod): Result (Object Resmod)
            fluxes_init (dict): Dictionnary of initial fluxes for each objectives
            fluxes_no_import (dict): Dictionnary of fluxes for each objectives after "shuttig down" import reaction

        Returns:
            list, Resmod, dict, dict: objective, result, flux_no_import, flux_init
        """
        if self.keep_import_reactions:
            flux_no_import = None
        else:
            flux_no_import = fluxes_no_import

        if self.is_community:
            objective = self.objectives_reaction_name
            flux_init = fluxes_init
            
        else:
            objective = result.tested_objective
            flux_init = fluxes_init[objective]
            flux_no_import = fluxes_no_import[objective]
            result.objective_flux_seeds=result.objective_flux_seeds[objective]
            if result.objective_flux_demands:
                result.objective_flux_demands=result.objective_flux_demands[objective]
            else:
                result.objective_flux_demands=None
        return objective, result, flux_no_import, flux_init
    

    
    def check_fluxes(self, maximize:bool, max_workers:int=-1):
        """Calculate the flux using Cobra and get the flux from lp for all solutions (set of seed).
        Store information and data into dataframe

        Args:
            maximize (bool): Determine if Maximize option is used
        """
        if self.is_community:
            dtypes = {'species':'str',
                    'biomass_reaction':'str',
                    'solver_type':'str',
                    'search_mode':'str',
                    'search_type':'str',
                    'accumulation':'str',
                    'model':'str',
                    'size':'int',
                    'lp_flux':'float',
                    'cobra_flux_init':'str',
                    'cobra_flux_no_import':'str',
                    'cobra_flux_seeds':'str',
                    'cobra_flux_demands':'str',
                    'has_flux':'str',
                    'has_flux_seeds':'str',
                    'has_flux_demands':'str',
                    'timer':'float'
                    }
        else :
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
            
        fluxes_no_import=None
            
        fluxes = pd.DataFrame(columns=['species','biomass_reaction', 'solver_type', 'search_mode', 'search_type',
                                       'accumulation', 'model', 'size', 'lp_flux', 'cobra_flux_init', 'cobra_flux_no_import',
                                       'cobra_flux_seeds', 'cobra_flux_demands', 'has_flux','has_flux_seeds',
                                       'has_flux_demands', 'timer'])
        fluxes = fluxes.astype(dtypes)
        
        if self.objectives_reaction_name:
            if self.result_seeds:
                logger.log.info("Check fluxes Starting")
                model = flux.get_model(self.file)
                fluxes_init = flux.get_init(model, self.objectives_reaction_name)
                if not self.keep_import_reactions:
                    fluxes_no_import = flux.stop_flux(model, self.objectives_reaction_name)
                self.model[self.name] = model
                print(color.purple+"\n____________________________________________")
                print("____________________________________________\n"+color.reset)
                print("RESULTS".center(44))
                print(color.purple+"____________________________________________")
                print("____________________________________________\n"+color.reset)

                logger.log.warning("Processing in parallel. " \
                "\nNo outputs will be shown. " \
                "\nPlease wait ...\n")

                prev_solver_type=None
                prev_search_mode=None
                has_warning=False
    
                # ProcessPoolExecutor is used to run the function in parallel
                if max_workers != -1:
                    # If max_workers is set to 0, it will use the default number of workers
                    if max_workers == 0:
                        max_workers=None
                    with ProcessPoolExecutor(max_workers=max_workers) as executor:
                        futures = []
                        for result in self.result_seeds:
                            futures.append(executor.submit(
                                process_result,
                                result,
                                self.model[self.name],
                                self.name,
                                self.equality_flux,
                                fluxes_init,
                                fluxes_no_import,
                                maximize,
                                dtypes,
                                self.accumulation,
                                self.is_community,
                                self.keep_import_reactions,
                                objectives=self.objectives_reaction_name
                            ))

                        prev_solver_type = None
                        prev_search_mode = None
                        has_warning = False
                        
                    # Add tqdm progress bar for completed futures
                    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing results"):
                        for future in as_completed(futures):
                            result_flux, solver_type, search_mode, warn = future.result()
                            # Check if the search mode has changed
                            if prev_search_mode == None or result.search_mode != prev_search_mode:
                                if has_warning:
                                    logger.log.warning(WARNING_MESSAGE_LP_COBRA)
                                prev_search_mode = search_mode
                                prev_solver_type = None
                            if prev_solver_type != solver_type:
                                prev_solver_type = solver_type
                            
                            if warn:
                                has_warning = True
                            # Add result to DataFrame
                            fluxes = pd.concat([fluxes, result_flux], ignore_index=True)

                        if has_warning:
                            logger.log.warning(WARNING_MESSAGE_LP_COBRA)
                else:
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
                        result.check_flux(self.model[self.name], equality_flux=self.equality_flux)

                        objective, result, flux_no_import, flux_init = self.format_flux_result(result, fluxes_init, fluxes_no_import)

                        warn = print_flux(result, maximize, self.is_community)
                        if warn:
                            has_warning=True
                    

                        flux_time = time() - flux_time
                        flux_time=round(flux_time, 3)
                        
                        result_flux =  pd.DataFrame([[self.name, objective, result.solver_type, result.search_mode,
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

        self.objectives_reaction_name = data["NETWORK"]["OBJECTIVE"]
 
        if data["NETWORK"]["SEARCH_MODE"] in NET_TITLE.CONVERT_TITLE_MODE:
            self.run_mode = NET_TITLE.CONVERT_TITLE_MODE[data["NETWORK"]["SEARCH_MODE"]]
        else:
            self.run_mode = data["NETWORK"]["SEARCH_MODE"]
        

        if data["OPTIONS"]["FLUX"] == "Maximization":
            maximize = True
        else:
            maximize = False

        if data["NETWORK"]["SOLVE"] in NET_TITLE.CONVERT_TITLE_SOLVE:
            solve = NET_TITLE.CONVERT_TITLE_SOLVE[data["NETWORK"]["SOLVE"]]
        else:
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
                                if reaction in self.objectives_reaction_name:
                                    obj_flux_lp[reaction] = flux[1]
                        if self.is_community:
                            transferred_list = data["RESULTS"][solver_type][search_info]["solutions"][solution][5]
                        else: 
                            transferred_list = None
                        self.add_result_seeds(solver_type_transmetted, search_info, name, size, seeds_list,
                                              obj_flux_lp, transferred_list=transferred_list)
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



    def check_seeds(self, seeds:list, transferred:list=None):
        """Check flux into objective reaction for a set of seeds.

        Args:
            seeds (list): Set of seeds to test

        Returns:
            bool: Return if the objective reaction has flux (True) or not (False)
        """
        model = flux.get_model(self.file)
        flux.get_init(model, self.objectives_reaction_name, False)
        flux.stop_flux(model, self.objectives_reaction_name, False)

        result = Resmod(None, self.objectives_reaction_name, 
                        None, None, None, len(seeds), seeds, None, None, 
                        is_community=self.is_community, transferred_list=transferred)

        # This mode has to work with the seeds directly
        # that's whiy wi do not want to try "on demands" the flux
        result.check_flux(model, False, self.equality_flux)
        return result.OK, result.objective_flux_seeds
    

    def update_network_sbml(self, reaction:Reaction):
        """When writing SBML, we need to update the Network object, more precisely the Reaction object 
        and change the boundaries as they are not needed for Hybrid-lpx.
        This is important to keep the mboudary for sigle network using Hybrid-lpx.
        For community, there is no Hybrid-lpx mode therefore i is not important to keep the boundaries,
        but we need a written sbml version for all Hybrid-Cobra modes (Filter, Guess-Check, Guess-Check Diversity)

        Args:
            reaction (Reaction): _description_.
        """
        if len(reaction.reactants) == 0:
            reaction.ubound=0
            # Upper bound can't be lower than lower bound
            if reaction.lbound > 0:
                reaction.lbound = 0
        if len(reaction.products) == 0:
            reaction.lbound=0
            # Lower bound can't be upper than upper bound
            if reaction.ubound < 0:
                reaction.ubound = 0

        
    def print_flux(self, result:Resmod, maximize:bool):
        """Print fluxes data as a table

        Args:
            result (Resmod): Current result to write
            maximize (bool): Determine if Maximize option is used

        Returns:
            warning (bool): Is a warning has to be raised or not. Only used for Hybrid-lpx mode
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
            
            
            concat_result = f"{result.name} | " 

            if not result.infeasible_seeds:
                if self.is_community:
                    concat_result=add_print_seed_community(result, color_seeds, concat_result, result.infeasible_seeds)
                        
                else:
                    concat_result += color_seeds + f"{result.objective_flux_seeds}" + color.reset + " | " 
                    warning, concat_result = add_print_demands(result, maximize, warning, concat_result) 
            else:
                concat_result += f"Infeasible" + " | " 
                if self.is_community:
                    concat_result=add_print_seed_community(result, color_seeds, concat_result, result.infeasible_seeds)
                else:
                    warning, concat_result = add_print_demands(result, maximize, warning, concat_result) 
            
            
            if result.solver_type=="HYBRID"  or result.solver_type=="FBA":
                lp_flux_rounded = round(result.chosen_lp,4)
                concat_result += " | " + color_lp + f"{lp_flux_rounded}" + color.reset
            print(concat_result)
        return warning
    

    
    

    def sbml_remove_reaction(self, reaction:ET.Element, species:str):
        """Remove reaction node into the model when defines by the normalisation as needed to be deleted
        and then remove the reaction from objective reaction list node.
        The objective list deletion is needed to get a Cobra valid file.

        Args:
            reaction (ET.Element): Etree element (node) to delete
            species (str): Network to apply the deletion
        """        
        SBML.remove_reaction(self.model[species], reaction)
        SBML.check_remove_objective(self.model[species], reaction, self.fbc[species])

    

    def sbml_review_reversibilty(self, reaction_name:str, reaction:ET.Element):
        """Review the reaction reversibility attribute of reaction node when defined by the normalisation as needed to be modified.

        Args:
            reaction_name (str): Reaction ID that needs to by modified
            reaction (ET.Element): Etree element (node) to modify

        Returns:
            bool: define if the reaction has been modified
        """
        is_modif_rev = False
        if reaction_name in self.reversible_modified_reactions:
            index = self.reversible_modified_reactions[reaction_name]
            reaction.attrib["reversible"] = str(self.reactions[index].reversible).lower()
            is_modif_rev = True
        return is_modif_rev
    

    def sbml_switch_meta(self, reaction_name:str, reaction:ET.Element, species:str):
        """Switch reactant and products for a reaction node when defined by the normalisation as needed to be switch.

        Args:
            reaction_name (str): Reaction ID that needs to by modified
            reaction (ET.Element):  Etree element (node) to modify
            species (str):  Network to apply the switch

        Returns:
            bool: define if the reaction has been modified
        """
        # Exchange list of reactants and product if they are tagged as modified
        # The modification tag is only on exchanging reactants and products
        # Reaction written backward will be wrote forward
        is_switch_meta=False
        if reaction_name in self.switched_meta_reactions:
            index = self.switched_meta_reactions[reaction_name]
            has_reactant=False
            has_product=False
            reactants=list()
            products=list()
            # loop into source
            for element in reaction:
                # copy and remove list of reactant and products from source
                if SBML.get_sbml_tag(element) == "listOfReactants":
                    reactants = copy.copy(element)
                    has_reactant = True
                    SBML.remove_sub_elements(element)
                elif SBML.get_sbml_tag(element) == "listOfProducts":
                    products = copy.copy(element)
                    has_product=True
                    SBML.remove_sub_elements(element)

            # add the new element into source node 
            # put products into reactant and reactant into products
            recreate_other_node=True
            for element in reaction:
                if SBML.get_sbml_tag(element) == "listOfReactants":
                    #check if node listOfProducts exist and copy element
                    if has_product:
                        SBML.add_metabolites(element, products)
                    elif recreate_other_node:
                        # the node listOfProducts doesnt exist it needs to be created
                        SBML.create_sub_element(reaction, "listOfProducts")
                        #copy the element of reactant (exchanging reactant and products)
                        SBML.add_metabolites(element, reactants)
                        recreate_other_node=False
                        SBML.remove_sub_elements(element)
                elif SBML.get_sbml_tag(element) == "listOfProducts" and has_reactant:
                    if has_reactant:
                        SBML.add_metabolites(element, reactants)
                    elif recreate_other_node:
                        SBML.create_sub_element(reaction, "listOfReactants")
                        SBML.add_metabolites(element, products)
                        recreate_other_node=False
                        SBML.remove_sub_elements(element)
            # Modify boundaries
            if self.parameters[species]:
                self.parameters[species][f'{reaction_name}_lower_bound'] = self.reactions[index].lbound
                self.parameters[species][f'{reaction_name}_upper_bound'] = self.reactions[index].ubound
                reaction.attrib['{'+self.fbc[species]+'}lowerFluxBound']= f'{reaction_name}_lower_bound'
                reaction.attrib['{'+self.fbc[species]+'}upperFluxBound']= f'{reaction_name}_upper_bound'
            else:
                reaction.attrib['{'+self.fbc[species]+'}lowerFluxBound']= self.reactions[index].lbound
                reaction.attrib['{'+self.fbc[species]+'}upperFluxBound']= self.reactions[index].ubound

            is_switch_meta = True
        return is_switch_meta
    

    def sbml_remove_import(self, reaction_name:str, reaction:ET.Element, species:str):
        """Remove the import direction of exchanged reaction by changing boundaries or the reaction node.
        During the process, new parameters are created for the boundaries that are changed.

        Args:
            reaction_name (str): Reaction ID that needs to by modified
            reaction (ET.Element):  Etree element (node) to modify
            species (str):  Network to apply the import reaction deletion

        Returns:
            bool: define if the import direction reaction has been modified
        """
        is_rm_import=False
        if reaction_name in self.exchanged_reactions:
            index = self.exchanged_reactions[reaction_name]
            self.parameters[species][f'{reaction_name}_lower_bound'] = self.reactions[index].lbound
            self.parameters[species][f'{reaction_name}_upper_bound'] = self.reactions[index].ubound
            reaction.attrib['{'+self.fbc[species]+'}lowerFluxBound']= f'{reaction_name}_lower_bound'
            reaction.attrib['{'+self.fbc[species]+'}upperFluxBound']= f'{reaction_name}_upper_bound'
            is_rm_import = True
        return is_rm_import
    

    def sbml_review_parameters(self, species:str):
        """While modifing boudaries for import reaction, new parameters has been created and needs to be added
        into the sbml file

        Args:
            species (str): Network to add the created parameters
        """
        # Replace list of parameters because we added new specific parameters for the exchange reactions
        parameters_copy = copy.copy(self.parameters[species])

        for el in self.model[species]:
            tag = SBML.get_sbml_tag(el)
            if tag == "listOfParameters":
                node = copy.deepcopy(el[0])
                for param in el:
                    id = param.attrib.get('id')
                    # Corrects the already existant parameters 
                    if id in parameters_copy:
                        param.attrib['value'] = str(parameters_copy[id])
                        # delete the existant parameter from the list of parameter to keep
                        # only the new parameters
                        parameters_copy.pop(id)
                # create new paramaters node
                for key, value in parameters_copy.items():
                    new_node = copy.deepcopy(node)
                    new_node.attrib['id'] = key
                    new_node.attrib['value'] = str(value)
                    el.append(new_node)

################################################################### 



###################################################################
################## Class NetCom : herit NetBase ################### 
###################################################################

class Network(NetBase):
    def __init__(self, file:str, run_mode:str=None, targets_as_seeds:bool=False, use_topological_injections:bool=False, 
                 keep_import_reactions:bool=True, input_dict:dict=None, accumulation:bool=False, to_print:bool=True, 
                 write_sbml:bool=False):
        """Initialize Object Network

        Args:
            file (str): SBML source file
            run_mode (str, optional):  Running command used (full or target or FBA). Defaults to None.
            targets_as_seeds (bool, optional): Targets can't be seeds and are noted as forbidden. Defaults to False.
            use_topological_injections (bool, optional): Metabolite of import reaction are seeds. Defaults to False.
            keep_import_reactions (bool, optional): Import reactions are not removed. Defaults to True.
            input_dict (dict, optional): The input dictionnary. Defaults to None.
            accumulation (bool, optional): Is accumulation authorized. Defaults to False. Defaults to False.
            to_print (bool, optional): Write messages into console if True. Defaults to True.
            write_sbml (bool, optional):  Is a writing SBML file mode or not. Defaults to False.
        """

        super().__init__(targets_as_seeds, use_topological_injections, 
                 keep_import_reactions, accumulation)
        self.file = file
        self.run_mode = run_mode
        self.file_extension = ""
        self._set_file_extension(file)
        self._set_name()
        self.species=[self.name]
        self.sbml=dict()
        self.sbml[self.name], self.sbml_first_line, self.default_namespace = SBML.get_root(self.file)
        self.model[self.name] = SBML.get_model(self.sbml[self.name])
        self.fbc = {self.name: SBML.get_fbc(self.sbml[self.name])}
        self.parameters = {self.name: SBML.get_listOfParameters(self.model[self.name])}

        # Instatiate objectives from target file if given by user
        is_user_objective = self.check_objectives(input_dict)
        # Find objectives on sbml file is not given
        is_reactant_found=False
        is_objective_error=False
        
        logger.print_log("\nFinding objective ...", "info")
        if self.objectives is None or not self.objectives:
            try:
                is_reactant_found = self.find_objectives(input_dict, self.name)
                # for obj in self.objectives:
                #     self.objectives_reaction_name.append(obj[1])
            except ValueError as e:
                is_objective_error = True
                logger.log.error(str(e))
        # Init networks with data given by user and objective reaction
        # write messages
        if self.run_mode is not None:
            # write console messages
            self.init_with_inputs(input_dict, is_reactant_found, is_objective_error, is_user_objective)

        logger.print_log("Network normalisation in progress...", "info")
        logger.print_log("Can take several minutes", "info")
        normalisation_time = time()
        self.get_network(self.name, to_print, write_sbml)
        normalisation_time = time() - normalisation_time
        logger.print_log(f"Normalisation total time: {round(normalisation_time, 3)}s", "info")
        




###################################################################
################## Class NetCom : herit NetBase ################### 
###################################################################
class Netcom(NetBase):
    def __init__(self, comfile:str, sbmldir:str, temp_dir:str, run_mode:str=None, run_solve:str=None, community_mode:str=None,
                 targets_as_seeds:bool=False, use_topological_injections:bool=False, keep_import_reactions:bool=True, 
                 input_dict:dict=None, accumulation:bool=False, to_print:bool=True, 
                 write_sbml:bool=False, equality_flux:bool=False):
        """Initialise Object Netcom

        Args:
            comfile (str): Text file path containing the list of files describing the community
            sbmldir (str): The directory path containing all the sbml files
            temp_dir (str): Temporary directory path for saving the merged sbml file
            run_mode (str, optional):  Running command used (full or target or FBA). Defaults to None.
            targets_as_seeds (bool, optional):  Targets can't be seeds and are noted as forbidden. Defaults to False.
            use_topological_injections (bool, optional): Metabolite of import reaction are seeds. Defaults to False.
            keep_import_reactions (bool, optional): Import reactions are not removed. Defaults to True.
            input_dict (dict, optional): he input dictionnary. Defaults to None.
            accumulation (bool, optional):  Is accumulation authorized. Defaults to False.
            to_print (bool, optional): Write messages into console if True. Defaults to True.
            write_sbml (bool, optional):  Is a writing SBML file mode or not. Defaults to False.
        """
        super().__init__(targets_as_seeds, use_topological_injections, 
                        keep_import_reactions, accumulation, equality_flux)
        self.name=""
        self.comfile = comfile
        self.sbml_dir = sbmldir
        self.sbml=dict()
        self.files=list()
        self.run_mode = run_mode
        self.run_solve = run_solve
        self.community_mode = community_mode
        self.extension=str()
        self.is_community=True
        self._set_file_extension()
        self._set_name()
        self.temp_dir = temp_dir
        if targets_as_seeds:
            short_target_option="tas"
        else:
            short_target_option="taf"
        self.file = os.path.join(self.temp_dir, f"tmp_{self.name}_{self.community_mode}_{self.run_solve}_{short_target_option}.xml") 

        # get list of species from text file
        com_list_file = open(self.comfile, "r") 
        data = com_list_file.read() 
        self.species = data.split("\n")
        com_list_file.close()

        self.get_sbml_data()
        is_user_objective = self.check_objectives(input_dict)
        # Find objectives on sbml file is not given
        is_reactant_found=False
        is_objective_error=False
        logger.print_log("\n Finding objectives of community ...", "info")
        if self.objectives is None or not self.objectives:
            for species in self.species:
                try:
                    is_reactant_found = self.find_objectives(input_dict, species)
                except ValueError as e:
                    is_objective_error = True
                    logger.log.error(str(e))

        # Init networks with data given by user and objective reaction
        # write messages
        if self.run_mode is not None:
            # write console messages
            self.init_with_inputs(input_dict, is_reactant_found, is_objective_error, is_user_objective)

        logger.print_log("Network normalisation in progress ...", "info")
        normalisation_time = time()
        for species in self.species:
            self.get_network(species, to_print, write_sbml)

        self.write_merge_sbml_file()
        normalisation_time = time() - normalisation_time
        logger.print_log(f"Normalisation total time: {round(normalisation_time, 3)}s", "info")
        

 
    ########################################################


    ######################## SETTER ########################
    def _set_name(self):
        n = f'{os.path.splitext(os.path.basename(self.comfile))[0]}'
        self.name = n
        print(f"Community network name: {n}")
    ########################################################


    ####################### METHODS ########################
    def _set_file_extension(self):
        # Get extension of fisrt file into directory
        # We assumed that all files are constructed in the same way
        # and though all extensions into a directory are the same
        first_file =os.listdir(self.sbml_dir)[0]
        self.extension = os.path.splitext(first_file)[1]


    def get_sbml_data(self):
        """Get all elements needed from sbml file for each network.
        These elements are the folowwing nodes from source file:
          - sbml
          - fbc
          - model
          - parameters
        """
        for species in self.species:
            sbml_file = os.path.join(self.sbml_dir, f"{species}{self.extension}")
            try:
                existant_path(sbml_file)
                self.files.append(sbml_file)
            except FileNotFoundError as e :
                logger.log.error(str(e))
                exit(1)
            self.sbml[species], self.sbml_first_line, self.default_namespace = SBML.get_root(sbml_file)
            self.fbc[species] = SBML.get_fbc(self.sbml[species])
            self.model[species] = SBML.get_model(self.sbml[species])
            self.parameters[species] = SBML.get_listOfParameters(self.model[species])


    def sbml_prefix_id(self, element:ET.Element, species:str):
        """Change the id of nodes by prefixing it with the network filename

        Args:
            element (ET.Element):  Etree element (node) to modify
            species (str): Network to be added as prefix
        """
        tag=SBML.get_sbml_tag(element)
        id = element.attrib.get("id")
        
        match tag:
            case 'reaction':
                element.attrib['id'] = prefix_id_network(self.is_community, id, species,"reaction")
                metaid =  element.attrib.get("metaid")
                if metaid:
                    element.attrib['metaid'] = prefix_id_network(self.is_community, metaid, species,"metaid")
                l_bound=element.attrib.get('{'+self.fbc[species]+'}lowerFluxBound')
                u_bound=element.attrib.get('{'+self.fbc[species]+'}upperFluxBound')
                element.attrib['{'+self.fbc[species]+'}lowerFluxBound']= prefix_id_network(self.is_community, l_bound,species)
                element.attrib['{'+self.fbc[species]+'}upperFluxBound']= prefix_id_network(self.is_community, u_bound,species)
                
                # Clean sbml by deleting notes and gene product association
                # Otherwise etree create an non findable xmlns attribute to sbml node
                # which cause an error in Cobra
                # We do it first because while doing all together there is two problems:
                # 1: When a node is delete then the newt node is the not the source next node but the one after
                # 2: when keeping nodes into list to delete after by looping on list, "notes" node are not deleted
                for el in element:
                    subtag = SBML.get_sbml_tag(el)
                    if subtag == "notes" or subtag == "geneProductAssociation":
                        element.remove(el)
                
                for el in element:
                    subtag = SBML.get_sbml_tag(el)
                    list_remove_meta = list()
                    list_add_meta = list()
                    # copy and remove list of reactant and products from source
                    if subtag == "listOfReactants" or subtag == "listOfProducts":
                        for meta in el:
                            new_meta =  copy.deepcopy(meta)
                            list_remove_meta.append(meta)
                            metabolite_id = new_meta.attrib.get("species")
                            pref_metabolite_id = prefix_id_network(self.is_community, metabolite_id, species,"metabolite")
                            new_meta.attrib['species'] = pref_metabolite_id
                            list_add_meta.append(new_meta)
                            
                        # Need to treat after looping to not mess with ids
                        for rm_meta in list_remove_meta:
                             el.remove(rm_meta)
                        for add_meta in list_add_meta:
                             el.append(add_meta)

            case 'species':
                element.attrib['id'] = prefix_id_network(self.is_community, id, species,"metabolite")
                for el in element:
                    subtag = SBML.get_sbml_tag(el)
                    if subtag == "notes":
                        element.remove(el)

            case 'parameter':
                element.attrib['id'] = prefix_id_network(self.is_community, id, species)

            case 'listOfFluxObjectives':
                for o in element:
                    name = o.attrib.get('{'+self.fbc[species]+'}reaction')
                    o.attrib['{'+self.fbc[species]+'}reaction'] = prefix_id_network(self.is_community, name, species,"reaction")
            

    def append_model(self, merged_model:ET.Element, species:str):
        """When a merged model has been created by copying the first network, all nodes are append to this
        merged model for the other networks

        Args:
            merged_model (ET.Element): Etree element (node) to modify
            species (str): Network to append to the merged model
        """
        meta_node = merged_model.find("listOfSpecies")
        param_node = merged_model.find("listOfParameters")
        reaction_node = merged_model.find("listOfReactions")

        list_obj_node = merged_model.find("{"+self.fbc[species]+"}listOfObjectives")
        obj_node = list_obj_node.find("{"+self.fbc[species]+"}objective")
        flux_obj_node = obj_node.find("{"+self.fbc[species]+"}listOfFluxObjectives")

        for meta in self.model[species].find("listOfSpecies"):
            meta_node.append(meta)

        for param in self.model[species].find("listOfParameters"):
            param_node.append(param)

        for react in self.model[species].find("listOfReactions"):
            reaction_node.append(react)

        list_obj_to_append = self.model[species].find("{"+self.fbc[species]+"}listOfObjectives")
        obj_to_append =  list_obj_to_append.find("{"+self.fbc[species]+"}objective")
        for obj in obj_to_append.find("{"+self.fbc[species]+"}listOfFluxObjectives"):
            flux_obj_node.append(obj)


    def prefix_parameter_dict(self, species:str):
        """While writing the sbml file, all parameters saved into the dictionnary needs to be prefixed
        because boundaries are modified and prefixed for each reaction

        Args:
            species (str): Network to be added as prefix
        """
        new_dict=dict()
        for key, val in self.parameters[species].items():
            new_key=prefix_id_network(self.is_community, key,species)
            new_dict[new_key] = val
        self.parameters[species]=new_dict


    def write_merge_sbml_file(self):
        """Compute all modifications needed (reaction normalization, prefixing id and boudaries 
        and parameter and objective reacrion list) then merge all networks into one mode and 
        rewrite it into temporary directory
        """
        #TODO parallelize ?
        is_first=True

        for species in self.model.keys():
            list_metabolites = SBML.get_listOfSpecies(self.model[species])
            list_parameters = SBML.get_parameters(self.model[species])
            list_objectives = SBML.get_objectives(self.model[species])
            list_reactions = SBML.get_listOfReactions(self.model[species])

            self.prefix_parameter_dict(species)

            # Prefix all metabolites with network id
            for metabolite in list_metabolites:
                self.sbml_prefix_id(metabolite, species)

            # Prefix all parameters with network id
            for parameter in list_parameters:
                self.sbml_prefix_id(parameter, species)

            # Prefix all objectives reaction with network id
            for objective in list_objectives[0]:
                if objective:
                    self.sbml_prefix_id(objective, species)

            # Delete the reactions from list of reation node
            for reaction in self.deleted_reactions.keys():
                if species in reaction:
                    id_reaction = reaction.replace(f"_{species}","")
                    node = list_reactions.find(f"reaction[@id='{id_reaction}']")
                    list_reactions.remove(node)

            # Corrects the SBML Model
            for reaction in list_reactions:
                reaction_name = reaction.attrib.get("id")
                reaction_name = prefix_id_network(self.is_community, reaction_name, species,"reaction")
                
                # Prefix all reactions, reactants, products and bounds with 
                # network id
                self.sbml_prefix_id(reaction, species)

                # Change the reversibility
                self.sbml_review_reversibilty(reaction_name, reaction)
                # switch reactants and products
                self.sbml_switch_meta(reaction_name, reaction, species)
                # remove import reactions
                if not self.keep_import_reactions: 
                    self.sbml_remove_import(reaction_name, reaction, species)

            self.sbml_review_parameters(species)

            # Merge all neworks in one file
            if is_first:
                new_sbml = self.sbml[species]
                merged_model = copy.deepcopy(self.model[species])
                merged_model.attrib["id"]=self.name
                new_sbml.remove(self.model[species])
                new_sbml.append(merged_model)
                def_ns=self.default_namespace.split("=")
                new_sbml.set(def_ns[0], def_ns[1].replace('"',''))
                is_first=False
            else:
                self.append_model(merged_model, species)

        
        # Save file in temp dir
        str_model =  self.sbml_first_line+SBML.etree_to_string(new_sbml)
        with open(self.file, 'w') as f:
            f.write(str_model)
        f.close()
        
    ########################################################


def process_result(result, model, name, equality_flux, fluxes_init, fluxes_no_import, maximize, dtypes, accumulation,
                   is_community, keep_import_reactions, objectives):
    # Deepcopy the result to avoid shared state
    result_copy = copy.deepcopy(result)

    flux_time = time()
    result_copy.check_flux(model, equality_flux=equality_flux)

   
    objective, formatted_result, flux_no_import, flux_init = format_flux_result(
                                                                        result_copy,
                                                                        fluxes_init,
                                                                        fluxes_no_import,
                                                                        is_community,
                                                                        keep_import_reactions,
                                                                        objectives,
                                                                        )

    warn = print_flux(
                        formatted_result,
                        maximize,
                        is_community, is_parallele=True
                    )

    flux_time = round(time() - flux_time, 3)

    df = pd.DataFrame([[name, objective, formatted_result.solver_type, formatted_result.search_mode,
                        formatted_result.search_type, str(accumulation), formatted_result.name, formatted_result.size, 
                        formatted_result.chosen_lp, flux_init, flux_no_import, 
                        formatted_result.objective_flux_seeds, formatted_result.objective_flux_demands,
                        str(formatted_result.OK), str(formatted_result.OK_seeds), 
                        str(formatted_result.OK_demands), flux_time]],
                      columns=['species', 'biomass_reaction', 'solver_type', 'search_mode', 
                               'search_type', 'accumulation', 'model', 'size', 'lp_flux', 
                               'cobra_flux_init', 'cobra_flux_no_import', 'cobra_flux_seeds', 
                               'cobra_flux_demands', 'has_flux', 'has_flux_seeds', 
                               'has_flux_demands', 'timer'])
    return df.astype(dtypes), formatted_result.solver_type, formatted_result.search_mode, warn


def format_flux_result(result, fluxes_init, fluxes_no_import, is_community, keep_import_reactions, objectives):
    """
    Format Resmod result data with flux information.

    Args:
        result (Resmod): The result object.
        fluxes_init (dict): Initial fluxes for each objective.
        fluxes_no_import (dict): Fluxes after disabling import reactions.
        is_community (bool): Whether this is a community model.
        keep_import_reactions (bool): Whether import reactions were retained.
        objectives (str or dict): Objectives used.

    Returns:
        tuple: (objective, updated result, flux_no_import, flux_init)
    """
    if keep_import_reactions:
        flux_no_import = None
    else:
        flux_no_import = fluxes_no_import

    if is_community:
        objective = objectives
        flux_init = fluxes_init
    else:
        objective = result.tested_objective
        flux_init = fluxes_init[objective]
        flux_no_import = flux_no_import[objective]
        result.objective_flux_seeds = result.objective_flux_seeds[objective]
        result.objective_flux_demands = (
            result.objective_flux_demands.get(objective)
            if result.objective_flux_demands
            else None
        )

    return objective, result, flux_no_import, flux_init



def print_flux(result, maximize, is_community, is_parallele=False):
    """
    Standalone function to print flux results as a table row.

    Args:
        result (Resmod): The current result to print.
        maximize (bool): Whether we're in maximize mode.
        is_community (bool): If the model is a community type.
        color (object): Color utility (like a namespace with .red_bright, .green_light, etc.).

    Returns:
        bool: warning flag (e.g., for hybrid LP divergence).
    """
    warning = False
    if result.name != "model_one_solution":
        if result.OK_seeds:
            if result.solver_type in {"HYBRID", "FBA"} and abs(result.chosen_lp - result.objective_flux_seeds) < 0.1:
                color_seeds = color_lp = color.green_light
            else:
                color_seeds = color_lp = color.cyan_light
                if result.solver_type in {"HYBRID", "FBA"} and not maximize and abs(result.chosen_lp - result.objective_flux_seeds) > 0.1:
                    warning = True
        else:
            color_seeds = color.red_bright

        concat_result = f"{result.name} | "

        if not result.infeasible_seeds:
            if is_community:
                concat_result = add_print_seed_community(result, color_seeds, concat_result, result.infeasible_seeds)
            else:
                concat_result += f"{color_seeds}{result.objective_flux_seeds}{color.reset} | "
                warning, concat_result = add_print_demands(result, maximize, warning, concat_result)
        else:
            concat_result += "Infeasible | "
            if is_community:
                concat_result = add_print_seed_community(result, color_seeds, concat_result, result.infeasible_seeds)
            else:
                warning, concat_result = add_print_demands(result, maximize, warning, concat_result)

        if result.solver_type in {"HYBRID", "FBA"}:
            lp_flux_rounded = round(result.chosen_lp, 4)
            concat_result += f" | {color_lp}{lp_flux_rounded}{color.reset}"

        if not is_parallele:
            print(concat_result)

    return warning


def add_print_seed_community(result:Resmod, color_seeds:str, concat_result:str, is_infeasible:bool=False):
    """Used for Community mode to add objectives line by line with its respective seeds flux value without rewriting de model name, 
    and the corresponding demands value for each objective

    Args:
        result (Resmod): Resmod object containing results data value and fluxes
        color_seeds (str): Text coloration for terminal
        maximize (bool): Needed for demands to define if a warning must be printed depending maximisation argument used or not (Hybrid-lpx)
        concat_result (str): String to print by concatening value of table (column and line)
        is_infeasible (bool, optional): Is the solution ingeasible with cobra. Defaults to False.

    Returns:
        str: String to print by concatening value of table (column and line)
    """
    is_first = True
    for objective, value in result.objective_flux_seeds.items():
        if is_first:
            if not is_infeasible:
                concat_result += color_seeds + objective + ": " + str(value) + color.reset + " | "  
            # In community mode, no warining from Hybrid-lpx to print
            _, concat_result = add_print_demands(result, False, False, concat_result, objective)
            is_first=False
        else:
            if is_infeasible:
                next_line = f"\n        |            | "
            else:
                next_line = f"\n        | " + color_seeds + objective + ": " + str(value) + color.reset + " | "
            _, next_line = add_print_demands(result, False, False, next_line, objective)
            concat_result += next_line
    return concat_result


def add_print_demands(result:Resmod, maximize:bool, warning:bool, concat_result:str, objective:str=None):
    """Print Demands flux respectively to each objective (called at the right time)

    Args:
        result (Resmod): Resmod object containing results data value and fluxes
        maximize (bool): Define if a warning must be printed depending of maximisation argument used or not (Hybrid-lpx)
        warning (bool): Warning that has to be raised or not. Only used for Hybrid-lpx mode
        concat_result (str): String to print by concatening value of table (column and line)
        objective (str, optional): The objective reaction to add in results (for community mode). Defaults to None.

    Returns:
        bool, str: warning, concat_result
    """
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

    if not result.infeasible_demands:
        flux_demand = result.objective_flux_demands
        supp = ""
        if flux_demand == None:
            flux_demand = "NA"
        else:
            if objective:
                flux_demand = result.objective_flux_demands[objective]
                supp = objective + ": " 
        
        concat_result += color_demands + supp + f"{flux_demand}" + color.reset
    else:
        concat_result += f"Infeasible" 

    return warning, concat_result