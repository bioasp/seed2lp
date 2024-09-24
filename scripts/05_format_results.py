from sys import argv
import json

if __name__ == '__main__':
    # User data
    tool_result_file = argv[1]
    species = argv[2]
    objective = argv[3]
    result_path = argv[4]
    tool = argv[5]
    
    if tool=="PRECURSOR":
        if "target" in tool_result_file:
            mode = "Precursor_tgt"
        else:
            mode = "Precursor_fn"
    else:
        mode = tool


    results=dict()
    options=dict()
    net=dict()
    enumeration=dict()
    tool_enum=dict()
    tool_result=dict()

    options['REACTION'] = "Remove Import Reaction"
    #Netseed or Precursor doesn't take into account the accumulation, by default its allowed
    options['ACCUMULATION'] = "Allowed"
    options['FLUX'] = "Maximization"
    results["OPTIONS"] = options

    net["NAME"] = species
    net["SEARCH_MODE"] = mode
    net["OBJECTIVE"] = [objective]
    net["SOLVE"] = tool
    results["NETWORK"] = net

    with open(tool_result_file, 'r') as j:
        net_solutions = json.loads(j.read())

    if tool=="NETSEED":
        del net_solutions['netseed']['solutions']['union']
    
    tool.lower()
    solutions = {f"model_{key}": val for key, val in net_solutions[tool.lower()]['solutions'].items()}
    for key,val in solutions.items():
        sol=[
                "size",
                len(val),
                "Set of seeds",
                val
            ]
        solutions[key]=sol


    enumeration['solutions']=solutions
    tool_enum['ENUMERATION']=enumeration

    tool_result[tool]=tool_enum
    results['RESULTS']=tool_result


    with open(result_path, 'w') as f:
        json.dump(results, f, indent="\t")
