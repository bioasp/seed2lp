# Object Reaction constitued of
#   - name: name/id of reaction
#   - reversible (bool): Set if the reaction is reversible
#   - lbound (float): Lower bound of a reaction
#   - ubound (float): Upper bound of a reaction
#   - Reactants (list): List of reactants (object Metabolite)
#   - Products (list): List of list of products (object Metabolite)

from seed2lp.metabolite import Metabolite
from . import logger

class Reaction:
    def __init__(self, name:str, reversible:bool=False, lbound:float=None, ubound:float=None):
        """Initialize Object Reaction

        Args:
            name (str): name/id of reaction
            reversible (bool, optional): Set if the reaction is reversible. Defaults to False.
            lbound (float, optional): Lower bound of a reaction. Defaults to None.
            ubound (float, optional): Upper bound of a reaction. Defaults to None.
        """
        self.name = name
        self.reversible = reversible
        self.lbound = lbound
        self.ubound = ubound
        self.reactants = list()
        self.products = list()
        self.is_exchange = False
        self.is_transport = False
        self.is_meta_modified = False
        self.is_reversible_modified = False


    ######################## SETTER ########################
    def _set_reactants(self, reactants_list:list):
        self.reactants = reactants_list
    
    def _set_products(self, products_list:list):
        self.products = products_list
    ########################################################

    ######################## METHODS ########################
    def add_metabolites_from_list(self, metabolites_list:list, metabolite_type:str,
                                  meta_exchange_list:list, meta_transport_list:list):
        """Add all Metabolite from a list as a Reactant or Product list

        Args:
            metabolites_list (list): List of metabolite
            metabolite_type (str): Type of metabolite to construc object list (Reactant or Product)
            meta_exchange_list (list): List of exchanged metabolite
            meta_transport_list (list): List of transport metabolite
        """
        meta_list=[]
        for meta in metabolites_list:
            metabolite = Metabolite(meta[0],round(float(meta[1]),10))
            # A reaction is an exchange reaction
            # Exchange reaction involving multiple metabolites are not considered as exchange
            # but will me removed into write_facts() function
            if self.is_exchange:
                # The metabolite is tagged as exchange
                meta_exchange_list.append(metabolite.name)
                if metabolite.name in meta_transport_list:
                    meta_transport_list.remove(metabolite.name)
            # we do not want to change exchange tag into transport tag
            # The reaction has to be taggued transport
            # if the reaction is not reversible, only the product is taggued transport
            # if the reaction is reversible both can be transported
            elif self.is_transport \
                and (metabolite.name not in meta_exchange_list) \
                and metabolite_type == "product":
                # The metabolite is tagged as exchange
                meta_transport_list.append(metabolite.name)
                metabolite.type = "transport"
            # A reaction is not an exchange reaction nor transport reaction 
            # Exchange reactions involving multiple metabolites are treated like intern metabolite
            else:
                # Check if the metabolite already existe in list of network
                if metabolite.name in meta_exchange_list:
                    metabolite.type = "exchange"
                elif metabolite.name in meta_transport_list:
                    metabolite.type = "transport"
                else:
                    metabolite.type = "other"
            meta_list.append(metabolite)
        
        meta_list.sort(key=lambda x: x.name)
        match metabolite_type:
            case "reactant":
                self._set_reactants(meta_list)
            case "product":
                self._set_products(meta_list)
        return meta_exchange_list, meta_transport_list


    def convert_to_facts(self, keep_import_reactions, use_topological_injections):
        """Correcting the Network an convert into facts

        Args:
            keep_import_reactions (bool):  Import reactions are not removed
            use_topological_injections (bool): Metabolite of import reaction are seeds
        """
        upper = self.ubound
        rev_upper = -self.lbound
        lower = round(float(0),10)
        facts = ""
        if self.reversible:
            # When the reaction is reversible, the reaction is splitted
            # Create 2 different reactions going in one way for reversible reaction  
            # Cases : [-1000, 1000] | [-8, 1000] | [-1000, 8]
            # divided in : 2*[0,1000] | [0,1000] and rev_[0,8] | [0,8] and rev_[0,1000]
            #lower= round(float(0),10)
            facts += self.write_facts(lower, 
                                    rev_upper,
                                    self.products, 
                                    self.reactants, 
                                    keep_import_reactions, 
                                    use_topological_injections, 
                                    self.reversible,
                                    True)


        # Upper bound does not change on forward reaction
        facts += self.write_facts(lower, 
                                    upper,
                                    self.reactants, 
                                    self.products, 
                                    keep_import_reactions, 
                                    use_topological_injections, 
                                    self.reversible,
                                    False)
        return facts


    
    def write_facts(self, lbound:float, ubound:float, reactants:list, products:list,
                         keep_import_reactions:bool, use_topological_injections:bool, 
                         reversible:bool, is_reversed:bool):
        """Convert the description of a reaction into ASP facts after correcting the Network

        Args:
            lbound (float): Lower bound of a reaction
            ubound (float): Upper bound of a reaction
            reactants (list): List of Reactants (Metabolite)
            products (list): List of Products (Metabolite)
            keep_import_reactions (bool):  Import reactions are not removed
            use_topological_injections (bool): Metabolite of import reaction are seeds
            reversible (bool): Define if the reaction is reversible.
            is_reversed (bool): Define if the reaction is the reversed writtent as "Rev_R_*"

        Returns:
            str: Reaction converted into ASP Facts
        """

        #Add reverse reaction
        # If mode remove_rxn, the import reactions (none -> metabolite)
        # are removed
        facts=""

        # Delete both exchange reaction and multiple metabolite exchange reaction
        # A reaction is multiple exchange
        # when None -> A + B || A + B -> None || None <-> A + B || A + B <-> None
        is_import_reaction = not reactants

        if not is_reversed:
            name = self.name
            if reversible:
                facts += f'reversible("{name}","rev_{self.name}").\n'
        else:
            name = f'rev_{self.name}'
        
        # only one metabolite involved exchange reaction are tagued as exchange
        # metabolite of exchange reaction involving multipele metabolite are managed like internal metabolites
        if self.is_exchange:
            facts += f'exchange("{name}").\n'
        
        prefix=""
        if not keep_import_reactions and is_import_reaction:
            prefix = "rm_"
            logger.log.info(f"Reaction {self.name} artificially removed into lp facts with a prefix 'rm_'")

        facts += f'{prefix}reaction("{name}").\n'
        
        
    
        facts += f'{prefix}bounds("{name}","{"{:.10f}".format(lbound)}","{"{:.10f}".format(ubound)}").\n'
        
        if self.is_transport:
            facts +=  f'{prefix}transport("{prefix}{name}","{reactants[0].name}","{products[0].name}").\n'


        for metabolite in reactants:
            facts += metabolite.convert_to_facts(f"{prefix}reactant", name)

        for metabolite in products:
            facts += metabolite.convert_to_facts(f"{prefix}product", name)
            # comme reversible, appelé 2 fois, donc suffit pour uniquement les produits
            if use_topological_injections and is_import_reaction:  # this reaction is a generator of seed
                facts += metabolite.convert_to_facts("seed")

        return facts
    ########################################################
