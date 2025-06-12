#!/usr/bin/env python3
from libsbml import readSBML
import networkx as nx
from sys import argv
from json import dump
from os import path, makedirs
import re



def buildDG(sbml):
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
        
        if r.reversible:
            react = [i.getSpecies() for i in r.getListOfProducts()]
            prod = [j.getSpecies() for j in r.getListOfReactants()]
            for rt in react:
                for p in prod:
                    DG.add_edge(rt,p)
        ###################################################

    return DG



def get_degree(DG:nx.DiGraph, is_ecoli_complete:bool):
    if is_ecoli_complete:
        species_dict={
                  "e_coli_core":[]
                  }
        
    else:
        species_dict={
                  "e_coli_core_no_g6p":[],
                  "e_coli_core_no_gln__L":[],
                  "e_coli_core_no_g3p":[]
                  }
    for node, degree in DG.degree():
        for key, val in species_dict.items():
            if is_ecoli_complete:
                 species_dict["e_coli_core"].append([node, degree])
            elif  key in node:
                species_dict[key].append([node.replace(f'_{key}',''), degree])
            

    for key, val in species_dict.items():
        val = sorted(val, key=lambda x: x[1], reverse=True)  
        species_dict[key]=val

    return species_dict

    


if __name__ == '__main__':
    sbml_file = argv[1]
    output_dir = argv[2]

    #sbml_file = "../results/e_coli_core/tmp_com_e_coli_core_2_1_global_all_taf.xml"
    
    if "e_coli_core.xml" in sbml_file:
        file_name = "e_coli_core"
        is_ecoli_complete=True
    else:
        com_name_group = re.search('com_(.*).xml', sbml_file)
        file_name=com_name_group.group(1)
        is_ecoli_complete=False

    DG=buildDG(sbml_file)

    dict_degree = get_degree(DG, is_ecoli_complete)

    #save results
    if not path.isdir(output_dir):
        makedirs(output_dir)
    
    result_path = path.join(output_dir,f"{file_name}_degree.json")
    with open(result_path, 'w') as f:
        dump(dict_degree, f, indent="\t")
   
# python 13_0_get_degree_node.py ../results/e_coli_core/tmp_com_e_coli_core_2_1_global_all_taf.xml ../results/e_coli_core/