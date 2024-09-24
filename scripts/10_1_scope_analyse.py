import os
import pandas as pd
from sys import argv
from seed2lp import sbml
import xml.etree.ElementTree as etree
import json

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
    species_scope_dir = argv[3]
    species_seeds_dir = argv[4]
    objective_file = argv[5]
    modes_info = argv[6]

    if modes_info == "netseed":
        run = mode = "netseed"
        optim = "submin"
        accu = True
    else:
        #'run','mode','optim', accu
        modes_split = modes_info.split("/")
        run = modes_split[0]
        mode = modes_split[1]
        optim = modes_split[2]
        if  modes_split[3] == "no_accu":
            accu=False
        else:
            accu=True

    
    modes_info=modes_info.replace("/", "_")
        
    tree = etree.parse(sbml_file)
    net = tree.getroot()
    model = sbml.get_model(net)

    species_set = sbml.get_used_metabolites(sbml_file, False)

    with open(objective_file) as fd:
        objective = fd.readline()

    reactants=list()
    biomass_reactants = sbml.get_listOfReactants_from_name(model,objective)
    for reactant in biomass_reactants:
        reactants.append(reactant.attrib.get('species'))
    biomass_reactants_set=set(reactants)

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
                    meta = metabolite.attrib.get('species')
                    meta_trim =  trim(meta)
                    exch.append(meta)
                    exch_trim.append(meta_trim)
    exchange_set=set(exch)
    exchange_trim_set=set(exch_trim)

    

    solutions_set=list()

    dtypes = {'species':'str',
            'run':'str',
            'mode':'str',
            'optim':'str',
            'accu':'str',
            'model':'str',
            'is_equal_union_species':'bool',
            'missing':'str',
            'is_biomass_included':'bool',
            'missing_biomass':'str',
            'percentage_missing_biomass':'float',
            'is_exchange_included':'bool',
            'missing_exchange':'str',
            'percentage_missing_exchange':'float',
            'is_seed_included_to_exchange':'bool',
            'missing_seed_into_exchange':'str',
            'percentage_missing_seed_into_exchange':'float',
            'is_exchange_included_to_seed':'bool',
            'missing_exchange_into_seed':'str',
            'percentage_missing_exchange_into_seeds':'float'}
    
    comparison_scope_df=pd.DataFrame(columns=['species','run', 'mode', 'optim', 'accu', 'model',
                                'is_equal_union_species', 'missing', 'percentage_missing',
                                'is_biomass_included', 'missing_biomass', 'percentage_missing_biomass',
                                'is_exchange_included', 'missing_exchange', 'percentage_missing_exchange',
                                'is_seed_included_to_exchange', 'missing_seed_into_exchange', 'percentage_missing_seed_into_exchange',
                                'is_exchange_included_to_seed', 'missing_exchange_into_seed', 'percentage_missing_exchange_into_seeds'])
    comparison_scope_df = comparison_scope_df.astype(dtypes)

    # Loop into all solutions of a specie
    for filename in os.listdir(species_scope_dir):
        scope_file = os.path.join(species_scope_dir, filename)
        model_name=os.path.splitext(filename)[0]
         
        # Get Scope
        f = open(scope_file)
        scope = json.load(f)

        scope_set = set(scope['scope'])

        # Get Seeds
        seeds=list()
        seeds_trim=list()
        seed_file=f"{species_seeds_dir}/{model_name}.sbml"
        tree = etree.parse(seed_file)
        net = tree.getroot()
        model = sbml.get_model(net)
        seeds_list = sbml.get_listOfSpecies(model)
        for e in seeds_list:
            seed = e.attrib['id']
            seed_trim = trim(seed)
            seeds.append(seed)
            seeds_trim.append(seed_trim)
        seed_set = set(seeds)
        seed_trim_set = set(seeds_trim)

        # compare scope with union of metabolite
        diff_scope = None
        is_equal_union_species=False
        if(scope_set == species_set):
            is_equal_union_species=True
        else:
            diff_scope = list(species_set.difference(scope_set))
            diff_scope_bigger = list(scope_set.difference(species_set))
            #print(diff_scope_bigger)

        # Compare scope with biomass reactant
        diff_biomass = None
        is_biomass_included = biomass_reactants_set.issubset(scope_set)
        if not is_biomass_included:
            diff_biomass=list(biomass_reactants_set.difference(scope_set))

        # Compare scope with exchange metabolites
        diff_exchange = None
        is_exchange_included = exchange_set.issubset(scope_set)
        if not is_exchange_included:
            diff_exchange=list(exchange_set.difference(scope_set))

        # Compare seed with exchange metabolites: seeds include into exchange
        diff_seed_into_exchange = None
        is_seed_included_to_exchange = seed_trim_set.issubset(exchange_trim_set)
        if not is_seed_included_to_exchange:
            diff_seed_into_exchange=list(seed_trim_set.difference(exchange_trim_set))

        # Compare seed with exchange metabolites: exchange included into seeds
        diff_exchange_into_seeds = None
        is_exchange_included_to_seeds = exchange_trim_set.issubset(seed_trim_set)
        if not is_exchange_included_to_seeds:
            diff_exchange_into_seeds=list(exchange_trim_set.difference(seed_trim_set))
        

        if diff_scope:
            percentage_missing = len(diff_scope)*100/len(species_set)
        else:
            percentage_missing = 0
        if diff_biomass:
            percentage_missing_biomass = len(diff_biomass)*100/len(biomass_reactants_set)
        else:
            percentage_missing_biomass = 0
        if diff_exchange:
            percentage_missing_exchange = len(diff_exchange)*100/len(exchange_set)
        else:
            percentage_missing_exchange = 0
        if diff_seed_into_exchange:
            percentage_missing_seed_into_exchange = len(diff_seed_into_exchange)*100/len(seed_set)
        else:
            percentage_missing_seed_into_exchange = 0
        if diff_exchange_into_seeds:
            percentage_missing_exchange_into_seeds = len(diff_exchange_into_seeds)*100/len(exchange_set)
        else:
            percentage_missing_exchange_into_seeds = 0
  
        current_df = pd.DataFrame([[species_name, run, mode, optim, accu, model_name,
                      str(is_equal_union_species), diff_scope, percentage_missing,
                      str(is_biomass_included), diff_biomass, percentage_missing_biomass,
                      str(is_exchange_included), diff_exchange, percentage_missing_exchange,
                      str(is_seed_included_to_exchange), diff_seed_into_exchange, percentage_missing_exchange,
                      str(is_exchange_included_to_seeds), diff_exchange_into_seeds, percentage_missing_exchange_into_seeds]],
                      columns=['species','run', 'mode', 'optim', 'accu', 'model', 
                                'is_equal_union_species', 'missing', 'percentage_missing',
                                'is_biomass_included', 'missing_biomass', 'percentage_missing_biomass',
                                'is_exchange_included', 'missing_exchange', 'percentage_missing_exchange',
                                'is_seed_included_to_exchange', 'missing_seed_into_exchange', 'percentage_missing_seed_into_exchange',
                                'is_exchange_included_to_seed', 'missing_exchange_into_seed', 'percentage_missing_exchange_into_seeds'])
        current_df = current_df.astype(dtypes)

        comparison_scope_df = pd.concat([comparison_scope_df, current_df], ignore_index=True)



    # saving as tsv file 
    species_out_dir = os.path.dirname(species_scope_dir)
    comparison_file=os.path.join(species_out_dir, f"{species_name}_{modes_info}_compare.tsv")
    comparison_scope_df.to_csv(comparison_file, sep="\t") 
        