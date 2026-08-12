#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Test seed2lp
"""
from os import path
from .utils import search_seed

################ DIRECTORIES AND FILES ###################
TEST_DIR = path.dirname(path.abspath(__file__))

# In This Network, The reaction R2 J + A -> C is deleted
# C is alone in the network, with an import/export reaction, 
# therefore C is always a seed by design in Full Network
# J is alone never involved in any reaction, J is never a seed
# All reaction are not reversible 
# except import/export reaction for exchange metabolite S1, S2 C and G
INFILE = path.join(TEST_DIR,'network/sbml/toy_paper_no_rev_rm_R2.sbml')
######################################################## 


################### FIXED VARIABLES ####################
RUN_MODE="full"
######################################################## 


################ EXPECTED SOLUTIONS ##################
# Same results for subset minimal and minimize
SEEDS_REASONING = [{'M_C_c', 'M_F_c', 'M_S1_e', 'M_S2_e'},
                    {'M_C_c', 'M_I_c', 'M_S1_e', 'M_S2_e'},
                    {'M_C_c', 'M_H_c', 'M_S1_e', 'M_S2_e'},
                    {'M_C_c', 'M_E_c', 'M_S1_e', 'M_S2_e'}
                    ]
SIZE_REASONING=len(SEEDS_REASONING)

# Same results for Filter, Guess-Check and Guess-Check Diversity
# Same results for subset minimal and minimize
# F is an objective reactant (therefore a target), and it is choosen 
# event if target is forbidden because in Full Network mode, 
# all metabolite are Target and can't be forbidden
SEEDS_HYB_COBRA = [{'M_C_c', 'M_F_c', 'M_S1_e', 'M_S2_e'}]
SIZE_HYB_COBRA=len(SEEDS_HYB_COBRA)

# metabolite A is a seed for hybrid only to create an export reaction
# When B is a seed, The reaction S1 -> A+B is not activated in FBA
# A is therefore not accumlated
SEEDS_SUBMIN_HYBRID = [{'M_C_c', 'M_F_c', 'M_S1_e', 'M_S2_e'},
                       {'M_A_c', 'M_C_c', 'M_I_c', 'M_S1_e', 'M_S2_e'},
                       {'M_B_c', 'M_C_c', 'M_I_c', 'M_S1_e', 'M_S2_e'},
                       {'M_A_c', 'M_C_c', 'M_H_c', 'M_S1_e', 'M_S2_e'},
                       {'M_B_c', 'M_C_c', 'M_H_c', 'M_S1_e', 'M_S2_e'},
                       {'M_A_c', 'M_C_c', 'M_E_c', 'M_S1_e', 'M_S2_e'},
                       {'M_B_c', 'M_C_c', 'M_E_c', 'M_S1_e', 'M_S2_e'}
                        ]
SIZE_SUBMIN_HYBRID=len(SEEDS_SUBMIN_HYBRID)

# F is an objective reactant (therefore a target), and it is choosen 
# event if target is forbidden because in Full Network mode, 
# all metabolite are Target and can't be forbidden
SEEDS_MIN_HYBRID = [{'M_C_c', 'M_F_c', 'M_S1_e', 'M_S2_e'}]
SIZE_MIN_HYBRID=len(SEEDS_MIN_HYBRID)

######################################################## 



######################### TESTS ########################
#TODO: 
#     - test with accumulation
#     - test keep import reaction and topological injection
#     - find Network to have different value in Filter / Gues_check / Guess_Check_Div
#     - find Network to have different value with accumulation authorized
#     - test without maximization for hybrid
#     - test unsat
#     - test possible_seeds (subset of seed that maximize number of producible targets)
#     - test changing objective

# solve values: 'reasoning', 'filter', 'guess_check', 'guess_check_div', 'hybrid'
# optim values: 'submin', 'min'

# ----------- SUBSETMIN ----------- 
def test_reasoning_submin():
    solve="reasoning"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_REASONING
    assert len(list_solution) == SIZE_REASONING

def test_filter_submin():
    solve="filter"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_HYB_COBRA
    assert len(list_solution) == SIZE_HYB_COBRA 

def test_gc_submin():
    solve="guess_check"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_HYB_COBRA
    assert len(list_solution) == SIZE_HYB_COBRA 

def test_gcd_submin():
    solve="guess_check_div"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_HYB_COBRA
    assert len(list_solution) == SIZE_HYB_COBRA 


def test_hybrid_submin():
    solve="hybrid"
    optim="submin"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_SUBMIN_HYBRID
    assert len(list_solution) == SIZE_SUBMIN_HYBRID


# ----------- MINIMIZE ----------- 
def test_reasoning_min():
    solve="reasoning"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_REASONING
    assert len(list_solution) == SIZE_REASONING

def test_filter_min():
    solve="filter"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_HYB_COBRA
    assert len(list_solution) == SIZE_HYB_COBRA 

def test_gc_min():
    solve="guess_check"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_HYB_COBRA
    assert len(list_solution) == SIZE_HYB_COBRA 

def test_gcd_min():
    solve="guess_check_div"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_HYB_COBRA
    assert len(list_solution) == SIZE_HYB_COBRA 


def test_hybrid_min():
    solve="hybrid"
    optim="min"
    list_solution=search_seed(INFILE, RUN_MODE, solve, optim)
    for solution in list_solution:
        assert set(solution) in SEEDS_MIN_HYBRID
    assert len(list_solution) == SIZE_MIN_HYBRID