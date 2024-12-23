import sys
import json
import pathlib
import pandas as pd



def get_datas(directory, results):
    for filepath in directory.rglob('*_results.json'):
        # Opening JSON file
        result = open(filepath)
        # returns JSON object as
        # a dictionary
        data = json.load(result)
        organism = data['NETWORK']["NAME"]
        size = data['RESULTS']["Cobrapy"]['ENUMERATION']['solutions']['model_1'][1]
        time = data['RESULTS']["Cobrapy"]['ENUMERATION']['time']

        
        list_data = [[organism, time, size]]

        current_df = pd.DataFrame(list_data,
            columns=['network', 'time', 'size'])

        results=pd.concat([results, current_df], ignore_index=True)
        result.close()
    return results



if __name__ == '__main__':
    solutions_dir_path = sys.argv[1]
    result_dir_path = sys.argv[2]

    results = pd.DataFrame(columns=['network', 'time'])
    
    
    results_dir = pathlib.Path(solutions_dir_path)

    results = get_datas(results_dir, results)

    results.to_csv(f'{result_dir_path}/cobra_supp_data.tsv', index=True, sep ='\t')
    
    
    