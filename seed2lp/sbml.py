"""Routines to extract information from SBML files.

"""
import xml.etree.ElementTree as ET
from re import sub, match, search
from . import logger

def register_all_namespaces(file:str):
    """Get namespaces for rewriting SBML file

    Args:
        file (str): SBML file path
    """
    namespaces = dict([node for _, node in ET.iterparse(file, events=['start-ns'])])
    for ns in namespaces:
        #print(ns,  namespaces[ns])
        ET.register_namespace(ns, namespaces[ns])
        
def get_root(file:str):
    """Get etree root

    Args:
        file (str): SBML file path

    Returns:
        sbml (etree Element), first_line (str) : Return an etree elemnt of the network, and the first line of the sbml file
    """
    register_all_namespaces(file)
    with open(file) as f:
        first_line = f.readline()
        xmlstring = f.read()
    f.close()
    
    # Remove the default namespace definition (xmlns="http://some/namespace")
    default_namespace = search(r'\sxmlns="[^"]+"', xmlstring).group()
    xmlstring = sub(default_namespace, '', xmlstring, count=1)

    sbml = ET.fromstring(xmlstring)  
    #tree = ET.parse(file)
    #sbml = tree.getroot()
    return sbml, first_line, default_namespace

def get_sbml_tag(element:ET.Element) -> str:
    "Return tag associated with given SBML element"
    if element.tag[0] == "{":
        _, tag = element.tag[1:].split("}")  # uri is not used
    else:
        tag = element.tag
    return tag


def get_model(sbml:ET.Element) -> ET.Element:
    """
    return the model of a SBML
    """
    model_element = None
    for e in sbml:
        tag = get_sbml_tag(e)
        if tag == "model":
            model_element = e
            break
    return model_element

def get_listOfSpecies(model:ET.Element) -> list[ET.Element]:
    """
    return list of species of a SBML model
    """
    listOfSpecies = None
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfSpecies":
            listOfSpecies = e
            break
    return listOfSpecies


def get_listOfReactions(model:ET.Element) -> list[ET.Element]:
    """return list of reactions of a SBML model"""
    listOfReactions = []
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfReactions":
            listOfReactions = e
            break
    return listOfReactions


def get_listOfReactants(reaction:ET.Element, species:str=None, is_community:bool=False) -> list:
    """return list of reactants of a reaction"""
    listOfReactants = list()
    listOfReactantsNames = list()
    for e in reaction:
        tag = get_sbml_tag(e)
        if tag == "listOfReactants":
            for meta in e:
                meta_id = meta_name = meta.attrib.get('species')
                if is_community:
                    meta_id = sub("^M_", f"M_{species}_",meta_id)
                listOfReactants.append([meta_id, meta.attrib.get('stoichiometry'), meta_name])
                
                # Create a list of only of meta to determine if a reaction will be transport reaction
                # both list must be the same (same element in reactnats and products)
                listOfReactantsNames.append(meta_name.rsplit('_', 1)[0])
            break
    return listOfReactants, listOfReactantsNames


def get_listOfReactants_from_name(model:ET.Element, reaction_name) -> list[ET.Element]:
    """return list of reactants of a reaction"""
    reactions_list = get_listOfReactions(model)
    for reaction in reactions_list:
        if reaction_name == reaction.attrib['id']:
            for e in reaction:
                tag = get_sbml_tag(e)
                if tag == "listOfReactants":
                    listOfReactants = e
                    break
    return listOfReactants


def get_listOfProducts(reaction:ET.Element, species:str=None, is_community:bool=False) -> list:
    """return list of products of a reaction"""
    listOfProducts = list()
    listOfProductsNames = list()
    for e in reaction:
        tag = get_sbml_tag(e)
        if tag == "listOfProducts":
            for meta in e:
                meta_id = meta_name  = meta.attrib.get('species')
                if is_community:
                    meta_id = sub("^M_", f"M_{species}_",meta_id)
                listOfProducts.append([meta_id, meta.attrib.get('stoichiometry'), meta_name])

                # Create a list of only of meta to determine if a reaction will be transport reaction
                # both list must be the same (same element in reactnats and products)
                listOfProductsNames.append(meta_name.rsplit('_', 1)[0])
            break
    return listOfProducts, listOfProductsNames


def get_reaction_from_name(model:ET.Element, reaction_name) -> list[ET.Element]:
    """return list of reactants of a reaction"""
    reactions_list = get_listOfReactions(model)
    for reaction in reactions_list:
        if reaction_name == reaction.attrib['id']:
            return reaction
    raise ValueError(f"No reaction {reaction_name} found in list of reactions \n")


