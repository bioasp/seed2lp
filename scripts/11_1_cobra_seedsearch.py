from sys import argv
from os import path,makedirs
import cobra
import pandas
import json
from time import time

def seed_searching(sbml_file, target_file, objective_file, nb_solutions, output_dir):
    max_growth = 0.1

    species = f'{path.splitext(path.basename(sbml_file))[0]}'

    o_file = open(objective_file, "r") 
    objective = o_file.read()
    

    results=dict()
    solutions=dict()
    options=dict()
    net=dict()
    enumeration=dict()
    tool_enum=dict()
    tool_result=dict()

    options['REACTION'] = "All metabolite as exchange reaction"
    #Netseed or Precursor doesn't take into account the accumulation, by default its allowed
    options['ACCUMULATION'] = "NA"
    options['FLUX'] = "has flux (= 0,1)"
    results["OPTIONS"] = options

    net["NAME"] = species
    net["SEARCH_MODE"] = "Cobrapy"
    net["OBJECTIVE"] = [objective]
    net["SOLVE"] = "Cobrapy"
    results["NETWORK"] = net


    model=cobra.io.read_sbml_model(sbml_file)
    model.objective = objective.replace("R_","")


    # Get forbidden metabolites as seed from targets
    t_file = open(target_file, "r") 
    data = t_file.read() 
    targets_list = data.split("\n") 

    for meta in model.metabolites:
        if meta.compartment != "e":
            meta_name = str(meta).rsplit("_",1)[0]
            #simulate target are forbiden seeds
            if f"M_{str(meta)}" in targets_list:
                continue
            #simulate that all metabolite can be a seed
            meta_name_ex=f"{meta_name}_e"
            metabolite_exchange = cobra.Metabolite(id=meta_name_ex,name=meta_name_ex, compartment="e")
            model.add_metabolites([metabolite_exchange])
            reaction_name=f"EX_{meta_name_ex}"

            try:
                # create the exchange reaction
                model.add_boundary(metabolite=metabolite_exchange,
                                    type='exchange',
                                    ub=float(1000),
                                    lb=float(-1000))
                
                # add transport reaction for newly created exchange reaction
                id_transport_reaction = f"TR_{meta_name_ex}"
                reaction = cobra.Reaction(id_transport_reaction)
                reaction.lower_bound = -1000.
                reaction.upper_bound = 1000.
                reactant = metabolite_exchange
                procuct = meta
                reaction.add_metabolites({
                        reactant: -1.0,
                        procuct: 1.0
                    })
                model.add_reactions([reaction])
            except:
                # The reaction already exist
                # transport reaction not needed to be added
                reaction = model.reactions.get_by_id(reaction_name)
                if reaction.lower_bound > 0:
                    reaction.lower_bound = float(-1000)
                    reaction.upper_bound = float(1000)
                else:
                    reaction.upper_bound = float(1000)
                    reaction.lower_bound = float(-1000)

            
    # Find solutions by minimising the components
    # will give up to "nb_solutions" model into a dataframe 
    time_search = time()
    min_components = cobra.medium.minimal_medium(model, max_growth, minimize_components=nb_solutions)
    time_search = time() - time_search
    time_search=round(time_search, 3)
    # When return a serie, there is only one solution
    if type(min_components) == pandas.core.series.Series:
        seeds = list()
        for indx, _ in min_components.items():
            seeds.append(indx.replace("EX_", "M_", 1) )
        sol=[
                "size",
                len(seeds),
                "Set of seeds",
                seeds
            ]
        solutions["model_1"]=sol
    else :
        min_components = min_components.T
        min_components.columns = [c.replace("EX_", "M_", 1) for c in list(min_components.columns)]
        min_components = min_components.replace(0, None)

        #create the solutions in a seed2lp format
        solutions_df = min_components.notna().dot(min_components.columns+',').str.rstrip(',')
        for index,solu in solutions_df.items():
            seeds = solu.split(',')
            sol=[
                    "size",
                    len(seeds),
                    "Set of seeds",
                    seeds
                ]
            solutions[f"model_{index+1}"]=sol


    enumeration['solutions']=solutions
    enumeration['time']=time_search
    tool_enum['ENUMERATION']=enumeration

    tool_result["Cobrapy"]=tool_enum
    results['RESULTS']=tool_result

    #save results
    result_dir = path.join(output_dir,"seeds_results")
    if not path.isdir(result_dir):
        makedirs(result_dir)
    
    result_path = path.join(result_dir,f"{species}_results.json")
    with open(result_path, 'w') as f:
        json.dump(results, f, indent="\t")






if __name__ == '__main__':
    # User data
    sbml_file = argv[1]
    target_file = argv[2]
    objective_file = argv[3]
    output_dir=argv[4]
    nb_solutions=argv[5]

    seed_searching(sbml_file, target_file, objective_file, int(nb_solutions), output_dir)

    # check if targets are in scope, get time