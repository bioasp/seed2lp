import cobra
from re import sub
from cobra.core import Model
import warnings
from . import logger, color

def get_model(model_file:str):
    """Get cobra model

    Args:
        model_file (str): Sbml file path of the network

    Returns:
        Model: The model generated from cobra
    """
    model = cobra.io.read_sbml_model(model_file)
    return model


def get_list_fluxes(model:Model, list_objective:list, show_messages:bool=True):
    """Get the objective reactions fluxe.
    Can generate the flux for multiple objective reactions

    Args:
        model (Model): Cobra model
        list_objective (list): List of objective reaction names
        show_messages (bool, optional): Write messages into console if True. Default True.

    Returns:
        dict: Dictionnary of objective reaction and their respective fluxes
    """
    warnings.filterwarnings("error")
    fluxes_dict = dict()
    for objective_reaction in list_objective:
        objective_reaction = remove_prefix_reaction(objective_reaction)
        # get flux of objective reaction
        model.objective = objective_reaction
        try:
            objective_flux = model.optimize().fluxes[objective_reaction]
        except UserWarning:
            objective_flux = 0.0
        fluxes_dict[objective_reaction]=objective_flux
    if show_messages:
        print(fluxes_dict)
        print('\n')
    return fluxes_dict


def set_objective(model:Model, objective:str):
    # get flux of objective reaction
    objective_reaction = remove_prefix_reaction(objective)
    model.objective = objective_reaction
    return objective_reaction
        

def remove_prefix_reaction(reaction):
    return sub("^R_","",reaction)


def get_reaction(model:Model, objective_name:str):
    id = remove_prefix_reaction(objective_name)
    return model.reactions.get_by_id(id)


def get_flux(model:Model, objective_reaction:str, list_objective:list, 
             is_community:bool=False, transferred_list:list=None, 
             equality_flux:bool=False):
    """Calculate the flux of the objective reaction chosen using cobra

    Args:
        model (Model): Cobra model
        objective_reaction (str): Objective reaction chosen
        list_objective (list): List of all objectives (specially for community mode)
        is_community (bool, optional): If it is a community mode. Defaults to False.
        transferred_list (list, optional): For community mode, we have transferred metavolites list. Defaults to None.
        equality_flux (bool, optional): Force the flux of biomass to be equal between species, else just force to have
                                        a minimum value of flux=0.1 . Defaults to False.

    Returns:
        float, bool: The value of the objective flux, if the model is infeasible or not
    """
    warnings.filterwarnings("error")
    objective_flux=dict()
    try:
        ###############################################################################
        ############################### COMMUNITY MODE ################################
        ############################################################################### 
        if is_community:
            created_transfers=list()
            created_transfers_id=list()
            dict_objective = dict()
            # Force equality of flux between species' objective reactions
            if equality_flux:
                # First species has its objective set to be compared with
                # for community model, so we loop on the other objectives
                # to add contraints: The flux on the other objectives
                # has to be the same as the objective of community model
                for obj in list_objective[1:]:
                    reaction = get_reaction(model, obj)
                    dict_objective[reaction]=1
                    same_flux = model.problem.Constraint(
                        model.reactions.get_by_id(objective_reaction).flux_expression - reaction.flux_expression, 
                        lb=0, ub=0)
                    model.add_cons_vars(same_flux)
            # Force to have flux in all species
            else:
                # We loop on all objective to add the constraint of minimial flux 
                # to all objective reactions
                for obj in list_objective:
                    reaction = reaction = get_reaction(model, obj)
                    dict_objective[reaction]=1
                    flux_positiv = model.problem.Constraint(
                        reaction.flux_expression, 
                        lb=0.1, ub=1000)
                    model.add_cons_vars(flux_positiv)

            model.objective = dict_objective

            # Create Transfer reaction  between 2 species where reactant is metabolite "From"
            # and product is metabolite "To"
            for transf_meta in transferred_list:
                name_meta=transf_meta["Metabolite"].rsplit('_',1)[0]
                name_meta=sub("^M_","",name_meta)
                id_reaction = f'R_TRANSF_{name_meta}_{transf_meta["From"]}_{transf_meta["To"]}'
                # Create the transfer reaction
                reaction = cobra.Reaction(id_reaction)
                reaction.lower_bound = 0.
                reaction.upper_bound = 1000.
                reactant = model.metabolites.get_by_id(sub("^M_","",transf_meta["ID from"]))
                procuct = model.metabolites.get_by_id(sub("^M_","",transf_meta["ID to"]))
                reaction.add_metabolites({
                        reactant: -1.0,
                        procuct: 1.0
                    })
                # For some reason sometimes the transfers already exists
                # This part check if it exists and if it does not then the transfers is created
                try:
                    model.reactions.get_by_id(id_reaction)
                except:
                    if id_reaction not in created_transfers_id:
                        created_transfers.append(reaction)
                        created_transfers_id.append(id_reaction)
            model.add_reactions(created_transfers) 
        ###############################################################################
        ###############################################################################
        ############################################################################### 

        objectives_flux = model.optimize()

        for obj in list_objective:
            objective = remove_prefix_reaction(obj)
            objective_flux[objective]=round(objectives_flux.fluxes[objective],2)

        infeasible = False
    except UserWarning:
        for obj in list_objective:
            objective = remove_prefix_reaction(obj)
            objective_flux[objective]=0
        infeasible = True
        logger.log.info("Model infeasible")
        
    return objective_flux, infeasible


