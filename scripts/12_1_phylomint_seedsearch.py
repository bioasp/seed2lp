#!/usr/bin/env python3
from libsbml import readSBML
import networkx as nx
from sys import argv
from os import path, makedirs
import json
from time import time

###################################################
#################### PHYLOMINT ####################
###################################################
# This part of code is an extract of phylomint 
# except for duplicate boole option and the duplication
# of reversible reactions
def buildDG(sbml, duplicate:bool=False, only_rev:bool=False):
    '''
    Usage: reads SBML file, parses reaction and product list
    Returns: networkx directed graph
    '''

    # initate empty directed graph
    DG = nx.DiGraph()

    document = readSBML(sbml)
    model = document.getModel()

    # get reactions
    rxn = (model.getListOfReactions())

    # get reaction and product and construct directed graph
    for r in rxn:
        react = [i.getSpecies() for i in r.getListOfReactants()]
        prod = [j.getSpecies() for j in r.getListOfProducts()]
        for rt in react:
            for p in prod:
                DG.add_edge(rt,p)
        

        ###################################################
        ################### ADDED CODE ####################
        ###################################################
        # Add a reverse reaction into graph (NOT from initial code)
        # because we used the normalized sbml, we can refer to reversible
        if duplicate or (only_rev and r.reversible):
            react = [i.getSpecies() for i in r.getListOfProducts()]
            prod = [j.getSpecies() for j in r.getListOfReactants()]
            for rt in react:
                for p in prod:
                    DG.add_edge(rt,p)
        ###################################################

    return DG

def getSeedSet(DG, maxComponentSize = 5):
    '''
    Usage: takes input networkX directed graph
    Returns: SeedSet dictionary{seedset:confidence score}
    Implementation follows literature description, 
    Improves upon NetCooperate module implementation which erroneously discards certian cases of SCCs (where a smaller potential SCC lies within a larger SCC)
    '''

    # get SCC
    SCC = nx.strongly_connected_components(DG)

    SeedSetConfidence = dict()

    for cc in SCC:
        # convert set to list
        cc_temp = list(cc)

        # filter out CC larger than threshold
        if len(cc_temp) > maxComponentSize:
            continue

        # check single element SCC
        elif len(cc_temp) == 1:
            if DG.in_degree(cc_temp[0]) == 0:
                SeedSetConfidence[cc_temp[0]] = 1.0    

        # check 2 to max threshold SCC
        else:
            #check if no out nodes
            for node in cc_temp:
                # check every edge of SCC
                for edge in DG.in_edges(node):
                    # if SCC is not self contained, then it is not considered seed set
                    if edge[0] not in cc_temp:
                        cc_temp = []
            for node in cc_temp:
                SeedSetConfidence[node] = 1/len(cc_temp) 
    
    SeedSet = SeedSetConfidence.keys()

    nonSeedSet = list(set(DG.nodes()) - set(SeedSet))

    return(SeedSetConfidence, SeedSet, nonSeedSet)

###################################################
###################################################



def write_into_json_file(seeds, objective,time_search,duplicate:bool=False,only_rev:bool=False):
    results=dict()
    solutions=dict()
    options=dict()
    net=dict()
    enumeration=dict()
    tool_enum=dict()
    tool_result=dict()
    sol=dict()
    

    options['REACTION'] = "Remove Import Reaction"
    #Netseed or Precursor doesn't take into account the accumulation, by default its allowed
    options['ACCUMULATION'] = "Allowed"
    options['FLUX'] = "NA"
    results["OPTIONS"] = options

    net["NAME"] = species
    net["SEARCH_MODE"] = "Phylomint"
    net["OBJECTIVE"] = [objective]
    net["SOLVE"] = "Phylomint"
    results["NETWORK"] = net
    sol=[
                    "size",
                    len(seeds),
                    "Set of seeds",
                    seeds
                ]
    solutions[f"model_1"]=sol


    enumeration['solutions']=solutions
    enumeration['time']=time_search
    tool_enum['MINIMIZE ENUMERATION']=enumeration

    tool_result["Phylomint"]=tool_enum
    results['RESULTS']=tool_result


    supp=""
    if duplicate:
        supp="_duplicate"
    if only_rev:
        supp="_duplicate_rev"
    #save results
    result_dir = path.join(f"{output_dir}{supp}","seeds_results")
    if not path.isdir(result_dir):
        makedirs(result_dir)
        
    result_path = path.join(f"{result_dir}",f"{species}{supp}_results.json")
    with open(result_path, 'w') as f:
        json.dump(results, f, indent="\t")



def export_dg(DG, species, output_dir, duplicate:bool=False,only_rev:bool=False):
    pos = nx.nx_agraph.graphviz_layout(DG)
    nx.draw(DG, pos=pos)
    file_name = species
    if duplicate:
        file_name += "_duplicate"
    if only_rev:
        file_name += "_duplicate_rev"
    file_name += ".dot"
    nx.drawing.nx_pydot.write_dot(DG, path.join(output_dir,file_name))



if __name__ == '__main__':
    sbml_file = argv[1]
    objective_file = argv[2]
    output_dir = argv[3]

    species = f'{path.splitext(path.basename(sbml_file))[0]}'
    
    ########### PHYLOMINT ###########
    DG=buildDG(sbml_file)
    #DG_duplicate=buildDG(sbml_file, True, False)
    DG_duplicate_rev=buildDG(sbml_file, False, True)

    # export DG en .dot et pareil pour netseed et voir difference
    #export_dg(DG, species, output_dir)
    #export_dg(DG_duplicate, species, output_dir, True)

    # Calculate the seed sets
    # maxComponentSize : Maximum number of nodes in a strongly connected component (SCC) to consider in SeedSet. (default = 5)
    time_search = time()
    _, SeedSet, _ = getSeedSet(DG, maxComponentSize=5)
    time_search = time() - time_search
    time_search=round(time_search, 3)

    #time_search_duplicate = time()
    #_, SeedSet_duplicate, _ = getSeedSet(DG_duplicate, maxComponentSize=5)
    #time_search_duplicate = time() - time_search_duplicate
    #time_search_duplicate=round(time_search_duplicate, 3)

    time_search_duplicate_rev = time()
    _, SeedSet_duplicate_rev, _ = getSeedSet(DG_duplicate_rev, maxComponentSize=5)
    time_search_duplicate_rev = time() - time_search_duplicate_rev
    time_search_duplicate_rev=round(time_search_duplicate_rev, 3)
    #################################

    
    o_file = open(objective_file, "r") 
    objective = o_file.read()
    write_into_json_file(list(SeedSet), objective, time_search)
    #write_into_json_file(list(SeedSet_duplicate), objective, time_search_duplicate, True, False)
    write_into_json_file(list(SeedSet_duplicate_rev), objective, time_search_duplicate_rev, False, True)

