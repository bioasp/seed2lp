#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Tests for seed2lp's community mode (multi-species metabolic networks with
metabolite transfers between species), using the toy community network at
networks/toys_communities/ (species B1..B4, community file com1.txt, plus two
extra community files added here: com_b4_only.txt for a single-species edge
case and com_b1_b2.txt for a smaller, partial community).

Unlike the single-network tests (tests/utils.py::search_seed, which drives
Reasoning/Hybrid/FBA objects directly in-process), these tests invoke the real
CLI end-to-end and parse the resulting JSON. Community mode's ComReasoning
results are not tagged the same way single-network results are (most search
modes collapse into the generic "Other"/"Enumeration" bucket - see
network.py's add_result_seeds), and - more importantly - community
bisteps/delsupset always run through real multiprocessing subprocesses
(run_multiprocess()/solve_bisteps()/solve_delete_superset()), which is exactly
the mechanism fixed for github issue 28 and its two follow-up bugs (the
Process(target=...) synchronous-call bug that made -tl a no-op, and the empty
cobra-flux JSON crash when reading the temp file back for the "reasoning"
step). A CLI/subprocess-level test is a more faithful regression guard for
that mechanism than driving the objects directly in-process would be - it is
the only way these bugs actually get exercised.

All solution counts and seed sets below were captured from real runs and
double-checked for determinism (two independent runs of the same command
produced identical solution sets, compared as sets of seed-tuples so run
order doesn't matter) before being hardcoded as regression baselines.

NOTE: these tests exist only in the GitLab dev repo for now - they still need
to be ported to the GitHub mirror (see [[project_dual_repo_release_workflow]]
in memory) the next time changes are synced there, same as every other test.
"""
import json
import subprocess
import sys
from os import path

import pytest

TEST_DIR = path.dirname(path.abspath(__file__))
REPO_ROOT = path.dirname(TEST_DIR)
COMMUNITIES_DIR = path.join(REPO_ROOT, "networks", "toys_communities", "communities")
SBMLDIR = path.join(REPO_ROOT, "networks", "toys_communities", "sbml")

COM_ALL = path.join(COMMUNITIES_DIR, "com1.txt")           # B1, B2, B3, B4
COM_B4_ONLY = path.join(COMMUNITIES_DIR, "com_b4_only.txt")  # B4 alone: no transfers possible
COM_B1_B2 = path.join(COMMUNITIES_DIR, "com_b1_b2.txt")      # B1 + B2 only: smaller community

########################################################

def run_community(out_dir, comfile=COM_ALL, extra_args=None, timeout=30):
    """Run `seed2lp community` end-to-end and return (CompletedProcess, results dict or None)."""
    args = [sys.executable, "-m", "seed2lp", "community", comfile, SBMLDIR, str(out_dir)] + (extra_args or [])
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    json_files = list(out_dir.glob("*_results.json"))
    data = json.loads(json_files[0].read_text()) if json_files else None
    return proc, data


def get_solutions(data, top_key="REASONING", sub_key=None):
    """Return the {model_name: {"size": ..., "Set of seeds": [...], ...}} solutions
    dict for one search key (github issue 27 schema: each solution is a plain dict,
    not a flat tagged list)."""
    results = data["RESULTS"][top_key]
    if sub_key is None:
        assert len(results) == 1, f"expected exactly one search key, got {list(results)}"
        sub_key = next(iter(results))
    return results[sub_key].get("solutions", {})


def seed_sets(solutions):
    """Return the set of solutions as frozenset-of-seeds, order-independent."""
    return {frozenset(sol["Set of seeds"]) for sol in solutions.values()}


def has_transfers(solutions):
    return any(len(sol.get("Set of transferred", [])) > 0 for sol in solutions.values())

########################################################


def test_bisteps_reasoning_needs_cross_species_transfers(tmp_path):
    """The 4-species community must actually use transfers: B1 and B3 each have
    a metabolite (M_F_c / M_G_c for B1, nothing for B3 in this exact set) that
    only becomes reachable through another species' export - a pure per-species
    topological analysis of B1/B3 in isolation finds them unreachable, so this
    also guards against community transfer silently stopping being used."""
    proc, data = run_community(tmp_path, extra_args=["-cm", "bisteps", "-so", "reasoning"])
    assert proc.returncode == 0, proc.stderr
    solutions = get_solutions(data)
    assert len(solutions) == 7
    assert has_transfers(solutions)


def test_bisteps_filter_and_guess_check_agree(tmp_path):
    """filter and guess_check both add a cobra flux check on top of the same
    reasoning search: on this toy community they must find the same 6 minimal
    solutions (a smaller subset of the 7 found by plain reasoning, since flux
    feasibility rules out one of them)."""
    (tmp_path / "filter").mkdir()
    proc_f, data_f = run_community(tmp_path / "filter", extra_args=["-cm", "bisteps", "-so", "filter"])
    (tmp_path / "gc").mkdir()
    proc_g, data_g = run_community(tmp_path / "gc", extra_args=["-cm", "bisteps", "-so", "guess_check"])

    assert proc_f.returncode == 0, proc_f.stderr
    assert proc_g.returncode == 0, proc_g.stderr

    solutions_f = get_solutions(data_f)
    solutions_g = get_solutions(data_g)
    assert len(solutions_f) == 6
    assert len(solutions_g) == 6
    assert seed_sets(solutions_f) == seed_sets(solutions_g)


def test_bisteps_and_delsupset_reasoning_find_the_same_minimal_solutions(tmp_path):
    """bisteps and delsupset are two different solving strategies for the same
    subset-minimal enumeration problem - on this toy community they must
    converge to the exact same set of 7 minimal solutions."""
    (tmp_path / "bisteps").mkdir()
    proc_b, data_b = run_community(tmp_path / "bisteps", extra_args=["-cm", "bisteps", "-so", "reasoning"])
    (tmp_path / "delsupset").mkdir()
    proc_d, data_d = run_community(tmp_path / "delsupset", extra_args=["-cm", "delsupset", "-so", "reasoning"])

    assert proc_b.returncode == 0, proc_b.stderr
    assert proc_d.returncode == 0, proc_d.stderr

    solutions_b = get_solutions(data_b)
    solutions_d = get_solutions(data_d)
    assert len(solutions_b) == 7
    assert len(solutions_d) == 7
    assert seed_sets(solutions_b) == seed_sets(solutions_d)


def test_global_mode_hits_the_solution_cap(tmp_path):
    """"global" community mode reuses the single-network Reasoning/HybridReasoning
    machinery directly (super().solve()), not run_multiprocess() - so unlike
    bisteps/delsupset (which naturally exhaust at 7 solutions on this toy
    community), it enumerates until the default -nbs cap (10) is reached."""
    proc, data = run_community(tmp_path, extra_args=["-cm", "global", "-so", "reasoning"])
    assert proc.returncode == 0, proc.stderr
    solutions = get_solutions(data)
    assert len(solutions) == 10


def test_single_species_community_has_one_solution_and_no_transfers(tmp_path):
    """A one-species "community" (B4 alone) cannot use any transfer - it must
    behave like a plain single-network search for B4's own biomass. B4 has no
    branching (unlike B2) and no dead-end cofactor (unlike B1/B3), so it has
    exactly one minimal seed set."""
    proc, data = run_community(tmp_path, comfile=COM_B4_ONLY, extra_args=["-cm", "bisteps", "-so", "reasoning"])
    assert proc.returncode == 0, proc.stderr
    solutions = get_solutions(data)
    assert len(solutions) == 1
    assert not has_transfers(solutions)
    (solution,) = solutions.values()
    assert solution["size"] == 5
    assert set(solution["Set of seeds"]) == {
        "M_B4_Q_e", "M_B4_R_e", "M_B4_S_e", "M_B4_T_e", "M_B4_U_e",
    }


def test_partial_community_allows_smaller_seed_sets(tmp_path):
    """A 2-species community (B1+B2 only) has fewer total biomass objectives to
    satisfy than the full 4-species one, so its smallest minimal solution (2
    seeds) is smaller than any solution found for the full community (8+ seeds)
    - a differentiated regression check that community composition, not just
    solve mode, changes the result."""
    proc, data = run_community(tmp_path, comfile=COM_B1_B2, extra_args=["-cm", "bisteps", "-so", "reasoning"])
    assert proc.returncode == 0, proc.stderr
    solutions = get_solutions(data)
    assert len(solutions) > 0
    smallest = min(sol["size"] for sol in solutions.values())
    assert smallest == 2


def test_short_time_limit_does_not_hang_or_crash(tmp_path):
    """Regression guard for github issue 28 in community mode: before the fix,
    -tl had zero effect in bisteps/delsupset (the subprocess never actually
    ran in the background), and a crash with no -tl at all hung forever. An
    unreasonably short -tl must make the run return quickly (well under the
    30s subprocess timeout) with a clean exit, not hang and not crash."""
    proc, data = run_community(
        tmp_path, extra_args=["-cm", "bisteps", "-so", "reasoning", "-tl", "0.0005"], timeout=15
    )
    assert proc.returncode == 0, proc.stderr
    assert data is not None
    assert "Time out" in proc.stdout or "Time out" in proc.stderr


def test_unknown_species_in_community_file_reports_clean_error(tmp_path):
    """A community file naming a species with no matching SBML file must fail
    cleanly (exit code 1, a readable error naming the missing file), not with
    a raw traceback and not by hanging."""
    bad_comfile = tmp_path / "com_bad.txt"
    bad_comfile.write_text("B1\nB99_DOES_NOT_EXIST")
    (tmp_path / "out").mkdir()

    proc, data = run_community(
        tmp_path / "out", comfile=str(bad_comfile), extra_args=["-cm", "bisteps", "-so", "reasoning"], timeout=15
    )
    assert proc.returncode == 1
    assert "B99_DOES_NOT_EXIST" in proc.stdout + proc.stderr
    assert "Traceback" not in proc.stdout + proc.stderr
