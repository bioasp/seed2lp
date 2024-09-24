from sys import argv
from os import listdir,path
import xml.etree.ElementTree as etree
import pandas as pd

in_dir = argv[1]
out_dir = argv[2]

def get_sbml_tag(element) -> str:
    "Return tag associated with given SBML element"
    if element.tag[0] == "{":
        _, tag = element.tag[1:].split("}")  # uri is not used
    else:
        tag = element.tag
    return tag

def get_fbc(sbml):
    """
    return the fbc namespace of a SBML
    """
    fbc = None 
    for nss in etree._namespaces(sbml):
        for key in nss:
            if key is not None and 'fbc' in key:
                fbc=key
                break
    return fbc

def get_model(sbml):
    """
    return the model of a SBML
    """
    model_element = None
    for e in sbml:
        tag = get_sbml_tag(e)
        if tag == "model":
            model_element = e
            break
    return model_element


if __name__ == '__main__':

    special_dict = {"iMM1415": "R_BIOMASS_mm_1_no_glygln",
                    "iAF987": "R_BIOMASS_Gm_GS15_WT_79p20M",
                    "iSynCJ816": "R_BIOMASS_Ec_SynAuto_1",
                    "iRC1080": "R_BIOMASS_Chlamy_auto"}

    listOfFluxObjectives = pd.DataFrame(columns=["species","reaction","coeffficient"])
    for file in listdir( in_dir ):
        found = False
        file_path = path.join(in_dir,file)
        species = f'{path.splitext(path.basename(file_path))[0]}'
        print(species)
        tree = etree.parse(file_path)
        sbml = tree.getroot()
        model = get_model(sbml)
        fbc = get_fbc(sbml)

        for e in model:
            tag = get_sbml_tag(e)
            if tag == "listOfObjectives":
                for lo in e[0]:
                    if lo:
                        for o in lo:
                            reac = o.attrib.get('{'+fbc+'}reaction')
                            coef = o.attrib.get('{'+fbc+'}coefficient')
                            if float(coef) == 1:
                                current_df = pd.DataFrame([[species,reac,coef]],
                                                          columns=["species","reaction","coeffficient"])
                                listOfFluxObjectives=pd.concat([listOfFluxObjectives, current_df], 
                                                               ignore_index=True)

                                found = True
                if not found:
                    reac =  special_dict[species]
                    current_df = pd.DataFrame([[species, reac, 0]],
                                             columns=["species","reaction","coeffficient"])
                    listOfFluxObjectives=pd.concat([listOfFluxObjectives, current_df], 
                                                               ignore_index=True)
                break
        
        tgt_path = path.join(out_dir,f"{species}_target.txt")
        with open(tgt_path, 'w') as tf:
            tf.write(f'{reac}')
        tf.close()

    out_file_path = path.join(out_dir,"list_objectives.tsv")
    with open(out_file_path, 'w') as f:
        listOfFluxObjectives.to_csv(out_file_path, sep="\t")
    f.close()
