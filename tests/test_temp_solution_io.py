#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Regression test for github issue #26: a solution written to the guess_check/filter
temporary .tsv file must be readable back, even when its cobra flux dict contains
numpy scalar types. numpy >= 2.0 changed np.float64's repr from a bare number to
"np.float64(...)", which broke the previous str()/repr + quote-replace decoding
and made every solution found right before a timeout look unsatisfiable.
"""
from os import path, remove
from json import dumps, loads
import numpy as np
from seed2lp.file import save, load_tsv, is_valid_dir

TEST_DIR = path.dirname(path.abspath(__file__))
TMP_DIR = path.join(TEST_DIR, "tmp")
is_valid_dir(TMP_DIR)


def test_temp_solution_cobra_flux_roundtrip():
    cobra_flux = {"bio1": np.float64(18.04)}
    cobra_flux_json = dumps({k: float(v) for k, v in cobra_flux.items()})
    seeds = ["M_A_c", "M_B_c"]
    solution_temp = ["model_1", len(seeds), seeds, 5, cobra_flux_json]

    full_path = path.join(TMP_DIR, "test_issue26_temp_solution")
    try:
        save(full_path, "", solution_temp, "tsv", True)
        rows = load_tsv(full_path + ".tsv")
        assert len(rows) == 1
        parsed_flux = loads(rows[0][4])
        assert parsed_flux == {"bio1": 18.04}
    finally:
        if path.exists(full_path + ".tsv"):
            remove(full_path + ".tsv")
