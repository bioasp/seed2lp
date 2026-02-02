#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Test seed2lp
"""
from os import path
from .utils import search_seed

##### ###### ##### DIRECTORIES AND FILES ###################
TEST_DIR = path.dirname(path.abspath(__file__))

# All reaction are not reversible 
# except import/export reaction for exchange metabolite S1, S2 C and G
INFILE = path.join(TEST_DIR,'network/sbml/toy_paper_no_reversible.sbml')
######################################################## 


################### FIXED VARIABLES ####################
RUN_MODE="fba"
######################################################## 


################# EXPECTED SOLUTIONS ###################

# Seeds for Reasoning, filter, Gues-Check, Guess-Check Diversty and Hybrid
SEEDS_SUBMIN_TAF= [{"M_B_c", "M_D_c", "M_E_c"},
                {"M_B_c", "M_D_c", "M_I_c"},
                {"M_B_c", "M_D_c", "M_H_c"},
                {"M_B_c", "M_I_c", "M_S2_e"},
                {"M_B_c", "M_E_c", "M_S2_e"},
                {"M_B_c", "M_H_c", "M_S2_e"},
                {"M_A_c", "M_D_c", "M_I_c", "M_S1_e"},
                {"M_D_c", "M_I_c", "M_J_c", "M_S1_e"},
                {"M_A_c", "M_D_c", "M_E_c", "M_S1_e"},
                {"M_A_c", "M_D_c", "M_H_c", "M_S1_e"},
                {"M_A_c", "M_E_c", "M_S1_e", "M_S2_e"},
                {"M_A_c", "M_H_c", "M_S1_e", "M_S2_e"},
                {"M_H_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_E_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_A_c", "M_I_c", "M_S1_e", "M_S2_e"},
                {"M_I_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_D_c", "M_H_c", "M_J_c", "M_S1_e"},
                {"M_D_c", "M_E_c", "M_J_c", "M_S1_e"}
                ]
SIZE_SUBMIN_TAF=len(SEEDS_SUBMIN_TAF)

SEEDS_MIN_TAF = [{"M_B_c", "M_D_c", "M_E_c"} ,
            {"M_B_c", "M_D_c", "M_I_c"} ,
            {"M_B_c", "M_D_c", "M_H_c"} ,
            {"M_B_c", "M_I_c", "M_S2_e"} ,
            {"M_B_c", "M_E_c", "M_S2_e"} ,
            {"M_B_c", "M_H_c", "M_S2_e"}
            ]
SIZE_MIN_TAF=len(SEEDS_MIN_TAF)


SEEDS_SUBMIN_TAS= [{"M_F_c"},
                {"M_B_c", "M_D_c", "M_E_c"},
                {"M_B_c", "M_D_c", "M_I_c"},
                {"M_B_c", "M_D_c", "M_H_c"},
                {"M_B_c", "M_I_c", "M_S2_e"},
                {"M_B_c", "M_E_c", "M_S2_e"},
                {"M_B_c", "M_H_c", "M_S2_e"},
                {"M_A_c", "M_D_c", "M_I_c", "M_S1_e"},
                {"M_D_c", "M_I_c", "M_J_c", "M_S1_e"},
                {"M_A_c", "M_D_c", "M_E_c", "M_S1_e"},
                {"M_A_c", "M_D_c", "M_H_c", "M_S1_e"},
                {"M_A_c", "M_E_c", "M_S1_e", "M_S2_e"},
                {"M_A_c", "M_H_c", "M_S1_e", "M_S2_e"},
                {"M_H_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_E_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_A_c", "M_I_c", "M_S1_e", "M_S2_e"},
                {"M_I_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_D_c", "M_H_c", "M_J_c", "M_S1_e"},
                {"M_D_c", "M_E_c", "M_J_c", "M_S1_e"}
                ]
SIZE_SUBMIN_TAS=len(SEEDS_SUBMIN_TAS)

SEEDS_MIN_TAS = [{"M_F_c"}]
SIZE_MIN_TAS=len(SEEDS_MIN_TAS)

######################################################## 






######################### TESTS ########################
#TODO: 
#     - test with accumulation
#     - test keep import reaction and topological injection
#     - find Network to have different value in Reasoning / Filter / Gues_check / Guess_Check_Div
#     - find Network to have different value with accumulation authorized
#     - test without maximization for hybrid
#     - test unsat
#     - test possible_seeds (subset of seed that maximize number of producible targets)
#     - test changing objective
#     - test target file

# solve values: 'all'
# optim values: 'submin', 'min'

# ---------------------- TARGET ARE FORBIDDEN ----------------------
# ----------- SUBSETMIN ----------- 
def test_submin_taf():
    solve="all"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAF
    assert len(list_solution) == SIZE_SUBMIN_TAF


# ----------- MINIMIZE ----------- 
def test_min_taf():
    solve="all"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAF
    assert len(list_solution) == SIZE_MIN_TAF


# ---------------------- TARGET AS SEEDS ----------------------
# ----------- SUBSETMIN ----------- 
def test_submin_tas():
    solve="all"
    optim="submin"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAS
    assert len(list_solution) == SIZE_SUBMIN_TAS


# ----------- MINIMIZE ----------- 
def test_min_tas():
    solve="all"
    optim="min"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAS
    assert len(list_solution) == SIZE_MIN_TAS
