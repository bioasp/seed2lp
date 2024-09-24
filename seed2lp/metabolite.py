# Object Metabolite constitued of:
#   - name (str): Name of the metabolite
#   - stoichiometry (int): Stoiciometry of the metabolite in the reaction eaquation if linked into a reaction 
#                           (not set for targets or possible seeds or forbidden seeds)
#   - compartment (str): character of the compartment of metabolite

class Metabolite:
    def __init__(self, name:str, stoichiometry:float=None, meta_type:str=""):
        """Initialize Object Metabolite

        Args:
            name (str): Name / ID of the Metabolite
            stoichiometry (int, optional): Stoichiometry of the metabolite if into a reactions. Defaults to None.
        """
        self.name = name
        self.stoichiometry = stoichiometry
        self.type = meta_type

    ######################## GETTER ########################
    def _get_name(self,):
        return self.name

    def _get_stoichiometry(self,):
        return self.stoichiometry
    ########################################################

    ######################## SETTER ########################
    def _set_name(self, name:str):
        self.name  =  name

    def _set_stoichiometry(self, stoichiometry:float):
        self.stoichiometry = stoichiometry
    ########################################################


    ######################## METHODS ########################
    def convert_to_facts(self, metabolite_type:str, reaction_name:str=None):
        """Convert metabolite into ASP facts : an atom reactant or product, associated to a reaction 
        and having a stoichiometry value

        Args:
            metabolite_type (str): Type of metabolite (exchange, transport, other)
            reaction_name (str, optional): Name of the reaction associated to the metabolite. Defaults to None.

        Returns:
            facts (str): The ASP atom created
        """
        facts = ""
        match metabolite_type:
            case "reactant"|"product":
                
                facts += f'{metabolite_type}("{self.name}","{"{:.10f}".format(self.stoichiometry)}","{reaction_name}","{self.type}").\n'
            case "seed":
                facts += f'{metabolite_type}("{self.name}","{self.type}").\n'
            case _:
                facts += f'{metabolite_type}("{self.name}","{"{:.10f}".format(self.stoichiometry)}","{reaction_name}","{self.type}").\n'
        return facts


    ########################################################
