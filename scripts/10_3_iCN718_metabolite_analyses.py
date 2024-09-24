import os
from sys import argv
import pandas as pd
from seed2lp.file import load_json
from seed2lp import sbml


solve_dict={"reas": "",
            "fil": " FILTER",
            "gc": " GUESS-CHECK",
            "gcd": " GUESS-CHECK-DIVERSITY"}

if __name__ == '__main__':
    # User data
    results_dir = argv[1]
    sbml_file_path = argv[2]
    out_dir = argv[3]

    species_set = sbml.get_used_metabolites(sbml_file_path, False)


    df_count = pd.DataFrame(0,columns=["nb_reasoning", "nb_filter", "nb_gc", "nb_gcd"], index = list(species_set))

    for filename in os.listdir(results_dir):
        if "_results.json" in filename:
            #Before, when tested for paper, filenames had _log_ and not _reas_
            if "_reas_" in filename or "_log_" in filename:
                solve="reas"
                col="nb_reasoning"
            elif "_fil_" in filename:
                solve="fil"
                col="nb_filter"
            elif "_gc_" in filename:
                solve="gc"
                col="nb_gc"
            elif "_gcd_" in filename:
                solve="gcd"
                col="nb_gcd"
            result_path=os.path.join(results_dir, filename)
            data = load_json(result_path)
            solutions = data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{solve_dict[solve]}"]["solutions"]

            for sol in solutions:
                list_seed=solutions[sol][3]
                for seed in list_seed:
                    df_count.loc[seed,col] +=1

    df_count.to_csv(os.path.join(out_dir,"metabolites_occurences.tsv"), sep="\t")