def get_fbc(sbml:ET.Element):
    """
    return the fbc namespace of a SBML
    """
    fbc = None 
    for nss in ET._namespaces(sbml):
        for key in nss:
            if key is not None and 'fbc' in key:
                fbc=key
                break
    return fbc


def get_listOfParameters(model:ET.Element)-> dict:
    """return list of reactions of a SBML model"""
    listOfParameters = dict()
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfParameters":
            for param in e:
                listOfParameters[param.get('id')]=param.get('value') 
            break
    return listOfParameters


def get_parameters(model:ET.Element) -> list[ET.Element]:
    """
    return list of parameters of a SBML model
    """
    listOfParameters = None
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfParameters":
            listOfParameters = e
            break
    return listOfParameters


def get_objectives(model:ET.Element) -> list[ET.Element]:
    """
    return list of parameters of a SBML model
    """
    listOfObjective = None
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfObjectives":
            listOfObjective = e
            break
    return listOfObjective


def get_listOfFluxObjectives(model,fbc)-> list:
    """return list of objective reactions of a SBML model"""
    listOfFluxObjectives = list()

    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfObjectives":
            for lo in e[0]:
                if lo:
                    for o in lo:
                        name = o.attrib.get('{'+fbc+'}reaction')
                        coef = o.attrib.get('{'+fbc+'}coefficient')
                        reaction = get_reaction_from_name(model, name)
                        listOfFluxObjectives.append([name,coef,reaction])
            break
    return listOfFluxObjectives


def read_SBML_species(filename)-> dict:
    """Yield names of species listed in given SBML file"""
    model_dict = dict()
    tree = ET.parse(filename)
    sbml = tree.getroot()
    model = get_model(sbml)
    species_list = list()
    reactions_list = list()
    
    for species in get_listOfSpecies(model):
        species_list.append(species.attrib['id'])
    for reaction in get_listOfReactions(model):
        reactions_list.append(f"{reaction.attrib['id']}")

    model_dict['Metabolites'] = species_list
    model_dict['Reactions'] = reactions_list
    return model_dict


def get_used_metabolites(filename, call_log=False)-> set:
    """Determine from source file the truly used metabolite (and not the list of species)
    Necessary for scripts 10_1_scope_analyse.py and 10_3_iCN718_metabolite_analyses.py

    Args:
        filename (str): Path to thie SBML file

    Returns:
        used_metabolites (set): Set of used metabolites
    """
    tree = ET.parse(filename)
    sbml = tree.getroot()
    model = get_model(sbml)
    # SBML has species that are never used on any reactions 
    # but are present into species list
    # Also, there is some reaction that involves species but 
    # having boundaries to [0,0], so we are not taken into account
    # the species of the species of these reactions into the used metabolites
    used_metabolites = set()

    fbc = get_fbc(get_root(filename)[0])
    parameters = get_listOfParameters(model)

    for reaction in get_listOfReactions(model):
        ubound =  parameters[reaction.attrib.get('{'+fbc+'}upperFluxBound')]
        lbound = parameters[reaction.attrib.get('{'+fbc+'}lowerFluxBound')]
        if float(ubound) == 0 and float(lbound) == 0  and call_log:
            logger.log.warning(f"Reaction {reaction.attrib['id']} deleted, boudaries [0,0]")
            continue
        else:
            reactants,_ = get_listOfReactants(reaction,"",False)
            products,_ = get_listOfProducts(reaction,"",False)
            for reactant in reactants:
                used_metabolites.add(reactant[0])
            for product in products:
                used_metabolites.add(product[0])

    return used_metabolites



def etree_to_string(model) -> str:
    return str(ET.tostring(model, encoding='utf-8', method='xml'),'UTF-8')

def create_sub_element(element:ET.Element, sub_element:str):
    ET.SubElement(element,sub_element)

def remove_sub_elements(element:ET.Element):
    for metabolite in list(element):
        element.remove(metabolite)

def add_metabolites(element:ET.Element, metabolites_list):
    for metabolite in metabolites_list:
        element.append(metabolite)

def remove_reaction(model:ET.Element, element:ET.Element):
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfReactions":
            e.remove(element)

def check_remove_objective(model:ET.Element, reaction:ET.Element, fbc):
    for e in model:
        tag = get_sbml_tag(e)
        if tag == "listOfObjectives":
            for lo in e[0]:
                if lo:
                    for o in lo:
                        if o.attrib.get('{'+fbc+'}reaction') == reaction.attrib['id']:
                            lo.remove(o)