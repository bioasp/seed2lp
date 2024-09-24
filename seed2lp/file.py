from os import path, makedirs, stat, remove
from json import dump, load
from csv import writer, reader
import argparse
from . import logger


def existant_path(inpath:str) -> str:
    """Argparse type, raising an error if given file does not exists

    Args:
        inpath (str): Network input path

    Raises:
        argparse.ArgumentTypeError: Error if the file doesn't exist

    Returns:
        str: Network input path
    """
    if not path.exists(inpath):
        raise argparse.ArgumentTypeError("file {} doesn't exists".format(inpath))
    return inpath

def is_valid_dir(dirpath):
    """Return True if directory exists or can be created (then create it)
    
    Args:
        dirpath (str): path of directory

    Returns:
        bool: True if dir exists, False otherwise
    """
    if not path.isdir(dirpath):
        try:
            makedirs(dirpath)
            return dirpath
        except OSError as e:
            logger.log.error(e)
            return None
    else:
        return dirpath
    
def existing_file(filepath):
    """Return True if file exists
    
    Args:
        filepath (str): path of file

    Returns:
        bool: True if dir exists, False otherwise
    """
    if not path.isfile(filepath):
        return False
    else:
        return True
    

def save(filename:str, directory:str, results, type:str, is_result_temp=False):
    """Save data into file dependinf on type (json / tsv)

    Args:
        filename (str): Filename of saved file
        directory (str): Output directory where to save file
        results: Results data in dictionnary (json) or datatrame (tsv)
        type (str): Type of output fils (json or tsv or txt)
    """

    out_file_path = path.join(directory,filename)
    try:
        match type:
            case 'json':
                out_file_path += '.json'
                with open(out_file_path, 'w') as f:
                    dump(results, f, indent="\t")
                f.close()
            case 'tsv':
                if not ".tsv" in out_file_path:
                    out_file_path += '.tsv'
                # List is given an we want to append data at the end
                if is_result_temp:
                    with open(out_file_path, 'a') as f:
                        tsv_output = writer(f, delimiter='\t')
                        tsv_output.writerow(results)
                # Dataframe is given, and all results are written at once
                else:
                    with open(out_file_path, 'w') as f:
                        results.to_csv(out_file_path, sep="\t")    
                f.close()
            case 'txt':
                if not ".txt" in out_file_path:
                    out_file_path += '.txt'
                with open(out_file_path, "w") as f:
                    f.write("\n".join(results))
    except  Exception as e:
        logger.log.error(f"while saving file: {e}")
    


def file_is_empty(file_path:str):
    """Check if the file is empty

    Args:
        file_path (str): Path of file to check

    Returns:
        bool: True if the file is empty
    """
    return stat(file_path).st_size==0


def write_instance_file(instance_file:str, facts:str):
    """Write and Save instance file
    """
    with open(instance_file, 'w') as f:
        f.write(facts)
    f.close()
    
def delete(filepath:str):
    """Delete a file

    Args:
        filepath (str): Path of File to delete
    """
    remove(filepath)

def load_json(filepath:str):
    """Load a json file into a variable

    Args:
        filepath (str): Path of json file to load

    Returns:
        result (dict): Data formated into a dictionnary
    """
    file = open(filepath)
    result = load(file)
    file.close()
    return result

def load_tsv(filepath:str):
    """Load a tsv file into a variable

    Args:
        filepath (str):  Path of json file to load

    Returns:
        result (list): Data formated into a list
    """
    file = open(filepath)
    result = reader(file, delimiter='\t')
    return list(result)
