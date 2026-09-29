#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Regression tests for github issue 27: the results JSON's "solutions" entries
became plain dicts ({"size": N, "Set of seeds": [...], ...}) instead of flat
tagged lists (["size", N, "Set of seeds", [...], ...]).

This is a breaking schema change with no backward-compat layer (by explicit
decision - see memory), so it must be verified from both ends: the write side
(the new shape is actually what lands on disk, for every producer: plain
reasoning/filter/guess_check, Hybrid-lpx/FBA, community) and the read side
(seed2lp's own reload path, network.py::convert_data_to_resmod(), used by the
flux/scope/fluxcom CLI commands to re-open a previously produced results.json -
these are real, documented, generic readers of this exact schema, not just an
internal detail). A round-trip through the real CLI (produce a results.json,
then feed it back into flux/scope/fluxcom) is the only way to catch a producer
and a consumer silently drifting apart, which is exactly the kind of bug a
pure unit test on either side alone would miss.
"""
import json
import subprocess
import sys
from os import path

from seed2lp import utils
from seed2lp.file import load_json
from seed2lp.network import Network

TEST_DIR = path.dirname(path.abspath(__file__))
REPO_ROOT = path.dirname(TEST_DIR)
INFILE = path.join(TEST_DIR, "network", "sbml", "toy_paper_no_reversible.sbml")
COM_ALL = path.join(REPO_ROOT, "networks", "toys_communities", "communities", "com1.txt")
SBMLDIR = path.join(REPO_ROOT, "networks", "toys_communities", "sbml")

########################################################

def run_seed2lp(args, timeout=30):
    full_args = [sys.executable, "-m", "seed2lp"] + args
    return subprocess.run(full_args, capture_output=True, text=True, timeout=timeout)


def one_results_json(out_dir):
    json_files = list(out_dir.glob("*_results.json"))
    assert len(json_files) == 1, f"expected exactly one results json in {out_dir}, found {json_files}"
    return json.loads(json_files[0].read_text())

########################################################


def test_target_guess_check_json_shape_and_reload(tmp_path):
    """The single-network filter/guess_check producer (complete_solutions())
    must write plain dicts with "size"/"Set of seeds"/"Cobra flux" (no
    "Set of transferred" - not community), and that file must be re-readable
    by both `flux` and `scope` without error."""
    search_dir = tmp_path / "search"
    search_dir.mkdir()
    proc = run_seed2lp(["target", INFILE, str(search_dir), "-so", "guess_check", "-m", "subsetmin"])
    assert proc.returncode == 0, proc.stderr

    data = one_results_json(search_dir)
    solutions = data["RESULTS"]["REASONING"]["SUBSET MINIMAL ENUMERATION GUESS-CHECK"]["solutions"]
    assert len(solutions) > 0
    for solution in solutions.values():
        assert isinstance(solution, dict)
        assert set(solution.keys()) == {"size", "Set of seeds", "Cobra flux"}
        assert solution["size"] == len(solution["Set of seeds"])
        assert isinstance(solution["Cobra flux"], dict)

    result_file = str(next(search_dir.glob("*_results.json")))

    flux_dir = tmp_path / "flux"
    flux_dir.mkdir()
    proc_flux = run_seed2lp(["flux", INFILE, result_file, str(flux_dir)])
    assert proc_flux.returncode == 0, proc_flux.stderr
    assert "Traceback" not in proc_flux.stdout + proc_flux.stderr

    scope_dir = tmp_path / "scope"
    scope_dir.mkdir()
    proc_scope = run_seed2lp(["scope", INFILE, result_file, str(scope_dir)])
    assert proc_scope.returncode == 0, proc_scope.stderr
    assert "Traceback" not in proc_scope.stdout + proc_scope.stderr


def test_fba_json_shape_and_reload(tmp_path):
    """The Hybrid-lpx/FBA producer (clingo_lpx.result_convert()) uses a
    different, unrelated set of optional keys ("reaction_flux" instead of
    "Cobra flux", and an optional nested "accumulation avoid with seeds" - a
    dict with its own "size"/"Set of seeds"). Both must round-trip through
    `flux` too (flux/scope explicitly special-case solver_type == "FBA")."""
    search_dir = tmp_path / "search"
    search_dir.mkdir()
    proc = run_seed2lp(["fba", INFILE, str(search_dir), "-m", "subsetmin"])
    assert proc.returncode == 0, proc.stderr

    data = one_results_json(search_dir)
    solutions = data["RESULTS"]["FBA"]["SUBSET MINIMAL ENUMERATION"]["solutions"]
    assert len(solutions) > 0
    saw_accumulation_key = False
    for solution in solutions.values():
        assert isinstance(solution, dict)
        assert "size" in solution and "Set of seeds" in solution
        assert "reaction_flux" in solution
        assert "Cobra flux" not in solution  # FBA-specific key, not the cobra one
        assert solution["size"] == len(solution["Set of seeds"])
        if "accumulation avoid with seeds" in solution:
            saw_accumulation_key = True
            accu = solution["accumulation avoid with seeds"]
            assert set(accu.keys()) == {"size", "Set of seeds"}
            assert accu["size"] == len(accu["Set of seeds"])
    # this toy network is known (from a manual run) to produce at least one
    # solution needing an accumulation-avoiding seed - fail loudly if that
    # ever stops happening, since it's the only coverage of this nested key
    assert saw_accumulation_key, "expected at least one solution with 'accumulation avoid with seeds'"

    result_file = str(next(search_dir.glob("*_results.json")))
    flux_dir = tmp_path / "flux"
    flux_dir.mkdir()
    proc_flux = run_seed2lp(["flux", INFILE, result_file, str(flux_dir)])
    assert proc_flux.returncode == 0, proc_flux.stderr
    assert "Traceback" not in proc_flux.stdout + proc_flux.stderr


def test_community_json_shape_and_fluxcom_reload(tmp_path):
    """The community producer must write "Set of transferred" alongside
    "Cobra flux", and the file must be re-readable by `fluxcom` (the
    community-aware sibling of `flux`, which also needs the transfer info to
    account for exchanged metabolites in each species' flux balance)."""
    search_dir = tmp_path / "search"
    search_dir.mkdir()
    proc = run_seed2lp(["community", COM_ALL, SBMLDIR, str(search_dir), "-cm", "bisteps", "-so", "reasoning"])
    assert proc.returncode == 0, proc.stderr

    data = one_results_json(search_dir)
    solutions = data["RESULTS"]["REASONING"]["SUBSET MINIMAL ENUMERATION"]["solutions"]
    assert len(solutions) > 0
    for solution in solutions.values():
        assert isinstance(solution, dict)
        assert "Set of transferred" in solution
        assert isinstance(solution["Set of transferred"], list)

    result_file = str(next(search_dir.glob("*_results.json")))
    fluxcom_dir = tmp_path / "fluxcom"
    fluxcom_dir.mkdir()
    proc_fluxcom = run_seed2lp(["fluxcom", COM_ALL, SBMLDIR, result_file, str(fluxcom_dir)])
    assert proc_fluxcom.returncode == 0, proc_fluxcom.stderr
    assert "Traceback" not in proc_fluxcom.stdout + proc_fluxcom.stderr


def test_minimize_one_model_json_shape(tmp_path):
    """write_one_model_solution() (minimize mode, single "model_one_solution"
    entry, no cobra flux at all) must also produce a plain dict."""
    search_dir = tmp_path / "search"
    search_dir.mkdir()
    proc = run_seed2lp(["target", INFILE, str(search_dir), "-so", "reasoning", "-m", "minimize"])
    assert proc.returncode == 0, proc.stderr

    data = one_results_json(search_dir)
    solutions = data["RESULTS"]["REASONING"]["MINIMIZE OPTIMUM"]["solutions"]
    solution = solutions["model_one_solution"]
    assert isinstance(solution, dict)
    assert set(solution.keys()) == {"size", "Set of seeds"}
    assert solution["size"] == len(solution["Set of seeds"])


def test_custom_targets_are_flattened_and_restored_on_reload(tmp_path):
    """A single-network search with a custom -tf targets file must:
    1. Write "USER DATA"/"TARGETS" flattened as a plain list (every target maps
       to itself for a single network, so the wrapping list is redundant).
    2. Be restored correctly on reload: before the fix, flux/scope/fluxcom
       never read TARGETS back at all (network.targets stayed empty after
       reload, silently discarding whatever custom targets the original
       search used - discovered while implementing the flattening above)."""
    targets_file = tmp_path / "custom_targets.txt"
    targets_file.write_text("M_H_c")

    search_dir = tmp_path / "search"
    search_dir.mkdir()
    proc = run_seed2lp(["target", INFILE, str(search_dir), "-so", "reasoning", "-m", "subsetmin",
                         "-tf", str(targets_file)])
    assert proc.returncode == 0, proc.stderr

    data = one_results_json(search_dir)
    assert data["USER DATA"]["TARGETS"] == ["M_H_c"]

    # Simulate exactly what network_flux()/scope() do on reload: construct the
    # Network, then restore targets from the JSON the same way they do.
    network = Network(INFILE, to_print=False, input_dict={"Objective": data["NETWORK"]["OBJECTIVE"][0][1]}, verbose=False)
    assert not network.targets, "sanity check: targets should start empty before the fix is applied"
    network.targets = utils.targets_from_json(data["USER DATA"]["TARGETS"])
    assert network.targets == {"M_H_c": ["M_H_c"]}


def test_targets_from_json_accepts_both_shapes():
    """Single-network TARGETS is flattened to a list; community TARGETS stays
    a dict (one target can group several species-prefixed ids there). The
    reload helper must accept either shape unchanged/converted correctly."""
    assert utils.targets_from_json(["M_a_c", "M_b_c"]) == {"M_a_c": ["M_a_c"], "M_b_c": ["M_b_c"]}
    community_shape = {"M_a": ["M_B1_a_c", "M_B2_a_c"]}
    assert utils.targets_from_json(community_shape) == community_shape
