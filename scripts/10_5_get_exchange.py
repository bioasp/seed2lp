import os
from sys import argv
from seed2lp import sbml
import xml.etree.ElementTree as etree

def get_listOfProducts_from_name(model, reaction_name) -> list:
    """return list of products of a reaction"""
    reactions_list = sbml.get_listOfReactions(model)
    for reaction in reactions_list:
        if reaction_name == reaction.attrib['id']:
            for e in reaction:
                tag = sbml.get_sbml_tag(e)
                if tag == "listOfProducts":
                    listOfProducts = e
                    break
    return listOfProducts

def trim(meta):
    meta_trim = str.strip(meta)
    meta_trim = meta_trim.rsplit('_', 1)[0]
    meta_trim = meta_trim.split('_', 1)[1]
    return meta_trim

if __name__ == '__main__':
    # User data
    species_name = argv[1]
    sbml_file = argv[2]
    output=argv[3]

    tree = etree.parse(sbml_file)
    net = tree.getroot()
    model = sbml.get_model(net)

    exch=list()
    exch_trim=list()
    SBML, sbml_first_line = sbml.get_root(sbml_file)
    reactions_list = sbml.get_listOfReactions(model)
    parameters = sbml.get_listOfParameters(model)
    fbc = sbml.get_fbc(SBML)

    for r in reactions_list:
        reactants = sbml.get_listOfReactants(r)
        products = sbml.get_listOfProducts(r)
        reaction_name = r.attrib.get("id")

        lower_bound = parameters[r.attrib.get('{'+fbc+'}lowerFluxBound')] \
                    if type(r.attrib.get('{'+fbc+'}lowerFluxBound')) is not float \
                    else '"'+r.attrib.get('{'+fbc+'}lowerFluxBound')+'"'
        lbound = round(float(lower_bound),10)
        upper_bound = parameters[r.attrib.get('{'+fbc+'}upperFluxBound')] \
                    if type(r.attrib.get('{'+fbc+'}upperFluxBound')) is not float \
                    else '"'+r.attrib.get('{'+fbc+'}upperFluxBound')+'"'
        ubound = round(float(upper_bound),10)

        # uses the definition of boundaries as cobra
        # a reaction is in boundaries (so exchange reaction)
        # when a reaction has only one metabolite and 
        # does not have reactants or products
        if not (reactants and products):
            exchange=None
            if reactants and len(reactants) == 1:
                if lbound >= 0:
                    continue
                else:
                    #print ("reactant  ",reaction_name, lbound, ubound)
                    exchange=sbml.get_listOfReactants_from_name(model,reaction_name)
            elif (products and len(products) == 1):
                if ubound <= 0:
                    continue
                else:
                    #print ("product  ",reaction_name, lbound, ubound)
                    exchange=get_listOfProducts_from_name(model,reaction_name)
            if exchange:
                for metabolite in exchange:
                    meta=metabolite.attrib.get('species')
                    meta_trim = trim(meta)
                    exch_trim.append(meta_trim)
                    exch.append(meta)



    # saving as tsv file 
    exch_trim_file=os.path.join(output, f"{species_name}_exchanges.txt")
    exch_file=os.path.join(output, f"{species_name}_exchanges_pre_suffix.txt")

    with open(exch_file, "w") as outfile:
        outfile.write("\n".join(str(item) for item in exch))
    with open(exch_trim_file, "w") as trimfile:
        trimfile.write("\n".join(str(item) for item in exch_trim))
        