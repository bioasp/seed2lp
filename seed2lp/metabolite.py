# Object Metabolite constitued of:
#   - name (str): Name of the metabolite
#   - stoichiometry (int): Stoiciometry of the metabolite in the reaction eaquation if linked into a reaction 
#                           (not set for targets or possible seeds or forbidden seeds)
#   - compartment (str): character of the compartment of metabolite

class Metabolite:
    def __init__(self, id_meta:str, name:str, stoichiometry:float=None, meta_type:str="", 
                 species:str=""):
        """Initialize Object Metabolite

        Args:
            name (str): Name / ID of the Metabolite
            stoichiometry (int, optional): Stoichiometry of the metabolite if into a reactions. Defaults to None.
        """
        self.id_meta = id_meta
        self.name = name
        self.stoichiometry = stoichiometry
        self.type = meta_type
        self.species = species


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
                
                facts += f'{metabolite_type}("{self.id_meta}","{"{:.10f}".format(self.stoichiometry)}","{reaction_name}","{self.type}","{self.name}","{self.species}").\n'
            case "seed":
                facts += f'{metabolite_type}("{self.id_meta}","{self.type}","{self.name}").\n'
            case _:
                facts += f'{metabolite_type}("{self.id_meta}","{"{:.10f}".format(self.stoichiometry)}","{reaction_name}","{self.type}","{self.name}","{self.species}").\n'
        return facts

    ########################################################
