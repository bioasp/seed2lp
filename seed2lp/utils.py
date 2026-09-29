"""Utilitaries"""
import os
import clyngor
import re
from re import findall
#from . import logger
from csv import reader


_pattern_from_sbml = re.compile(r"__(\d+)__")
_pattern_compartment_bracket = re.compile(r"__91__[A-Za-z0-9]+__93__$")


def metabolite_root_id(meta_id: str) -> str:
    """Strip a trailing compartment tag, to compare the same metabolite across compartments.

    Two compartment-suffix conventions are found in SBML files: BiGG-style,
    an underscore-separated suffix (e.g. "glc_c" for cytosolic glucose), and
    ModelSEED/AGORA-style, an SBML-encoded bracket suffix (e.g.
    "1odecg3p__91__c__93__", i.e. "1odecg3p[c]" once decoded). The bracket
    form is tried first since it is unambiguous (SBML always encodes "["/"]"
    as "__91__"/"__93__"); otherwise this falls back to the BiGG convention.

    Args:
        meta_id (str): Metabolite id as parsed from the raw SBML file

    Returns:
        str: Id with its trailing compartment tag removed
    """
    stripped = _pattern_compartment_bracket.sub("", meta_id)
    if stripped != meta_id:
        return stripped
    return meta_id.rsplit('_', 1)[0]


def decode_sbml_id(sid: str) -> str:
    """Decode SBML-safe encoded characters back to their original form.

    Mirrors cobrapy's default id decoding (cobra.io.sbml.pattern_from_sbml),
    so ids parsed directly from the SBML file match the ids of a model
    loaded through cobra.io.read_sbml_model, and read better in messages.

    Args:
        sid (str): Id as parsed from the raw SBML file (e.g. "1odecg3p__91__c__93__")

    Returns:
        str: Id with encoded characters restored (e.g. "1odecg3p[c]")
    """
    return _pattern_from_sbml.sub(lambda match: chr(int(match.group(1))), sid)


def solve(*args, **kwargs):
    logger = logging.getLogger("s2lp")

    "Wrapper around clyngor.solve"
    kwargs.setdefault('use_clingo_module', False)
    try:
        return clyngor.solve(*args, **kwargs)
    except FileNotFoundError as err:
        if 'clingo' in err.filename:
            logger.error('Binary file clingo is not accessible in the PATH.')
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
    logger = logging.getLogger("s2lp")

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
    logger.warning("Output not totally recovered. Json has been repaired but might miss results")
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


def build_solution_dict(size:int, seeds:list, cobra_flux:dict=None, transferred:list=None,
                         reaction_flux:list=None, accumulation_avoided_seeds:dict=None) -> dict:
    """Build one "solutions" entry of the results JSON as a plain dict, instead of
    the flat tagged list (["size", N, "Set of seeds", [...], ...]) used before
    github issue 27. Every key beyond "size"/"Set of seeds" is omitted (not set
    to null) when not applicable to the current solving mode.

    Args:
        size (int): Number of seeds in this solution
        seeds (list): List of seed metabolite ids
        cobra_flux (dict, optional): Cobra-inferred flux per objective (filter/guess_check/community). Defaults to None.
        transferred (list, optional): List of transferred-metabolite dicts (community only). Defaults to None.
        reaction_flux (list, optional): List of (reaction, flux) pairs (Hybrid-lpx/FBA only). Defaults to None.
        accumulation_avoided_seeds (dict, optional): {"size": int, "Set of seeds": list} sub-solution
            for the seeds avoided to prevent accumulation (Hybrid-lpx/FBA only). Defaults to None.

    Returns:
        dict: One "solutions" entry
    """
    solution = {"size": size, "Set of seeds": seeds}
    if transferred is not None:
        solution["Set of transferred"] = transferred
    if cobra_flux is not None:
        solution["Cobra flux"] = cobra_flux
    if reaction_flux is not None:
        solution["reaction_flux"] = reaction_flux
    if accumulation_avoided_seeds is not None:
        solution["accumulation avoid with seeds"] = accumulation_avoided_seeds
    return solution


def targets_from_json(targets_data) -> dict:
    """Convert a "USER DATA"/"TARGETS" JSON value back into the dict shape
    Network expects as input_dict["Targets"] ({target: [associated metabolite
    ids]}). Single-network results store it flattened as a plain list (every
    target maps to itself, so the wrapping list was redundant); community
    results keep the dict, since one target can group several species-prefixed
    ids there. Accepts either shape so older un-flattened single-network files
    still load correctly.

    Args:
        targets_data (list|dict): The "TARGETS" value as read from a results JSON

    Returns:
        dict: {target: [associated metabolite ids]}
    """
    if isinstance(targets_data, list):
        return {target: [target] for target in targets_data}
    return targets_data