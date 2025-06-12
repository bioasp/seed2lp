import os
from sys import argv
from seed2lp.file import load_json, save

   
community_dict={"com_BiGG_2_2": None,
          "com_BiGG_2_3": None,
          "com_BiGG_2_4": None,
          "com_BiGG_4_3": None,
}

empty_dict={"reas": None,
            "fil": None,
            "fil_equality_flux": None,
            "gc": None,
            "gcd": None
            }

solve_dict={"reas": "",
            "fil": " FILTER",
            "fil_equality_flux": " FILTER",
            "gc": " GUESS-CHECK",
            "gcd": " GUESS-CHECK-DIVERSITY"
            }

dict_nb={'nb_solution':None,
         'nb_rejected':None,
         'timer':None,
         }

com_mode={"global":None,
          "bisteps":None,
          "delsupset":None,
          "bisteps_extended":None,
          "delsupset_extended":None
          }


def get_data_solution(data:dict, key_solve:str, key_com:str, key_com_mode:str):
    print(key_solve)
    solutions = data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{solve_dict[key_solve]}"]["solutions"]
    community_dict[key_com]['nb_solution'][key_com_mode][key_solve]=len(solutions)
    community_dict[key_com]['timer'][key_com_mode][key_solve]=data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{solve_dict[key_solve]}"]["Timer"]

    if key_solve != "reas" and "rejected" in data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{solve_dict[key_solve]}"]:
        community_dict[key_com]['nb_rejected'][key_com_mode][key_solve] = data["RESULTS"]["REASONING"][f"SUBSET MINIMAL ENUMERATION{solve_dict[key_solve]}"]["rejected"]

def compute_solution(solutions_dir, filename, community, comunity_mode, is_all_mode, solve_key):
    result_path=os.path.join(solutions_dir, filename)
    data = load_json(result_path)

    print(f"Starting: {community}, {comunity_mode}")
    if not is_all_mode:
        get_data_solution(data, solve_key, community, comunity_mode)

    else:
        for solve_key in solve_dict:
            get_data_solution(data, solve_key, community, comunity_mode)

if __name__ == '__main__':
    # User data
    solutions_dir = argv[1]
    solutions_dir_equality_flux = argv[2]
    result_dir = argv[3]
    
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    for com_key in community_dict:
        community_dict[com_key]=dict_nb.copy()
        community_dict[com_key]['nb_solution']=com_mode.copy()
        community_dict[com_key]['nb_rejected']=com_mode.copy()
        community_dict[com_key]['timer']=com_mode.copy()
        for com_mode_key in com_mode:
            community_dict[com_key]['nb_solution'][com_mode_key]=empty_dict.copy()
            community_dict[com_key]['nb_rejected'][com_mode_key]=empty_dict.copy()
            community_dict[com_key]['timer'][com_mode_key]=empty_dict.copy()


    for filename in os.listdir(solutions_dir):
        is_all_mode=False
        if "_results.json" in filename:
            #Before, when tested for paper, filenames had _log_ and not _reas_
            if "_reas_" in filename or "_log_" in filename:
                solve_key="reas"
            elif "_fil_" in filename:
                if solutions_dir_equality_flux != "NA":
                    solve_key="fil_equality_flux"
                else:
                    solve_key="fil"
            elif "_gc_" in filename:
                solve_key="gc"
            elif "_gcd_" in filename:
                solve_key="gcd"
            else:
                is_all_mode = True

            if "extend_transf" in filename:
                is_extended = True
            else:
                is_extended = False

            for com_key in community_dict:
                if com_key in filename:
                    community = com_key
                    break
            for com_mode_key in com_mode:
                if is_extended:
                    if com_mode_key == "bisteps" or com_mode_key == "delsupset":
                        continue
                    elif com_mode_key == "bisteps_extended" or com_mode_key == "delsupset_extended":
                        com_mode_key_file = com_mode_key.replace('_extended', '')
                        if com_mode_key_file in filename:
                            comunity_mode = com_mode_key
                            compute_solution(solutions_dir, filename, community, 
                                             comunity_mode, is_all_mode, solve_key)
                else:
                    if com_mode_key == "global" or com_mode_key == "bisteps" or com_mode_key == "delsupset":
                        if com_mode_key in filename:
                            comunity_mode = com_mode_key
                            compute_solution(solutions_dir, filename, community, 
                                             comunity_mode, is_all_mode, solve_key)
                    elif com_mode_key == "bisteps_extended" or com_mode_key == "delsupset_extended":
                        continue
    if solutions_dir_equality_flux != "NA":
        for filename in os.listdir(solutions_dir_equality_flux):
            is_all_mode=False
            if "_results.json" in filename:
                solve_key="fil_equality_flux"
                
                for com_key in community_dict:
                    if com_key in filename:
                        community = com_key
                        break
                for com_mode_key in com_mode:
                    if com_mode_key in filename:
                        comunity_mode = com_mode_key
                        compute_solution(solutions_dir, filename, community, 
                                            comunity_mode, is_all_mode, solve_key)
            
        

    save("data_solution_bigg_com",result_dir,community_dict,"json")
