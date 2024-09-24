"""
Clingo lpx functions for launching command and extract results.
"""

import subprocess 
import json
from resource import getrusage, RUSAGE_CHILDREN
from .utils import repair_json
from . import logger, color


def command(files:list, options:list, nb_model:int=0, time_limit:int=0) -> iter:
    """Create the Clingo-lpx command to run for solving

    Args:
        files (list): List of ASP files used for sovling.
        options (list): Clingo options
        nb_model (int, optional): Limit number of solutions to find. Defaults to 0 meaning unlimited.
        time_limit (int, optional): Time limit given by user in minutes. Defaults to 0 meaning unlimited.

    Raises:
        ValueError: If the number of model is negative, the command is not correct

    Returns:
        iter: Composition of the command to run
    """

    CMD = ['python', '-m', 'clingolpx']
    options = list(filter(None, options))

    if time_limit:
        time_limit = int(time_limit)
        options.append(f'--time-limit={str(time_limit)}')
    if nb_model:
        nb_model = int(nb_model)
        if nb_model < 0:
            raise ValueError("Number of model must be >= 0.")
        options.append(f'-n {str(nb_model)}')
    else:
        options.append(f'-n 0')

    options.append("--warn=none")

    if files:
        cmd = [*CMD, *files, *options]
    else:
        cmd = [*CMD, *options]

    return cmd


def solve(cmd:list, time_limit:int):
    """Launch the Clingo-lpx command

    Args:
        cmd (list): Clingo-lpx command
        time_limit (int): Time limit given by user in minutes.

    Returns:
        proc_output (str), err_output (str), error_code (int), memory (float), is_killed (bool)
    """
    
    cmd.append(f'--outf=2')
    is_killed=False
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if time_limit:
            process.wait(timeout=time_limit+60)
    except subprocess.TimeoutExpired:
        logger.log.error(f'Timeout: {time_limit/60} min expired')
        process.kill()
        process.wait()
        is_killed=True

    proc_output, err_output = process.communicate()
    memory=getrusage(RUSAGE_CHILDREN).ru_maxrss / (1024 * 1024)
    error_code=process.returncode
    if is_killed:
        error_code=0
    if error_code==1:
        logger.log.error(f'Timeout: {time_limit/60} min expired')
    return str(proc_output, 'UTF-8'), err_output, error_code, round(memory,3), is_killed



def result_convert(proc_output:str, objectives:list=None, enum_mode:str="", 
                   is_killed:bool=False, to_print:bool=True):
    """Convert the output result into constructed and limited output (JSON type)

    Args:
        proc_output (str):  Output from the solver
        objectives (list, optional):  List of objective reactions to show on output. Defaults to None.
        enum_mode (str, optional): Enumeration mode to detect intersection or enumeration. Defaults to "".
        is_killed (bool, optional): Detects if the process was killed. Defaults to False.
        to_print (bool, optional): Print the solution into consol. Defaults to True.

    Returns:
        result (dict), unsatisfiable (bool), has_optimum (bool), time (dict), costs (list)
    """
    result={}
    seed_accu={}
    time={}
    has_optimum = False
    unsatisfiable = True
    model_number=1
    seeds_list=list()
    reaction_list=list()
    costs=None
    if proc_output:
        if is_killed:
            proc_output=repair_json(proc_output, True)
        result_data = json.loads(proc_output)

        if 'Result' in result_data:
            if result_data['Result'] == 'SATISFIABLE':
                unsatisfiable = False
            if result_data['Result'] == 'OPTIMUM FOUND':
                has_optimum = True
                unsatisfiable = False
        elif enum_mode=="domRec":
            unsatisfiable = False
        if 'Time' in result_data:
            time = result_data['Time']
        
        if 'Call' in result_data:
            if 'Witnesses' in result_data['Call'][0]:
                #Case minimize finding optimum or case intersection
                if (has_optimum and enum_mode != "enumeration") or enum_mode == "cautious":
                    model = result_data['Call'][0]['Witnesses'][-1]
                    reaction_list, seeds_list, objective_str, seeds_accu_list = \
                            get_model_data(model, objectives)
                    nb_seed=len(seeds_list)
                    nb_seed_accu=len(seeds_accu_list)
                    result[f'model_{model_number}']=["size", nb_seed] + \
                                            ["Set of seeds", seeds_list.copy()] + \
                                            ['reaction_flux', reaction_list.copy()] 
                    if nb_seed_accu or nb_seed_accu>0:
                        seed_accu["size"] = nb_seed_accu
                        seed_accu["Set of seeds"] = seeds_accu_list.copy()
                        result[f'model_{model_number}']=result[f'model_{model_number}'] +\
                                                                ["accumulation avoid with seeds", seed_accu]
                    if "Costs" in model:
                        costs = model["Costs"]
                    if to_print:
                        print_data(model_number, objective_str, seeds_list, seeds_accu_list)
                elif not unsatisfiable:
                    for model in result_data['Call'][0]['Witnesses']:
                        reaction_list, seeds_list, objective_str, seeds_accu_list = \
                            get_model_data(model, objectives)
                        nb_seed=len(seeds_list)
                        nb_seed_accu=len(seeds_accu_list)
                        print_data(model_number, objective_str, seeds_list, seeds_accu_list)
                        result[f'model_{model_number}']=["size", nb_seed] + \
                                                ["Set of seeds", seeds_list.copy()] + \
                                                ['reaction_flux', reaction_list.copy()] 
                        if nb_seed_accu or nb_seed_accu>0:
                            seed_accu["size"] = nb_seed_accu
                            seed_accu["Set of seeds"] = seeds_accu_list.copy()
                            result[f'model_{model_number}']=result[f'model_{model_number}'] +\
                                                                    ["accumulation avoid with seeds", seed_accu]
                        model_number+=1

    return result, unsatisfiable, has_optimum, time, costs