def get_init(model:Model, list_objective:list, show_messages:bool=True):
    """Get initial flux of all objective reactions using cobra

    Args:
        model (Model): Cobra model
        list_objective (list): List of objective reaction names
        show_messages (bool, optional): Write messages into console if True. Default True.

    Returns:
        dic: Dictionnary of objective reaction and their respective fluxes
    """
    if show_messages:
        title_mess = "\n############################################\n" \
            "############################################\n" \
            f"                 {color.bold}CHECK FLUX{color.cyan_light}\n"\
            "############################################\n" \
            "############################################\n"
        logger.print_log(title_mess, "info", color.cyan_light) 

    
        print("---------------- FLUX INIT -----------------\n")
    fluxes_init = get_list_fluxes(model, list_objective, show_messages)

    if show_messages:
        print("--------------- MEDIUM INIT ----------------\n")
        for reaction in model.medium:
            print(reaction, model.reactions.get_by_id(reaction).lower_bound, model.reactions.get_by_id(reaction).upper_bound)
        print(f"\n")
    return fluxes_init


def stop_flux(model:Model, list_objective:list=None, show_messages:bool=True):
    """Stop the import reaction flux

    Args:
        model (Model): Cobra model
        list_objective (list): List of objective reaction names
        show_messages (bool, optional): Write messages into console if True. Default True.

    Returns:
        dic: Dictionnary of objective reaction and their respective fluxes
    """
    if show_messages:
        print("---------- STOP IMPORT FLUX -------------\n") 
    logger.log.info("Shutting down import flux ...")

    for elem in model.boundary:
        if not elem.reactants and elem.upper_bound > 0:
            if elem.lower_bound > 0:
                elem.lower_bound = 0
            elem.upper_bound = 0.0
        if not elem.products and elem.lower_bound < 0:
            if elem.upper_bound < 0:
                elem.upper_bound = 0
            elem.lower_bound = 0.0

    logger.log.info("... DONE")

    if list_objective is not None:
        fluxes_no_import = get_list_fluxes(model, list_objective, show_messages)
        return fluxes_no_import


