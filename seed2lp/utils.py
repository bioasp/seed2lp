"""Utilitaries"""
import os
import clyngor
import re
from re import findall
from . import logger
from csv import reader


def solve(*args, **kwargs):
    "Wrapper around clyngor.solve"
    kwargs.setdefault('use_clingo_module', False)
    try:
        return clyngor.solve(*args, **kwargs)
    except FileNotFoundError as err:
        if 'clingo' in err.filename:
            logger.log.error('Binary file clingo is not accessible in the PATH.')
            exit(1)
        else:  raise err


def get_ids_from_file(fname:str, asp_atome_type:str=None) -> [str]:
    """Get metabolites id from seeds file, forbidden seeds file or possible seeds file

    Args:
        fname (str): file path
        asp_atome_type (str, optional): Type of atome for facts. Defaults to None.

    Raises:
        NotImplementedError: Target file of extension [ext] not implemented

    Returns:
        [str]: List of metabolite
    """
    "Yield identifiers of seeds/targets/metabolites found in given sbml or text or lp file"
    metabolit_list = list()
    ext = os.path.splitext(fname)[1]
    #if ext in {'.sbml', '.xml'}:  # sbml data
    #    from .sbml import read_SBML_species
    #    yield from read_SBML_species(fname)
    if ext in {'.lp'}:  # ASP data
        for model in solve(fname).by_arity:
            for line, in model.get(f'{asp_atome_type}/1', ()):
                line = unquoted(line)
                if re.search("^M_*",line):
                    metabolit_list.append(line) 
                else:
                    metabolit_list.append(f'M_{line}') 
    elif ext in {'.txt', ''}:  # file, one line per metabolite
        with open(fname) as fd:
            for line in map(str.strip, fd):
                if line:
                    if re.search("^M_*",line):
                        metabolit_list.append(line) 
                    else:
                        metabolit_list.append(f'M_{line}') 
    else:
        raise NotImplementedError(f"Target file of ext {ext}: {fname}")
    return metabolit_list
    
    
