#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description:
Regression tests for github issue #28: HybridReasoning.solve_hybrid() must not
report "Unsatisfiable problem" (or "Time out") when the solver subprocess never
had the chance to finish because it crashed, hit an I/O/XML error, or was
interrupted (Ctrl+C) - those are failures, not "no solution found".

These tests drive the real solve_hybrid()/wait_for_subprocess() methods (on a
minimal HybridReasoning stand-in that skips __init__) with a fake "filter"
target standing in for the multiprocessing worker, so the exact control flow
being fixed is exercised without needing a real network/clingo/cobra solve.
"""
import logging
from os import path
from time import sleep

import pytest

from seed2lp.reasoninghybrid import HybridReasoning

TEST_DIR = path.dirname(path.abspath(__file__))
TMP_DIR = path.join(TEST_DIR, "tmp")


class FakeReasoning(HybridReasoning):
    """Minimal stand-in exposing only what solve_hybrid() touches. Subclasses
    HybridReasoning (without calling its __init__) purely so the real
    wait_for_subprocess()/get_solution_from_temp() are available unmodified -
    this test exercises those exact methods, not reimplementations of them."""

    def __init__(self, time_limit, verbose=False):
        self.logger = logging.getLogger("s2lp_test_issue28")
        self.verbose = verbose
        self.time_limit = time_limit
        self.time_limit_minute = (time_limit / 60) if time_limit else None
        self.temp_dir = TMP_DIR
        self.temp_result_file = "test_issue28_never_written"
        self.optimum_found = False
        self.optimum = tuple()
        self.network = object()  # never touched: no temp file is ever written in these tests


def _messages(caplog):
    return [r.message for r in caplog.records]


def test_real_timeout_reports_timeout_not_a_crash(caplog):
    """The subprocess is still alive when the time budget runs out: a genuine
    time out, distinct from a crash. "Unsatisfiable problem" is still expected
    to follow when nothing was recovered from the temp file - that combination
    ("we timed out and found nothing") is legitimate and unchanged; it is only
    the crash case that must no longer be labeled "Unsatisfiable problem"."""
    def slow_filter(queue, full_option, asp_files, search_mode, full_path, is_one_model):
        sleep(2)
        queue.put([None, {}, 1.0, 1.0, 0])

    fake = FakeReasoning(time_limit=0.3)
    fake.filter = slow_filter

    with caplog.at_level(logging.ERROR, logger="s2lp_test_issue28"):
        time_solve, time_ground, solution_list, number_rejected = fake.solve_hybrid(
            "filter", [], [], "submin", False
        )

    messages = _messages(caplog)
    assert any("Time out" in m for m in messages)
    assert not any("Solver process failed" in m for m in messages)
    assert not solution_list


def test_subprocess_crash_reports_failure_not_unsatisfiable(caplog):
    """The subprocess raises (e.g. a malformed SBML/XML file) before ever
    calling queue.put(): must be reported as a failure, not as UNSAT.

    queue.get() cannot tell a crashed subprocess apart from a slow one purely
    from the exception it raises (Empty either way) - the crash is only
    detected via p.is_alive() once that Empty fires, so the failure message
    carries the exit code, not the child's exception text (that text only
    ever reaches the child's own stderr traceback, invisible to the parent)."""
    def crashing_filter(queue, full_option, asp_files, search_mode, full_path, is_one_model):
        raise ValueError("simulated malformed XML input")

    fake = FakeReasoning(time_limit=0.3)
    fake.filter = crashing_filter

    with caplog.at_level(logging.ERROR, logger="s2lp_test_issue28"):
        time_solve, time_ground, solution_list, number_rejected = fake.solve_hybrid(
            "filter", [], [], "submin", False
        )

    messages = _messages(caplog)
    assert any("Solver process failed unexpectedly" in m for m in messages)
    assert any("exited with code" in m for m in messages)
    assert not any(m.startswith("Time out") for m in messages)
    assert not any("Unsatisfiable problem" in m for m in messages)
    assert not solution_list


def test_no_time_limit_crash_is_not_silently_relabeled_unsat(caplog):
    """With no -tl set (self.time_limit is None, the CLI default), a naive
    single blocking queue.get(timeout=None) would hang forever on a crashed
    subprocess (nothing is ever put on the queue, and there is no timeout to
    raise Empty). wait_for_subprocess()'s polling must still detect the dead
    subprocess within one poll interval and report a failure, not hang and
    not silently default to "unsat" (the old
    `not self.time_limit -> unsat = True` heuristic used to do the latter)."""
    def crashing_filter(queue, full_option, asp_files, search_mode, full_path, is_one_model):
        raise RuntimeError("simulated crash with no time limit set")

    fake = FakeReasoning(time_limit=None)
    fake.filter = crashing_filter

    with caplog.at_level(logging.ERROR, logger="s2lp_test_issue28"):
        fake.solve_hybrid("filter", [], [], "submin", False)

    messages = _messages(caplog)
    assert any("Solver process failed unexpectedly" in m for m in messages)
    assert not any("Unsatisfiable problem" in m for m in messages)


def test_keyboard_interrupt_propagates_and_still_cleans_up_process(monkeypatch):
    """Ctrl+C during queue.get() must stop the program (propagate), not be
    silently swallowed and reported as UNSAT/timeout - and the subprocess must
    still be terminated (the `finally` block) even though the exception escapes."""
    import multiprocessing

    def noop_filter(queue, full_option, asp_files, search_mode, full_path, is_one_model):
        sleep(0.2)
        queue.put([None, {}, 1.0, 1.0, 0])

    terminated = []
    real_terminate = multiprocessing.Process.terminate

    def spy_terminate(self):
        terminated.append(True)
        return real_terminate(self)

    def raise_keyboard_interrupt(self, *args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(multiprocessing.Process, "terminate", spy_terminate)
    monkeypatch.setattr(multiprocessing.queues.Queue, "get", raise_keyboard_interrupt)

    fake = FakeReasoning(time_limit=5)
    fake.filter = noop_filter

    with pytest.raises(KeyboardInterrupt):
        fake.solve_hybrid("filter", [], [], "submin", False)

    assert terminated == [True]