def calculate(model:Model, list_objective:list, list_seeds:list,  
              fluxes_lp=dict, try_demands:bool=True, is_community:bool=False,
              transferred_list:list=None, equality_flux:bool=False):
    """Calculate the flux by adding seeds and import for them using Cobra.
    Calculate on the objective list, the first having flux stop the calculation

    Args:
        model (Model): Cobra model
        list_objective (list): List of objective reaction names
        list_seeds (list): One result set of seed 
        fluxes_lp (dict): Dictionnary of all reaction and their associated LP flux
        try_demands (bool, optional): Option to try to add demands if seeds failed.
                                        Defaults to True. False for hybrid with cobra.

    Returns:
        dict, str: result (containing the data), objective_reaction (chosen, the first having flux)
    """
    warnings.filterwarnings("error")
    logger.log.info("Starting calculate Flux...")
    if not list_objective:
        logger.log.error("No objective found, abort")
        return None, None
    
    #cobra.flux_analysis.add_loopless(model)
    #model.solver = 'cplex'
    
    species = model.id
    objective_flux_seeds=None
    objective_flux_demands=None
    ok_result=False
    ok_seeds=None
    ok_demands=None
    objective_reaction=None

    meta_exchange_list=dict()

    for reaction in model.boundary:
        for key in reaction.metabolites.keys():
            meta_exchange_list[str(key)]=reaction.id

    created_sinks = []
    logger.log.info("Opening Import flux from seeds (Exchange) or add Sinks ...")
    objective_reaction = set_objective(model, list_objective[0])

    for seed in list_seeds:
        seed = sub("^M_","",seed)
        #compartment = model.metabolites.get_by_id(seed).compartment
        #if compartment == 'e':
        if seed in meta_exchange_list.keys():
            reaction_exchange = model.reactions.get_by_id(meta_exchange_list[seed])
            # For a seed in the exchange metabolites list, we allow both import and export
            # on the "maximum" flux (1000)

            if not reaction_exchange.reactants:
                reaction_exchange.upper_bound = float(1000)
                # Do not change the lower bound when there is an export 
                # Because in ASP we can not change the value of an already
                # exisiting bounds atom
                if reaction_exchange.lower_bound >= 0:
                    reaction_exchange.lower_bound = float(-1000)
            if not reaction_exchange.products:
                reaction_exchange.lower_bound = float(-1000)
                # Do not change the lower bound when there is an export 
                # Because in ASP we can not change the value of an already
                # exisiting bounds atom
                if reaction_exchange.upper_bound <= 0:
                    reaction_exchange.upper_bound = float(1000)
        else: 
            if not f"SK_{seed}" in created_sinks:
                model.add_boundary(metabolite=model.metabolites.get_by_id(seed),
                                        type='sink',
                                        ub=float(1000),
                                        lb=float(-1000))
                created_sinks.append(f"SK_{seed}")
        
    logger.log.info("Opening Import flux: Done")

    logger.log.info("Checking objective flux on seeds ...")
    
    lp_flux=None
    if not is_community:
        if fluxes_lp:
            lp_flux = fluxes_lp[list_objective[0]]

    
    objective_flux_seeds, infeasible_seeds = get_flux(model, objective_reaction, list_objective, is_community, transferred_list, equality_flux)
    if objective_flux_seeds:
        ok_seeds = True
        for _, value in objective_flux_seeds.items():
            ok_seeds = ok_seeds and value > 10e-5 
    else:
        ok_seeds = False

    objective_flux_demands=None
    infeasible_demands=None
    if ok_seeds:
        ok_result = True
        logger.log.info("... OK")
    elif try_demands:
        logger.log.info("... KO - Checking objective flux on demands ...")
        # create a demand reaction for all products of the biomass reaction
        products = [m.id for m in model.reactions.get_by_id(objective_reaction).products]
        for m in products:
            try:
                model.add_boundary(model.metabolites.get_by_id(m), type="demand")
            except:
                low =  model.reactions.get_by_id(f"DM_{m}").lower_bound
                up = model.reactions.get_by_id(f"DM_{m}").upper_bound
                if up <= 0:
                    model.reactions.get_by_id(f"DM_{m}").upper_bound = float(1000)
                if low < 0 :
                    model.reactions.get_by_id(f"DM_{m}").lower_bound = float(0)

        objective_flux_demands, infeasible_demands = get_flux(model, objective_reaction, list_objective, is_community, transferred_list, equality_flux)

        if objective_flux_demands:
            ok_demands = True
            for _, value in objective_flux_seeds.items():
                ok_demands = ok_demands and value > 10e-5 
        else:
            ok_demands = False
        
        if ok_demands:
            ok_result = True
            logger.log.info("... OK")
        else:
            logger.log.info("... KO")

    result = {'id' : species,
            'objective_flux_seeds': objective_flux_seeds,
            'objective_flux_demands': objective_flux_demands,
            'OK_seeds': ok_seeds,
            'OK_demands': ok_demands,
            'OK': ok_result,
            'infeasible_seeds': infeasible_seeds,
            'infeasible_demands': infeasible_demands}

    return result, objective_reaction, lp_flux