def get_targets_from_file(fname:str, is_community:bool):
    """Get metabolites id or reactions id from target file

    Args:
        fname (str): Target file path
        is_community (bool): Community mode

    Raises:
        ValueError: The element [element] misses prefix M_ or R_"
        NotImplementedError: The [file name] extension has to be ".txt". 
        ValueError: Multiple objective reaction found

    Returns:
        [str],[str]: List of target and list of objective reaction
    """
    target_list=dict()
    objective_reaction_list = list()
    ext = os.path.splitext(fname)[1]
    if ext in {'.txt',  ".csv",''}:  # file, one line per metabolite
        # file = open(fname)
        # tgts = reader(file, delimiter='\t')
        with open(fname, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue  # ignore empty line
                data = re.split(r"[ \t]+", line)

                obj_id=data[0]
                if is_community:
                    if len(data)==2:
                        species=data[1]
                    else:
                        raise ValueError(f"invalid data, needs 2 elements (metabolite or reaction / species):\n {line}")
                else:
                    if len(data)==1:
                        species=""
                    else:
                        raise ValueError(f"invalid data, needs 1 element (metabolite or reaction):\n {line}")

                if re.search("^M_*",line):
                    prefixed_id=prefix_id_network(is_community, obj_id, species, "metabolite")
                    if obj_id in target_list:
                        target_list[obj_id].append(prefixed_id)
                    else:
                        target_list[obj_id]=[prefixed_id]
                    #target_list.append(line)
                elif re.search("^R_*",line):
                    objective_reaction_list.append([species, obj_id])
                else:
                    raise ValueError(f"\n{fname} : The element {line} misses prefix M_ or R_")
    else:
        raise NotImplementedError(f'\nThe {fname} extension has to be ".txt". Given: {ext}')
    
    if len(objective_reaction_list) >1 and not is_community:
        raise ValueError(f"\nMultiple objective reaction found in {fname}\n")
    elif is_community:
        no_duplicates = len({x[0] for x in objective_reaction_list}) == len(objective_reaction_list)
        if not no_duplicates:
            raise ValueError(f"\nMultiple objective reaction found in {fname} for same species\n")


    
    return target_list, objective_reaction_list


def quoted(string:str) -> str:
    r"""Return string, double quoted

    >>> quoted('"a').replace('\\', '$')
    '"$"a"'
    >>> quoted('"a b"').replace('\\', '$')
    '"a b"'
    >>> quoted('a b').replace('\\', '$')
    '"a b"'
    >>> quoted('a\\"').replace('\\', '$')
    '"a$""'
    >>> quoted('a"').replace('\\', '$')
    '"a$""'
    >>> quoted('\\"a"').replace('\\', '$')
    '"$"a$""'
    >>> quoted('"').replace('\\', '$')
    '"$""'

    """
    if len(string) > 1 and string[0] == '"' and string[-2] != '\\' and string[-1] == '"':
        return string
    else:
        return '"' + string.replace('\\"', '"').replace('"', '\\"') + '"'


def unquoted(string:str) -> str:
    r"""Remove surrounding double quotes if they are acting as such

    >>> unquoted('"a').replace('\\', '$')
    '$"a'
    >>> unquoted('"a b"')
    'a b'
    >>> unquoted('b"').replace('\\', '$')
    'b$"'
    >>> unquoted('"b\\"').replace('\\', '$')
    '$"b$"'

    """
    if string[0] == '"' and string[-2] != '\\' and string[-1] == '"':
        return string[1:-1]
    else:
        return string.replace('\\"', '"').replace('"', '\\"')


def quoted_data(asp:str) -> str:
    "Return the same atoms as found in given asp code, but with all arguments quoted"
    def gen():
        for model in clyngor.solve(inline=asp):
            for pred, args in model:
                yield f'{pred}(' + ','.join(quoted(str(arg)) for arg in args) + ').'
    return ' '.join(gen())


def repair_json(json_str:str, is_clingo_lpx:bool=False):
    """Function to add closing ] or } to the json after the process has been killed
    delete also the last element of the json which can be not finished

    Args:
        proc_output (str): process output

    Returns:
        str: complete output on json format
    """
    close = {'{': '}', 
             '[': ']'}
    if is_clingo_lpx:
        output = json_str.rsplit('{', 1)[0]
        output = output.rsplit(',', 1)[0]
    else:
        output = json_str.rsplit('\"model', 1)[0]
    # get the list of caracter "{" "[" "]" "}" in the order of apparition 
    list_open_close=findall("{|\[|\]|}", output)
    missing_list=list()
    for car in list_open_close:
        size=len(missing_list)
        # delete the opening element when the closing element  appear right after
        if size!= 0 and ((missing_list[size -1] == "{" and car == "}") 
            or (missing_list[size -1] == "[" and car == "]")):
            missing_list.pop(size -1)
        else:
            missing_list.append(car)
    close_str=""
    for i, open in reversed(list(enumerate(missing_list))):
        close_str += "\n" + i * "\t" + close[open]
    logger.log.warning("Output not totally recovered. Json has been repaired but might miss results")
    return output+close_str

def prefix_id_network(is_community:bool, name:str, species:str="", type_element:str=""):
        """Prefix Reaction or Metbolite by the network name (filename) if the tool is used for community.
        For single network, nothing is prefixed.

        Args:
            name (str): ID of the element
            species (str, optional): Network name (from filename). Defaults to "".
            type_element: (str, optional): "reaction" or "metabolite" or no type. Defaults to "".

        Returns:
            str: The name prfixed by the network if needed
        """
        match is_community, type_element:
            case True,"reaction":
                return re.sub("^R_", f"R_{species}_",name)
            case True,"metabolite":
                return re.sub("^M_", f"M_{species}_",name)
            case True,"metaid":
                return re.sub("^meta_R_", f"meta_R_{species}_",name)
            case True,_:
                return f"{species}_{name}"
            case _,_:
                return name