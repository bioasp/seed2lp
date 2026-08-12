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
RUN_MODE="target"
######################################################## 


################# EXPECTED SOLUTIONS ###################

# Seeds for Reasoning, filter, Gues-Check, Guess-Check Diversty and Hybrid
SEEDS_SUBMIN_TAF= [{"M_B_c", "M_D_c", "M_E_c"},
                {"M_B_c", "M_D_c", "M_I_c"},
                {"M_B_c", "M_D_c", "M_H_c"},
                {"M_B_c", "M_I_c", "M_S2_e"},
                {"M_B_c", "M_E_c", "M_S2_e"},
                {"M_B_c", "M_H_c", "M_S2_e"},
                {"M_I_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_D_c", "M_I_c", "M_J_c", "M_S1_e"},
                {"M_H_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_E_c", "M_J_c", "M_S1_e", "M_S2_e"},
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


SEEDS_SUBMIN_TAS= [{"M_B_c", "M_D_c", "M_E_c"},
                {"M_B_c", "M_D_c", "M_I_c"},
                {"M_B_c", "M_D_c", "M_H_c"},
                {"M_B_c", "M_D_c", "M_F_c"},
                {"M_B_c", "M_I_c", "M_S2_e"},
                {"M_B_c", "M_E_c", "M_S2_e"},
                {"M_B_c", "M_H_c", "M_S2_e"},
                {"M_B_c", "M_F_c", "M_S2_e"},
                {"M_I_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_F_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_D_c", "M_I_c", "M_J_c", "M_S1_e"},
                {"M_D_c", "M_F_c", "M_J_c", "M_S1_e"},
                {"M_H_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_E_c", "M_J_c", "M_S1_e", "M_S2_e"},
                {"M_D_c", "M_H_c", "M_J_c", "M_S1_e"},
                {"M_D_c", "M_E_c", "M_J_c", "M_S1_e"}
                ]
SIZE_SUBMIN_TAS=len(SEEDS_SUBMIN_TAS)

SEEDS_MIN_TAS = [{"M_B_c", "M_D_c", "M_E_c"} ,
            {"M_B_c", "M_D_c", "M_I_c"} ,
            {"M_B_c", "M_D_c", "M_H_c"} ,
            {"M_B_c", "M_D_c", "M_F_c"} ,
            {"M_B_c", "M_I_c", "M_S2_e"} ,
            {"M_B_c", "M_E_c", "M_S2_e"} ,
            {"M_B_c", "M_H_c", "M_S2_e"},
            {"M_B_c", "M_F_c", "M_S2_e"} ,
            ]
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

# solve values: 'reasoning', 'filter', 'guess_check', 'guess_check_div', 'hybrid'
# optim values: 'submin', 'min'

# ---------------------- TARGET ARE FORBIDDEN ----------------------
# ----------- SUBSETMIN ----------- 
def test_reasoning_submin_taf():
    solve="reasoning"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAF
    assert len(list_solution) == SIZE_SUBMIN_TAF

def test_filter_submin_taf():
    solve="filter"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAF
    assert len(list_solution) == SIZE_SUBMIN_TAF 

def test_gc_submin_taf():
    solve="guess_check"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAF
    assert len(list_solution) == SIZE_SUBMIN_TAF 

def test_gcd_submin_taf():
    solve="guess_check_div"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAF
    assert len(list_solution) == SIZE_SUBMIN_TAF 


def test_hybrid_submin_taf():
    solve="hybrid"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAF
    assert len(list_solution) == SIZE_SUBMIN_TAF


# ----------- MINIMIZE ----------- 
def test_reasoning_min_taf():
    solve="reasoning"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAF
    assert len(list_solution) == SIZE_MIN_TAF

def test_filter_min_taf():
    solve="filter"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAF
    assert len(list_solution) == SIZE_MIN_TAF 

def test_gc_min_taf():
    solve="guess_check"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAF
    assert len(list_solution) == SIZE_MIN_TAF 

def test_gcd_min_taf():
    solve="guess_check_div"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAF
    assert len(list_solution) == SIZE_MIN_TAF 


def test_hybrid_min_taf():
    solve="hybrid"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAF
    assert len(list_solution) == SIZE_MIN_TAF


# ---------------------- TARGET AS SEEDS ----------------------
# ----------- SUBSETMIN ----------- 
def test_reasoning_submin_tas():
    solve="reasoning"
    optim="submin"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAS
    assert len(list_solution) == SIZE_SUBMIN_TAS

def test_filter_submin_tas():
    solve="filter"
    optim="submin"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAS
    assert len(list_solution) == SIZE_SUBMIN_TAS 

def test_gc_submin_tas():
    solve="guess_check"
    optim="submin"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAS
    assert len(list_solution) == SIZE_SUBMIN_TAS 

def test_gcd_submin_tas():
    solve="guess_check_div"
    optim="submin"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAS
    assert len(list_solution) == SIZE_SUBMIN_TAS 


def test_hybrid_submin_tas():
    solve="hybrid"
    optim="submin"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_TAS
    assert len(list_solution) == SIZE_SUBMIN_TAS


# ----------- MINIMIZE ----------- 
def test_reasoning_min_tas():
    solve="reasoning"
    optim="min"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAS
    assert len(list_solution) == SIZE_MIN_TAS

def test_filter_min_tas():
    solve="filter"
    optim="min"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAS
    assert len(list_solution) == SIZE_MIN_TAS 

def test_gc_min_tas():
    solve="guess_check"
    optim="min"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAS
    assert len(list_solution) == SIZE_MIN_TAS 

def test_gcd_min_tas():
    solve="guess_check_div"
    optim="min"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAS
    assert len(list_solution) == SIZE_MIN_TAS 


def test_hybrid_min_tas():
    solve="hybrid"
    optim="min"
    targets_as_seeds=True
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim, targets_as_seeds)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_TAS
    assert len(list_solution) == SIZE_MIN_TAS