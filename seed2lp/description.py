# Object Description, herit from Network, added properties:
#     - file (str): Path of input network file (sbml)
#     - out_dir (str): Output directory
#     - details (bool): Reaction Details performed if True. 

import pandas as pd
import re
from os import path
from seed2lp.network import Network     
from . import flux, logger, color
import warnings
import difflib
import seed2lp.sbml as SBML
import copy


SRC_DIR = path.dirname(path.abspath(__file__))
ASP_SRC_ENUM_CC = path.join(SRC_DIR, 'asp/enum-cc.lp')

BISEAU_VIZ = """
#defined reactant/4.
#defined product/4.
#defined reaction/1.
link(T,R) :- reactant(T,_,R,_).
link(R,P) :- product(P,_,R,_).
shape(R,rectangle) :- reaction(R).
obj_property(edge,arrowhead,vee).
"""
BISEAU_VIZ_NOREACTION = """
link(M,P) :- product(P,_,R,_) ; reactant(M,_,R,_).
link(P,P) :- product(P,_,R,_) ; not reactant(_,_,R,_).
link(M,M) :- reactant(M,_,R,_), not product(_,_,R,_).
obj_property(edge,arrowhead,vee).
"""



class Description(Network):
    def __init__(self, file:str, keep_import_reactions:bool, out_dir:str, 
                 details:bool=False, visu:bool=False, visu_no_reaction:bool=False,
                 write_file:bool=False):
        """Initialize Object Description, herit from Network

        Args:
            file (str): Path of input network file (sbml)
            keep_import_reactions (bool): Import reactions are not removed
            out_dir (str): Output directory
            details (bool, optional): Reaction Details performed if True. Defaults to False.
            visu (bool, optional): Graph of Network performed if True. Defaults to False.
            visu_no_reaction (bool, optional): Graph of Network without the reaction performed if True. Defaults to False.
            write_file (bool, optional): Write corrected network into SBML file if True. Defaults to False.
        """
        super().__init__(file, keep_import_reactions=keep_import_reactions, write_sbml=write_file)
        self.out_dir = out_dir
        self.details = details
        self.visu = visu
        self.visu_no_reaction = visu_no_reaction
        self.write_file = write_file
        self.convert_to_facts()
        if self.keep_import_reactions:
            self.short_option="import_rxn"
        else:
            self.short_option="rm_rxn"
        self.cobra_details=""
        self.lp_details=""

    
    ######################## METHODS ########################
    def get_details(self):
        """Reconstruct reaction details from asp facts
        Describe the reaction formula and boundaries
        """

        print(f"\n\n{color.cyan_dark}############################################")  
        print("############################################")  
        print("                 DETAILS ") 
        print("############################################") 
        print(f"############################################\n{color.reset}") 

        print(f"\n{color.purple}____________________________________________{color.reset}") 
        print("\n                 LP FACTS ")
        print(f"{color.purple}____________________________________________\n{color.reset}") 
        print("Getting details from lp facts ...\n")
        self.details_from_lp()
        print(" ---> done\n")

        print(f"\n{color.purple}____________________________________________{color.reset}") 
        print("\n                 COBRA ")
        print(f"{color.purple}____________________________________________\n{color.reset}") 
        print("Getting details from cobra ...\n")
        self.details_from_cobra()
        print(" ---> done\n")

        print(f"\n{color.purple}____________________________________________{color.reset}") 
        print("\n                 DIFF ")
        print(f"{color.purple}____________________________________________\n{color.reset}") 
        print("Searching diff ...\n")
        self.details_diff()
        print(" ---> done\n")


    def details_from_lp(self):
        """Get the network description from lp facts and save it
        """
        logger.log.info("Start Getting Details from LP file")
        reactions_composition_df = pd.DataFrame(columns=['reaction', 'metabolite', 'type_metabolite', 'stoichiometry'])
        reaction_df = pd.DataFrame(columns=['reaction', 'low_bound', 'up_bound','is_forward', 'is_reverse', 'is_low_set'])
        only_forward=list()
        full_details=""
        lis_obj=list()

        lines=re.split("\n", self.facts)
        # Getting the network and the reaction direction
        for line in lines:
            if re.search("reaction",line):
                reaction = re.split("\"", line)[1]
                if "rev_" in reaction:
                    reaction = re.split("rev_R_", reaction)[1]
                    df=pd.DataFrame(data=[[reaction, 0.0, 0.0, False, True, False]],columns=['reaction', 'low_bound', 'up_bound','is_forward', 'is_reverse', 'is_low_set'])
                    reaction_df=pd.concat([reaction_df,df], ignore_index = True)
                else:
                    reaction = re.split("R_", reaction)[1]
                    try:
                        index=reaction_df[reaction_df["reaction"]==reaction].index[0]
                        reaction_df.at[index,'is_forward']=True
                    except Exception:
                        only_forward.append(f"R_{reaction}")
                        df=pd.DataFrame(data=[[reaction, 0.0, 0.0, True, False, False]],columns=['reaction', 'low_bound', 'up_bound','is_forward', 'is_reverse', 'is_low_set'])
                        reaction_df=pd.concat([reaction_df,df], ignore_index = True)
            elif re.search("bounds",line):
                split_line = re.split(",", line)
                reaction=re.split("\"", split_line[0])[1]
                lower=re.split("\"", split_line[1])[1]
                lower=float(lower)
                upper=re.split("\"", split_line[2])[1]
                upper=float(upper)
                if "rev_" in reaction:
                    reaction = re.split("rev_R_", reaction)[1]
                    try:
                        index=reaction_df[reaction_df["reaction"]==reaction].index[0]
                        reaction_df.at[index,'low_bound'] = -upper
                        reaction_df.at[index,'is_low_set'] = True
                    except Exception:
                        df=pd.DataFrame(data=[[reaction, -upper, 0.0, False, True, True]],columns=['reaction', 'low_bound', 'up_bound','is_forward', 'is_reverse', 'is_low_set'])
                        reaction_df=pd.concat([reaction_df,df], ignore_index = True)
                        reaction_df.at[index,'is_low_set'] = True
                else:
                    reaction = re.split("R_", reaction)[1]
                    try:
                        index=reaction_df[reaction_df["reaction"]==reaction].index[0]
                        reaction_df.at[index,'up_bound'] = upper
                        if not reaction_df.at[index,'is_low_set']:
                            reaction_df.at[index,'low_bound'] = lower
                            reaction_df.at[index,'is_low_set'] = True
                    except Exception:
                        only_forward.append(f"R_{reaction}")
                        df=pd.DataFrame(data=[[reaction, lower, upper, True, False, True]],columns=['reaction', 'low_bound', 'up_bound','is_forward', 'is_reverse', 'is_low_set'])
                        reaction_df=pd.concat([reaction_df,df], ignore_index = True)
            elif re.search("reactant",line):
                split_line = re.split(",", line)
                reaction=re.split("\"", split_line[2])[1]
                metabolite = re.split("\"", split_line[0])[1]
                stoichiometry=round(float(re.split("\"", split_line[1])[1]),6)
                if "rev_" in reaction:
                    reaction = re.split("rev_R_", reaction)[1]
                    df=pd.DataFrame(data=[[reaction, metabolite, "product", stoichiometry]],
                                    columns=['reaction', 'metabolite', 'type_metabolite', 'stoichiometry'])
                    reactions_composition_df=pd.concat([reactions_composition_df,df], ignore_index = True)
                elif reaction in only_forward:
                    reaction = re.split("R_", reaction)[1]
                    df=pd.DataFrame(data=[[reaction, metabolite, "reactant", stoichiometry]],
                                    columns=['reaction', 'metabolite', 'type_metabolite', 'stoichiometry'])
                    reactions_composition_df=pd.concat([reactions_composition_df,df], ignore_index = True)
            elif re.search("product",line):
                split_line = re.split(",", line)
                reaction=re.split("\"", split_line[2])[1]
                metabolite = re.split("\"", split_line[0])[1]
                stoichiometry=round(float(re.split("\"", split_line[1])[1]),6)
                if "rev_" in reaction:
                    reaction = re.split("rev_R_", reaction)[1]
                    df=pd.DataFrame(data=[[reaction, metabolite, "reactant", stoichiometry]],
                                    columns=['reaction', 'metabolite', 'type_metabolite', 'stoichiometry'])
                    reactions_composition_df=pd.concat([reactions_composition_df,df], ignore_index = True)
                elif reaction in only_forward:
                    reaction = re.split("R_", reaction)[1]
                    df=pd.DataFrame(data=[[reaction, metabolite, "product", stoichiometry]],
                                    columns=['reaction', 'metabolite', 'type_metabolite', 'stoichiometry'])
                    reactions_composition_df=pd.concat([reactions_composition_df,df], ignore_index = True)
        reaction_df.sort_values(by=['reaction'])
        reactions_composition_df.sort_values(by=['reaction', 'metabolite'])
        self.objectives = lis_obj

        #reaction_without_reactant=[]
        #reaction_without_product=[]
        # Writting the network description
        for _,row in reaction_df.iterrows():
            reaction=row[0]
            lower=row[1]
            upper=row[2]
            forward=row[3]
            reverse=row[4]
            symbol=""
            compo_line=f'{reaction}:'
            match ([forward, reverse]):
                case [True, False]:
                    symbol=" -->"
                    if upper == 0:
                        symbol=" <--"
                case [False, True]:
                    symbol=" <--"
                    if lower == 0:
                        symbol=" -->"
                case [True, True]:
                    symbol=" <=>"
            sub_reaction=reactions_composition_df[reactions_composition_df["reaction"]==reaction]
            sub_reactant=sub_reaction[sub_reaction["type_metabolite"]=="reactant"]
            sub_product=sub_reaction[sub_reaction["type_metabolite"]=="product"]
            it=0
            if sub_reactant.empty:
                #reaction_without_reactant.append(reaction)
                compo_line += " "
            else:
                for r_metabolite in sub_reactant.iterrows():
                    it += 1
                    if it!=1:
                        compo_line += " +"
                    stoic=""
                    if r_metabolite[1]["stoichiometry"] != 1.0:
                        stoic=f' {r_metabolite[1]["stoichiometry"]}'
                    compo_line += f'{stoic} {re.sub("^M_", "", r_metabolite[1]["metabolite"])}'
            compo_line += symbol
            it=0
            if sub_product.empty:
                #reaction_without_product.append(reaction)
                compo_line += " "
            else:
                for p_metabolite in sub_product.iterrows():
                    it += 1
                    if it!=1:
                        compo_line += " +"
                    stoic=""
                    if p_metabolite[1]["stoichiometry"] != 1.0:
                        stoic=f' {p_metabolite[1]["stoichiometry"]}'
                    compo_line += f'{stoic} {re.sub("^M_", "", p_metabolite[1]["metabolite"])}'
            compo_line += f'\t[{lower}, {upper}]'
            #print(compo_line)
            full_details += f'{compo_line}\n'

        self.lp_details = path.join(self.out_dir, f"{self.name}_{self.short_option}_details_from_lp.txt")
        #print("REACTION WITHOUT REACTANT")
        #print(reaction_without_reactant)
        #print("REACTION WITHOUT PRODUCT")
        #print(reaction_without_product)
        save(self.lp_details , full_details)
        

    def details_from_cobra(self):
        """Get the network description from sbml file by using cobra and save it
        """
        logger.log.info("Start Getting Details from Cobra file")
        warnings.filterwarnings("error")
        model = flux.get_model(self.file)
        if not self.keep_import_reactions:
            flux.stop_flux(model)
        full_details=""
        for reaction in model.reactions:
            full_details += f"{reaction}\t[{reaction.lower_bound}, {reaction.upper_bound}]\n"
            
        self.cobra_details = path.join(self.out_dir, f"{self.name}_{self.short_option}_details_from_cobra.txt")
        save(self.cobra_details, full_details)


    def details_diff(self):
        """Compare the Network description from cobra and lp facts
        save the diff information into file
        """
        logger.log.info("Start checking diff between Cobra and LP Network")
        diff = ""
        with open(self.cobra_details) as cobra_details:
            cobra_details_text = cobra_details.readlines()
        
        with open(self.lp_details) as lp_details:
            lp_details_text = lp_details.readlines()

        # Find the diff:
        for line in difflib.unified_diff(
                cobra_details_text, lp_details_text, fromfile=self.cobra_details,
                tofile=self.lp_details, lineterm=''):
            diff += f'{line}\n'

        cobra_details.close()
        lp_details.close()

        diff_path = path.join(self.out_dir, f"{self.name}_{self.short_option}_details_diff.txt")
        save(diff_path, diff)

    def render_network(self):
        """From lp facts render the network graph with or without reaction
        """
        import biseau
        out_file = path.join(self.out_dir, f"{self.name}_{self.short_option}_visu")

        print(f"\n\n{color.cyan_dark}############################################")  
        print("############################################")  
        print("                 GRAPH ") 
        print("############################################") 
        print(f"############################################\n{color.reset}") 
        if self.visu:
            print(f"\n{color.purple}____________________________________________{color.reset}") 
            print(f"\n            GRAPH WITH REACTIONS ")
            print(f"{color.purple}____________________________________________{color.reset}\n") 
            print("Generating graph ...\n")
            viz = BISEAU_VIZ
            out_file_visu = f"{out_file}.png"
            try:
                img_visu = biseau.compile_to_single_image(self.facts + viz, outfile=out_file_visu)
                img_visu.close()
                print(f'-> Input graph rendered in {out_file_visu}\n')
            except KeyboardInterrupt:
                    print(f'-> Aborted! file :{out_file_visu}\n')
        if self.visu_no_reaction:
            print(f"\n{color.purple}____________________________________________{color.reset}") 
            print("\n           GRAPH WITHOUT REACTIONS ")
            print(f"{color.purple}____________________________________________\n{color.reset}") 
            print("Generating graph ...\n")
            viz = BISEAU_VIZ_NOREACTION
            out_file_visu_no_reaction = f"{out_file}_no_reactions.png"
            try:
                img_visu_no_reaction = biseau.compile_to_single_image(self.facts + viz, outfile=out_file_visu_no_reaction)
                img_visu_no_reaction.close()
                print(f'-> Input graph rendered in {out_file_visu_no_reaction}\n')
            except KeyboardInterrupt:
                print(f'-> Aborted! file :{out_file_visu_no_reaction}\n')


    def rewrite_sbml_file(self):
        """SBML file is written from corrected network
        """
        print(f"\n\n{color.cyan_dark}############################################")  
        print("############################################")  
        print("           WRITING SBML FILE ") 
        print("############################################") 
        print(f"############################################\n{color.reset}") 

        if self.keep_import_reactions:
            logger.log.warning("IMPORT REACTION KEPT")
        else:
            logger.log.warning("IMPORT REACTION REMOVED BY DEFAULT")
            logger.log.warning("If you want to keep import reaction\nuse option -kir / --keep-import-reactions")
        model = SBML.get_model(self.sbml)
        original_reactions = SBML.get_listOfReactions(model)

        # Need Two loop to remove first then two do modification
        # If removing while looping, then the loop misses some reactions
        # because the index of the reaction changes
        rm_reac_message = "Reaction removed:"
        is_rm = False
        for reaction in original_reactions:
            reaction_name = reaction.attrib.get("id")
            if reaction_name in self.deleted_reactions:
                SBML.remove_reaction(model,reaction)
                is_rm = True
                rm_reac_message+=f"\n\t- {reaction_name}"
        if is_rm:
            logger.log.info(rm_reac_message)

        modif_rev_message = "Reaction with tag reversible modified:"
        is_modif_rev = False
        exch_meta_message = "Reaction with Reactants and Products exchanged:"
        is_exch_meta = False
        rm_import_message = "Import reaction removed:"
        is_rm_import = False
        for reaction in original_reactions:
            reaction_name = reaction.attrib.get("id")
            # Change the reversibility
            if reaction_name in self.reversible_modified_reactions:
                index = self.reversible_modified_reactions[reaction_name]
                reaction.attrib["reversible"] = str(self.reactions[index].reversible).lower()
                is_modif_rev = True
                modif_rev_message+=f"\n\t- {reaction_name}"

            # Exchange list of reactants and product if they are tagged as modified
            # The modification tag is only on exchanging reactants and products
            # Reaction written backward will be wrote forward
            if reaction_name in self.meta_modified_reactions:
                index = self.meta_modified_reactions[reaction_name]
                has_reactant=False
                has_product=False
                reactants=list()
                products=list()
                # loop into source
                for element in reaction:
                    # copy and remove list of reactant and products from source
                    if SBML.get_sbml_tag(element) == "listOfReactants":
                        reactants = copy.copy(element)
                        has_reactant = True
                        SBML.remove_sub_elements(element)
                    elif SBML.get_sbml_tag(element) == "listOfProducts":
                        products = copy.copy(element)
                        has_product=True
                        SBML.remove_sub_elements(element)

                # add the new element into source node 
                # put products into reactant and reactant into products
                recreate_other_node=True
                for element in reaction:
                    if SBML.get_sbml_tag(element) == "listOfReactants":
                        #check if node listOfProducts exist and copy element
                        if has_product:
                            SBML.add_metabolites(element, products)
                        elif recreate_other_node:
                            # the node listOfProducts doesnt exist it needs to be created
                            SBML.create_sub_element(reaction, "listOfProducts")
                            #copy the element of reactant (exchanging reactant and products)
                            SBML.add_metabolites(element, reactants)
                            recreate_other_node=False
                            SBML.remove_sub_elements(element)
                    elif SBML.get_sbml_tag(element) == "listOfProducts" and has_reactant:
                        if has_reactant:
                            SBML.add_metabolites(element, reactants)
                        elif recreate_other_node:
                            SBML.create_sub_element(reaction, "listOfReactants")
                            SBML.add_metabolites(element, products)
                            recreate_other_node=False
                            SBML.remove_sub_elements(element)
                # MODIFIER LES BOUNDARIES
                if self.parameters:
                    self.parameters[f'{reaction_name}_lower_bound'] = self.reactions[index].lbound
                    self.parameters[f'{reaction_name}_upper_bound'] = self.reactions[index].ubound
                    reaction.attrib['{'+self.fbc+'}lowerFluxBound']= f'{reaction_name}_lower_bound'
                    reaction.attrib['{'+self.fbc+'}upperFluxBound']= f'{reaction_name}_upper_bound'
                else:
                    reaction.attrib['{'+self.fbc+'}lowerFluxBound']= self.reactions[index].lbound
                    reaction.attrib['{'+self.fbc+'}upperFluxBound']= self.reactions[index].ubound

                is_exch_meta = True
                exch_meta_message+=f"\n\t- {reaction_name}"


            if not self.keep_import_reactions and  reaction_name in self.exchanged_reactions:
                index = self.exchanged_reactions[reaction_name]
                self.parameters[f'{reaction_name}_lower_bound'] = self.reactions[index].lbound
                self.parameters[f'{reaction_name}_upper_bound'] = self.reactions[index].ubound
                reaction.attrib['{'+self.fbc+'}lowerFluxBound']= f'{reaction_name}_lower_bound'
                reaction.attrib['{'+self.fbc+'}upperFluxBound']= f'{reaction_name}_upper_bound'
                is_rm_import = True
                rm_import_message+=f"\n\t- {reaction_name}"

        if is_modif_rev:
            logger.log.warning(modif_rev_message)
        if is_exch_meta:
            logger.log.warning(exch_meta_message)
        if is_rm_import:
            logger.log.warning(rm_import_message)

        # Replace list of parameters because we added new specific parameters for the exchange reactions
        parameters_copy = copy.copy(self.parameters)

        for el in model:
            tag = SBML.get_sbml_tag(el)
            if tag == "listOfParameters":
                node = copy.deepcopy(el[0])
                for param in el:
                    id = param.attrib.get('id')
                    # Corrects the already existant parameters 
                    if id in parameters_copy:
                        param.attrib['value'] = str(parameters_copy[id])
                        # delete the existant parameter from the list of parameter to keep
                        # only the new parameters
                        parameters_copy.pop(id)
                # create new paramaters node
                for key, value in parameters_copy.items():
                    new_node = copy.deepcopy(node)
                    new_node.attrib['id'] = key
                    new_node.attrib['value'] = str(value)
                    el.append(new_node)

        file_path = path.join(self.out_dir, self.name+".xml") 
        str_model =  self.sbml_first_line+SBML.etree_to_string(self.sbml)
        print(f"File saved at: {file_path}")
        save(file_path, str_model)

    ######################################################## 


######################## FUNCTIONS ########################
def save(out_file:str, data):
    """Save file of Network description or graphs

    Args:
        out_file (str): Output file path
        data: Graph or Network details data
    """
    with open(out_file, 'w') as f:
        f.write(data)
    f.close()
    logger.log.info(f"File saved at: {out_file}")