def get_model_data(model:dict, objectives:list=None):
    """Get clingo results and convert into lists

    Args:
        model (dict): output of clingo
        objectives (list, optional): List of objective reactions to show on output. Defaults to None.

    Returns:
        reaction_list (list), seeds_list (list), objective_str (str), seeds_accu_list (list)
    """
    objective_str=''
    reaction_list=list()
    seeds_list=list()
    seeds_accu_list=list()
    for answer in model['Value']:
        if 'seed("' in answer:
            seed=answer.replace('seed("','',1).replace('")','',1)
            seed=seed.split(',')[0].replace('"','',2)
            seeds_list.append(seed)
        elif 'seed_accu(' in answer:
            seed_accu=answer.replace('seed_accu("','',1).replace('")','',1)
            seed_accu=seed_accu.split(',')[0].replace('"','',2)
            seeds_accu_list.append(seed_accu)
        else:
            answer = answer.replace('__lpx(','',1).replace(')','',1)
            reaction = answer.split(',')[0].replace('"','',2)
            flux = answer.split(',')[1].replace('"','',2).replace(')','',1)
            if '/' in flux:
                numerator=int(flux.split('/')[0])
                denominator=int(flux.split('/')[1])
                flux=round(float(numerator/denominator),10)
            else:
                flux=round(float(flux),10)
            if reaction in objectives:
                objective_str+=f'"{reaction}" = {flux}\n'
            reaction_list.append((reaction,flux))
    
    seeds_list=list(sorted(seeds_list))
    seeds_accu_list=list(sorted(seeds_accu_list))
    return reaction_list, seeds_list, objective_str, seeds_accu_list

def print_data(model_number:int, objective_str:str, seeds_list:list, 
               seeds_accu_list:list):
    """Data written into terminal

    Args:
        model_number (int): name of the solution
        objective_str (str): Reaction name and flux
        seeds_list (list): Seeds list 
        seeds_accu_list (list): Seeds used for accumulation list 
    """
    plural_seed=""
    plural_accu=""
    nb_seed = len(seeds_list)
    nb_seed_accu = len(seeds_accu_list)
    if nb_seed>=2:
        plural_seed="s"
    if nb_seed_accu>=2:
        plural_accu="s"
    #is_accu = seeds_accu_str or seeds_accu_str != ""
    print(f"Answer: {model_number} ({nb_seed} seed{plural_seed}) ")
    seeds_str = ', '.join(map(str, seeds_list))
    print(seeds_str)
    if nb_seed_accu > 0:
        seeds_accu_str = ', '.join(map(str, seeds_accu_list))
        print(f"{color.red_bright} Seed{plural_accu} for which export reaction \navoids accumulation ({nb_seed_accu} seed{plural_accu})")
        print(seeds_accu_str+color.reset)
    print('Assignment:')
    print(objective_str)
  