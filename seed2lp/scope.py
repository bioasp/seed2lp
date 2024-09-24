from .network import Network
from menetools import run_menescope
from .file import is_valid_dir, save
from os.path import join
from .sbml import get_used_metabolites
import libsbml
from padmet.utils.sbmlPlugin import convert_from_coded_id
from padmet.utils.connection import sbmlGenerator
import sys
from . import logger


class Scope:
    def __init__(self, file:str, network:Network, output_dir:str):
        """Initialize Object Scope

        Args:
            file (str): SBML File (Needed to detect source used metabolites on the network)
            network (Network): Corrected Network
        """
        self.file = file
        self.network = network
        self.output_dir = output_dir
        self.dir_seeds_sbml = is_valid_dir(join(output_dir,'sbml'))
        self.dir_scope = is_valid_dir(join(output_dir,'scope'))

    ######################## METHODS ########################
    def execute(self):
        """Execute the scope from seeds solution for each solution and save it into file.
        Creates an intermediate seed sbml file.
        """
        # Get global data on the network
        set_used_metabolites = get_used_metabolites(self.file)

        # run the scope for each solutions of the result
        for result in self.network.result_seeds:
            #TODO : print better in TABLE
            print(result.run_mode.upper())
            print(result.solver_type)
            print(result.search_mode)
            print(result.name)
            print("Accumulation:", result.accu)

            if  result.accu == True:
                accu="accu"
            else:
                accu="no_accu"

            run_mode = result.run_mode.lower().replace(" ","_").replace("-", "_")
            solver = result.solver_type.lower().replace(" ","_").replace("-", "_")
            search_mode = result.search_mode.lower().replace(" ","_").replace("-", "_")
            seeds=set(result.seeds_list)

            seeds_sbml_complete_dir_path = is_valid_dir(join(self.dir_seeds_sbml, run_mode, solver, search_mode, accu))
            seeds_sbml_path=join(seeds_sbml_complete_dir_path, f'{result.name}.sbml')
            scope_dir_path = is_valid_dir(join(self.dir_scope, run_mode, solver, search_mode, accu))

            # Write the seed into sbl format for each solutions
            create_species_sbml(seeds, seeds_sbml_path)
            logger.log.info(f"Seeds sbml file created: {seeds_sbml_path}")
            
            # Run menescope from seed to get the scope
            logger.log.info(f"Scope running for {seeds_sbml_path}...") 
            scope_model = run_menescope(self.file, seeds_sbml_path)
            logger.log.info(f"Scope terminated.") 
            scope_model["size_scope"] = len(scope_model["scope"])
            scope_model["size_all_metabolites"] = len(set_used_metabolites)


            
            print("size of scope", scope_model["size_scope"])
            print("size of all metabolites", scope_model["size_all_metabolites"],"\n\n")
            save(f'{result.name}', scope_dir_path, scope_model, "json")
            logger.log.info(f"Scope saved in: {scope_dir_path}/{result.name}.json.") 



def create_species_sbml(metabolites, outputfile):
    """Create a SBML files with a list of species containing metabolites of the input set.
    Check if there are forbidden SBML characters in the metabolite IDs/ If yes, exit.
    
    Args:
        metabolites (set): set of metabolites
        outputfile (str): SBML file to be written
    """
    document = libsbml.SBMLDocument(2, 1)
    model = document.createModel("metabolites")
    forbidden_charlist = ['-', '|', '/', '(', ')',
        "'", '=', '#', '*', '.', ':', '!', '+', '[',
        ']', ',', ' ']
    forbidden_character_in_metabolites = None
    issue_trying_to_add_species = None
    for compound in metabolites:
        compound = compound.strip('"')
        _, _, comp = convert_from_coded_id(compound)
        s = model.createSpecies()
        sbmlGenerator.check(s, 'create species')
        forbidden_characters_detacted = [char for char in forbidden_charlist if char in compound]
        if len(forbidden_characters_detacted) > 0:
            logger.log.warning("Forbidden character ({0}) in {1}. SBML creation will failed.".format(' '.join(forbidden_characters_detacted), compound))
            forbidden_character_in_metabolites = True
        try:
            sbmlGenerator.check(s.setId(compound), 'set species id')
        except:
            issue_trying_to_add_species = True
            logger.log.warning("Issue when trying to add compound {0}.".format(compound))

        if comp is not None:
            sbmlGenerator.check(s.setCompartment(comp), 'set species compartment')
        elif comp is None:
            logger.log.warning("No compartment for " + compound)

    if issue_trying_to_add_species is True and forbidden_character_in_metabolites is True:
        logger.log.warning("Forbidden character in compound ID, SBML creation will failed.")
        logger.log.warning("Modify the metabolic networks SBMl file by renaming these metabolites and removing the forbidden character.")
        sys.exit(1)
    if issue_trying_to_add_species is True and forbidden_character_in_metabolites is None:
        logger.log.warning("Issue when trying to add metabolite into SBML file, potential issue with SBML format.")
        logger.log.warning("Modify the metabolic networks SBMl file by renaming these metabolites and removing the forbidden character.")
        sys.exit(1)

    libsbml.writeSBMLToFile(document, outputfile)