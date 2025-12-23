#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Test seed2lp
"""
from os import path
from .utils import get_network
import re

##### ###### ##### DIRECTORIES AND FILES ###################
TEST_DIR = path.dirname(path.abspath(__file__))

# All reaction are not reversible 
# except import/export reaction for exchange metabolite S1, S2 C and G
INFILE = path.join(TEST_DIR,'network/sbml/toy_paper.sbml')
######################################################## 


################### FIXED VARIABLES ####################

######################################################## 



################# EXPECTED SOLUTIONS ###################
EXCH = {"R_EX_S1", "R_EX_S2", "R_EX_C", "R_EX_G"}

DEL = {"R_R2"}

# For exchange reaction when import reaction deleted
# The deletion is on ASP facts with atom reaction and bounds prefixed with "rm_" 
# and product or reactant prefixed with "rm_" 
REV = {'R_BIOMASS', 'R_EX_S1', 'R_EX_S2', 'R_EX_C', 'R_EX_G'}

META_EXCH = {"R_R7"}

FORBID_TAF = {"M_F_c"}

RM_RXN = ['rm_reaction("rev_R_EX_S1").',
        'rm_reaction("rev_R_EX_S2").',
        'rm_reaction("rev_R_EX_C").',
        'rm_reaction("rev_R_EX_G").',
        'rm_bounds("rev_R_EX_S1","0.0000000000","1000.0000000000").',
        'rm_bounds("rev_R_EX_S2","0.0000000000","1000.0000000000").',
        'rm_bounds("rev_R_EX_C","0.0000000000","1000.0000000000").',
        'rm_bounds("rev_R_EX_G","0.0000000000","1000.0000000000").',
        'rm_product("M_S1_e","1.0000000000","rev_R_EX_S1","exchange","M_S1_e","toy_paper").',
        'rm_product("M_S2_e","1.0000000000","rev_R_EX_S2","exchange","M_S2_e","toy_paper").',
        'rm_product("M_C_c","1.0000000000","rev_R_EX_C","exchange","M_C_c","toy_paper").',
        'rm_product("M_G_c","1.0000000000","rev_R_EX_G","exchange","M_G_c","toy_paper").'
        ]
SIZE_RM_RXN=len(RM_RXN)

SEED_TI = ['seed("M_S1_e","exchange","M_S1_e").',
        'seed("M_S2_e","exchange","M_S2_e").',
        'seed("M_C_c","exchange","M_C_c").',
        'seed("M_G_c","exchange","M_G_c").'
        ]
SIZE_SEED_TI=len(SEED_TI)


MATCH_RM = 'rm_'
MATCH_SEED = 'seed\('

######################################################## 

def test_exchange():
    run_mode = "full"
    targets_as_seeds = False
    topological_injection = False
    keep_import_reactions = False

    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    assert set(network.exchanged_reactions) == EXCH


def test_delete():
    run_mode = "full"
    targets_as_seeds = False
    topological_injection = False
    keep_import_reactions = False

    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    assert set(network.deleted_reactions) == DEL


def test_rev_modified():
    run_mode = "full"
    targets_as_seeds = False
    topological_injection = False
    keep_import_reactions = False

    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    assert set(network.reversible_modified_reactions.keys()) == REV


# import reaction removed, prefixed by "rm_" on atom 
# reaction reaction and bounds 
# and 
def test_rm_rxn():
    run_mode = "full"
    targets_as_seeds = False
    topological_injection = False
    keep_import_reactions = False

    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    network.convert_to_facts()

    rm_list_found=re.findall(MATCH_RM, network.facts)
    size_rm_found=len(rm_list_found)
    assert size_rm_found == SIZE_RM_RXN

    seed_list_found=re.findall(MATCH_SEED, network.facts)
    size_seed_found=len(seed_list_found)
    assert size_seed_found == 0
    
    for rm in RM_RXN:
        assert rm in network.facts
    
# import reaction kept, no prefix on atom reaction
def test_kir():
    run_mode = "full"
    targets_as_seeds = False
    topological_injection = False
    keep_import_reactions = True

    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    network.convert_to_facts()
    
    rm_list_found=re.findall(MATCH_RM, network.facts)
    size_rm_found=len(rm_list_found)
    assert size_rm_found == 0

    seed_list_found=re.findall(MATCH_SEED, network.facts)
    size_seed_found=len(seed_list_found)
    assert size_seed_found == 0


# import reaction kept, no prefix on atom reaction
# atom seed added product or reactant (dependeing way it is written on sbml)
def test_ti():
    run_mode = "full"
    targets_as_seeds = False
    topological_injection = True
    keep_import_reactions = True

    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    network.convert_to_facts()

    rm_list_found=re.findall(MATCH_RM, network.facts)
    size_rm_found=len(rm_list_found)
    assert size_rm_found == 0

    seed_list_found=re.findall(MATCH_SEED, network.facts)
    size_seed_found=len(seed_list_found)
    assert size_seed_found == SIZE_SEED_TI
    for seed in SEED_TI:
        assert seed in network.facts



def test_taf():
    run_mode = "target"
    targets_as_seeds = False
    topological_injection = False
    keep_import_reactions = False
    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    assert set(network.forbidden_seeds) == FORBID_TAF


def test_tas():
    run_mode = "target"
    targets_as_seeds = True
    topological_injection = False
    keep_import_reactions = False
    network = get_network(INFILE, run_mode, targets_as_seeds, 
                    topological_injection, keep_import_reactions)
    # check if list is empty
    assert not network.forbidden_seeds