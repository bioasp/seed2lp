import cobra 
model=cobra.io.read_sbml_model("networks/toys_communities/communities/comex.sbml")
model=cobra.io.read_sbml_model("networks/toys_communities/sbml/B1.sbml")

for elem in model.boundary:
    if not elem.reactants and elem.upper_bound > 0:
        if elem.lower_bound > 0:
            elem.lower_bound = 0
        elem.upper_bound = 0.0
    if not elem.products and elem.lower_bound < 0:
        if elem.upper_bound < 0:
            elem.upper_bound = 0
        elem.lower_bound = 0.0

model.reactions.EX_A.upper_bound = 0
model.reactions.EX_B.upper_bound = 0
model.reactions.EX_C.upper_bound = 0
model.reactions.EX_E.upper_bound = 0
#model.reactions.EX_A.lower_bound = -1000
model.reactions.B1_EX_A.lower_bound = -1000
model.reactions.B2_EX_A.lower_bound = -1000
model.reactions.B2_EX_B.lower_bound = -1000
#model.reactions.EX_B.lower_bound = -1000
model.reactions.EX_C.lower_bound = 0
model.reactions.EX_E.lower_bound = 0


same_flux = model.problem.Constraint(
                model.reactions.B1_Biom1.flux_expression - model.reactions.B2_Biom2.flux_expression, 
                lb=0, ub=0)
model.add_cons_vars(same_flux)


#biom_com = cobra.Reaction("Biom_com")
#biom_com.name = "Biom_com"
#biom_com.lower_bound = 0
#biom_com.upper_bound = 1000
#biom_com.add_metabolites({
#    model.metabolites.get_by_id("BM1_e"): -1.0,
#    model.metabolites.get_by_id("BM2_e"): -1.0})
#
#model.reactions.add(biom_com)


model.objective = "B1_Biom1"
solution = model.optimize()
print(solution.fluxes['B1_Biom1'], solution.fluxes['B2_Biom2'], solution.objective_value)

for r in model.reactions:
    print(f"{r} -- {r.lower_bound} -- {r.upper_bound}")

#######################################################################################################################################################


import cobra 
model=cobra.io.read_sbml_model("networks/toys_communities/communities/comex_2.sbml")

for elem in model.boundary:
    if not elem.reactants and elem.upper_bound > 0:
        if elem.lower_bound > 0:
            elem.lower_bound = 0
        elem.upper_bound = 0.0
    if not elem.products and elem.lower_bound < 0:
        if elem.upper_bound < 0:
            elem.upper_bound = 0
        elem.lower_bound = 0.0

model.reactions.EX_A.upper_bound = 0
model.reactions.EX_B.upper_bound = 0
model.reactions.EX_A.lower_bound = -1000
model.reactions.EX_B.lower_bound = 0

#same_flux = model.problem.Constraint(model.reactions.Biom1_B1.flux_expression - model.reactions.Biom2_B2.flux_expression, lb=0, ub=0)
#model.add_cons_vars(same_flux)
