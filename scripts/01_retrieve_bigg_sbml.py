import requests
from os import path, mkdir
import json
from sys import argv


def bigg_data_import(out_dir):
    """Import BIGG models and save them to a directory.

    Args:
        dir_ (str, optional): Name of the directory where files will be stored. Defaults to 'BIGG'.
    """
    print('>>> BIGG data import...', end='\t')
    dir_= path.join(out_dir,'bigg')
    db_version = requests.get('http://bigg.ucsd.edu/api/v2/database_version').json()
    data = requests.get('http://bigg.ucsd.edu/api/v2/models').json()
    if not path.exists(dir_) : mkdir(dir_)
    mkdir(dir_+'/data')
    mkdir(dir_+'/sbml')
   
    with open(f'{dir_}/data/db_version.json', 'w') as db_version_f: json.dump(db_version, db_version_f, indent=4)
    
    for model in data['results']:
        id_ = model['bigg_id']
        r = requests.get(f'http://bigg.ucsd.edu/static/models/{id_}.xml')
        with open(f'{dir_}/sbml/{id_}.xml', 'wb') as f : f.write(r.content)
    print('Done.')
    return db_version



if __name__ == '__main__':
    out_dir = argv[1]
    bigg_data_import(out_dir)
