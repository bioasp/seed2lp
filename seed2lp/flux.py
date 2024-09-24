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
        objective_reaction = sub("^R_","",objective_reaction)
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


def get_flux(model:Model, objective_reaction:str):
    """Calculate the flux of the objective reaction chosen using cobra

    Args:
        model (Model): Cobra model
        objective_reaction (str): Objective reaction chosen

    Returns:
        float: The value of the objective flux
    """
    warnings.filterwarnings("error")
    try:
        #with open('/home/cghassem/Projets/seed-2-lp/analyses/test.lp', 'w') as out:
        #    #print(str(model.solver))
        #    out.write(str(model.solver))
        objective_flux = model.optimize().fluxes[objective_reaction]
        infeasible = False
    except UserWarning:
        objective_flux = 0.0
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
              fluxes_lp=dict, try_demands:bool=True):
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

    for objective_reaction in list_objective:
        if fluxes_lp:
            lp_flux = fluxes_lp[objective_reaction]
        else:
            lp_flux=None

        # get flux of objective reaction
        objective_reaction = sub("^R_","",objective_reaction)
        model.objective = objective_reaction
        created_sinks = []
        logger.log.info("Opening Import flux from seeds (Exchange) or add Sinks ...")
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
        objective_flux_seeds, infeasible_seeds = get_flux(model, objective_reaction)
        ok_seeds = objective_flux_seeds > 10e-5 if objective_flux_seeds else False

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

            objective_flux_demands, infeasible_demands = get_flux(model, objective_reaction)
            ok_demands = objective_flux_demands > 10e-5 if objective_flux_demands else False
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
