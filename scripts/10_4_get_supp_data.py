import sys
import json
import pathlib
import pandas as pd
from seed2lp import sbml

def compute_union_intersection(data, mode, solve_mode, time_solve):
    list_solutions=list()
    if 'solutions' in data['RESULTS'][mode][solve_mode]:
        for solution in data['RESULTS'][mode][solve_mode]['solutions']:
            list_solutions.append(set(data['RESULTS'][mode][solve_mode]['solutions'][solution][3]))

    if list_solutions:
        intersection = int(len(set.intersection(*list_solutions)))
        union = int(len(set.union(*list_solutions)))
    else:
        if time_solve == "Time out" or time_solve =="time out":
            intersection = union = "Time out"
        else:
            intersection = union = "unsat"
    return intersection, union

def get_union_intersection(data, mode, solve_mode, time_solve, is_reasoning):
    if is_reasoning:
        if time_solve == "unsat":
            intersection = union = "unsat"
        else:
            intersection, union = compute_union_intersection(data, mode, solve_mode, time_solve)
    else:
        intersection, union = compute_union_intersection(data, mode, solve_mode, time_solve)
    return intersection, union



def get_datas(directory, sbml_path, modes_list, results, get_suffix:bool=True):
    for filepath in directory.rglob('*_results.json'):
        organism=filepath.parent.name
        # get total number of metabolite
        sbml_file = f'{sbml_path}/{organism}.xml'
        species_list=list()
        reaction_list=list()
        for specie in sbml.read_SBML_species(sbml_file)['Metabolites']:
            species_list.append(specie)
        for reaction in sbml.read_SBML_species(sbml_file)['Reactions']:
            reaction_list.append(reaction)
        total_number_metabolite = len(species_list)
        total_number_reaction = len(reaction_list)

        # Opening JSON file
        result = open(filepath)
        # returns JSON object as
        # a dictionary
        data = json.load(result)

        # SUBMIN data
        submin_solve = "unsat"
        submin_rejected = None
        submin_memory = None
        submin_intersection = "unsat"
        submin_union = "unsat"

        # MINIMIZE OPTIMUM data
        minimize_opti_solve = "unsat"
        minimize_opti_memory = None
        minimize_opti_rejected = None

        # MINIMIZE data
        minimize_solve = "unsat"
        minimize_rejected = None
        min_intersection = "unsat"
        min_union = "unsat"
        minimize_memory = None

        is_reasoning = False

        search_mode = data['NETWORK']['SEARCH_MODE']
        if data['OPTIONS']['ACCUMULATION'] == "Allowed":
            accumulation = True
        else:
            accumulation = False

        has_rejected=False
        for mode  in modes_list:
            if mode in data['RESULTS']:
                if get_suffix:
                    if 'GUESS-CHECK-DIVERSITY' in str(data['RESULTS'][mode]):
                        suffix=' GUESS-CHECK-DIVERSITY'
                        has_rejected = True
                    elif 'GUESS-CHECK' in str(data['RESULTS'][mode]):
                        suffix=' GUESS-CHECK'
                        has_rejected = True
                    elif 'FILTER' in str(data['RESULTS'][mode]):
                        suffix=' FILTER'
                        has_rejected = True
                    else:
                        suffix=''
                        is_reasoning=True
                else:
                    suffix=''
                    is_reasoning=True
                
                if 'Timer' in data['RESULTS'][mode][f'SUBSET MINIMAL ENUMERATION{suffix}']:
                    submin_solve = data['RESULTS'][mode][f'SUBSET MINIMAL ENUMERATION{suffix}']['Timer']['Solving time']
                submin_intersection, submin_union = get_union_intersection(data, mode, f'SUBSET MINIMAL ENUMERATION{suffix}',  submin_solve, is_reasoning)

                if 'rejected' in data['RESULTS'][mode][f'SUBSET MINIMAL ENUMERATION{suffix}']:
                    submin_rejected = data['RESULTS'][mode][f'SUBSET MINIMAL ENUMERATION{suffix}']['rejected']

                if "MINIMIZE OPTIMUM" in data['RESULTS'][mode]:
                    if 'Timer' in data['RESULTS'][mode][f'MINIMIZE OPTIMUM{suffix}']:
                        minimize_opti_solve = data['RESULTS'][mode][f'MINIMIZE OPTIMUM{suffix}']['Timer']['Solving time']
                    if has_rejected and 'rejected' in data['RESULTS'][mode][f'MINIMIZE OPTIMUM{suffix}']:
                        minimize_opti_rejected = data['RESULTS'][mode][f'MINIMIZE OPTIMUM{suffix}']['rejected']

                if mode == 'HYBRID':
                    submin_memory = data['RESULTS'][mode][f'SUBSET MINIMAL ENUMERATION']["Memory (GB)"]
                    minimize_opti_memory = data['RESULTS'][mode][f'MINIMIZE OPTIMUM']["Memory (GB)"]
                    

                if('MINIMIZE ENUMERATION' in data['RESULTS'][mode]):

                    if 'timer' in data['RESULTS'][mode][f'MINIMIZE ENUMERATION{suffix}']:
                        minimize_solve = data['RESULTS'][mode][f'MINIMIZE ENUMERATION{suffix}']['Timer']['Solving time']

                    min_intersection, min_union = get_union_intersection(data, mode, f'MINIMIZE ENUMERATION{suffix}', minimize_solve, is_reasoning)

                    if has_rejected and 'rejected' in data['RESULTS'][mode][f'MINIMIZE ENUMERATION{suffix}']:
                        minimize_rejected = data['RESULTS'][mode][f'MINIMIZE ENUMERATION{suffix}']['rejected']
                    if mode == 'HYBRID':
                        minimize_memory = data['RESULTS'][mode][f'MINIMIZE ENUMERATION{suffix}']["Memory (GB)"]
            
                list_data = [[organism, search_mode, f'{mode}{suffix}', accumulation, 'Solving (sec)',
                    submin_solve, minimize_opti_solve, minimize_solve, None, None],
                    [organism, search_mode, f'{mode}{suffix}', accumulation, 'Intersection',
                    submin_intersection, None, min_intersection, total_number_metabolite, total_number_reaction],
                    [organism, search_mode, f'{mode}{suffix}', accumulation, 'Union',
                    submin_union, None, min_union, total_number_metabolite, total_number_reaction]]
                
                if mode == 'HYBRID' or mode == 'FBA':
                    list_data.append([organism, search_mode, f'{mode}{suffix}', accumulation, 'Memory (GB)',
                    submin_memory, minimize_opti_memory, minimize_memory, None, None])
                
                if has_rejected:
                    list_data.append([organism, search_mode, f'{mode}{suffix}', accumulation, 'Rejected',
                    submin_rejected, minimize_opti_rejected, minimize_rejected, None, None])

                current_df = pd.DataFrame(list_data,
                    columns=['network', 'search_mode', 'mode', 'accumulation', 'type_data', 
                            'submin', 'minimize_opti', 'minimize', 'number_metabolites', 'number_reactions'])
                current_df['accumulation'] = current_df['accumulation'].astype('bool')

                results=pd.concat([results, current_df], ignore_index=True)
        result.close()
    return results



if __name__ == '__main__':
    solutions_dir_path = sys.argv[1]
    sbml_path = sys.argv[2]
    result_dir_path = sys.argv[3]
    prefix = sys.argv[4]

    results = pd.DataFrame(columns=['network', 'search_mode', 'mode', 'accumulation', 'type_data', 
                                    'submin', 'minimize_opti', 'minimize', 'number_metabolites', 'number_reactions'])
    
    results['accumulation'] = results['accumulation'].astype('bool')
    # search_mode:  Full network / Target
    # mode : REASONING / HYBRID /FBA
    # type_data: Grounding (sec) / Solving (sec)
    
    results_dir = pathlib.Path(solutions_dir_path)

    modes_list = ['REASONING']
    results = get_datas(results_dir, sbml_path, modes_list, results, True)


    results=results.set_index(['network', 'search_mode', 'mode'])

    results.to_csv(f'{result_dir_path}/{prefix}_supp_data.tsv', index=True, sep ='\t')
    
    
    