import os
from sys import argv
import pandas as pd
from seed2lp.file import load_json
from seed2lp import sbml


solve_dict={"reas": "",
            "fil": " FILTER",
            "gc": " GUESS-CHECK",
            "gcd": " GUESS-CHECK-DIVERSITY"
            }

species_dict={"e_coli_core_no_g6p": None,
            "e_coli_core_no_gln__L": None,
            #"e_coli_core_no_g3p": None
            }

col_seed_dict={"reas": "nb_seed_reasoning",
            "fil": "nb_seed_filter",
            "gc": "nb_seed_gc",
            "gcd": "nb_seed_gcd"
            }

col_transf_dict={"reas": "nb_transf_reasoning",
            "fil": "nb_transf_filter",
            "gc": "nb_transf_gc",
            "gcd": "nb_transf_gcd"
            }

com_mode={"global":None,
          "bisteps":None,
          "delsupset":None}

def count_meta(df_count:pd.DataFrame, solutions:list, key:str, com_mode_key:str):
    print("Starting counts")
    if key == "reas":
        print("REASONING")
    else:
        print(solve_dict[key])
    nb_sol = 0
    for sol in solutions:
        if nb_sol %50000 == 0 and nb_sol !=0:
            print(nb_sol)
        list_transf=None
        list_transf_done=list()
        list_seed=solutions[sol][3]
        list_transf=solutions[sol][5]
        for seed in list_seed:
            for species,_ in species_dict.items():
                if species in seed:
                    df_count.loc[(seed.replace(f"_{species}",""),species,com_mode_key),col_seed_dict[key]] +=1
        if list_transf:
            for transf in list_transf:
                if transf["Metabolite"] not in list_transf_done:
                    list_transf_done.append(transf["Metabolite"])
                    df_count.loc[(transf["Metabolite"], transf["From"],com_mode_key),col_transf_dict[key]] +=1
        nb_sol +=1
    return df_count

if __name__ == '__main__':
    # User data
    results_dir = argv[1]
    sbml_file_path = argv[2]
    out_dir = argv[3]
    com_name = argv[4]

    metabolite_set = sbml.get_used_metabolites(sbml_file_path)

    multi_index = pd.MultiIndex.from_product([list(metabolite_set),
                                        list(species_dict.keys()),
                                        list(com_mode.keys())],
                                   names=['metabolite', 'species', 'com_mode'])

    df_count = pd.DataFrame(0,columns=[col_seed_dict["reas"], col_seed_dict["fil"], 
                                       col_seed_dict["gc"], col_seed_dict["gcd"],
                                       col_transf_dict["reas"], col_transf_dict["fil"], 
                                       col_transf_dict["gc"], col_transf_dict["gcd"]],
                                        index = multi_index)
    for filename in os.listdir(results_dir):
        if "_results.json" in filename and (com_name in filename or not com_name):
            is_all_mode = False
            #Before, when tested for paper, filenames had _log_ and not _reas_
            if "_reas_" in filename or "_log_" in filename:
                key="reas"
            elif "_fil_" in filename:
                key="fil"
            elif "_gc_" in filename:
                key="gc"
            elif "_gcd_" in filename:
                key="gcd"
            else:
                is_all_mode = True
            result_path=os.path.join(results_dir, filename)
            data = load_json(result_path)

            for com_mode_key in com_mode:
                if com_mode_key in filename:
                    comunity_mode = com_mode_key
                    
            if not is_all_mode:
                solutions = data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{solve_dict[key]}"]["solutions"]
                df_count = count_meta(df_count, solutions, key, comunity_mode)

            else:
                for key, val in solve_dict.items():
                    solutions = data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{val}"]["solutions"]
                    df_count = count_meta(df_count, solutions, key, comunity_mode)
    prefix=""
    if com_name:
        prefix = f"{com_name}_"
    df_count.to_csv(os.path.join(out_dir,f"{prefix}metabolites_occurences.tsv"), sep="\t")

# python 13_1_com_e_coli_core_metabolite_analyses.py ../results/e_coli_core/results ../networks/communities/xml/e_coli_core.xml ../results/e_coli_core