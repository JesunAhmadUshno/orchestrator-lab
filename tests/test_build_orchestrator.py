"""Unit tests for the Level 2 Build parallel orchestrator."""
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-1-learn"))
sys.path.insert(0, os.path.join(ROOT, "level-2-build"))
from orchestrator import OrchestratorError  # noqa: E402
from orchestrator_build import (  # noqa: E402
    ParallelSupervisor, build_parallel_scenario, validate_build_graph,
)


def make_task(tid, deps=None, **over):
    task = {"id": tid, "name": tid.lower(), "worker": "Worker",
            "dependencies": deps or [], "cost_units": 1, "work_steps": 1,
            "step_budget": 3, "fail_times": 0, "payload": "one two",
            "sleep_seconds": 0.01, "timeout_seconds": 2.0}
    task.update(over)
    return task


class TestParallel(unittest.TestCase):
    def test_parallel_speedup(self):
        # 4 independent tasks sleeping 0.30s each: sequential would
        # take about 1.20s; a 4-worker pool should finish well under.
        tasks = [make_task("P%d" % i, sleep_seconds=0.30) for i in range(1, 5)]
        start = time.monotonic()
        result = ParallelSupervisor(max_workers=4, max_retries=0).run(tasks)
        elapsed = time.monotonic() - start
        self.assertEqual(result["summary"]["succeeded"], 4)
        self.assertLess(elapsed, 0.75)

    def test_order_independence_of_records(self):
        # The slowest task is listed first; records must still come
        # back in topological (sorted wave) order, not finish order.
        tasks = [make_task("A", sleep_seconds=0.25),
                 make_task("B", sleep_seconds=0.01),
                 make_task("C", sleep_seconds=0.01),
                 make_task("D", deps=["A", "B", "C"], sleep_seconds=0.01)]
        result = ParallelSupervisor(max_workers=4, max_retries=0).run(tasks)
        self.assertEqual([r["task_id"] for r in result["tasks"]],
                         ["A", "B", "C", "D"])
        self.assertEqual(result["summary"]["succeeded"], 4)

    def test_dependency_waits_for_slow_parent(self):
        tasks = [make_task("A", sleep_seconds=0.20),
                 make_task("B", deps=["A"], sleep_seconds=0.01)]
        result = ParallelSupervisor(max_workers=4, max_retries=0).run(tasks)
        self.assertEqual(result["waves"], [["A"], ["B"]])
        self.assertEqual(result["summary"]["status"], "complete")


class TestTimeout(unittest.TestCase):
    def test_timeout_fires_before_worker_finishes(self):
        tasks = [make_task("SLOW", sleep_seconds=0.50, timeout_seconds=0.05)]
        start = time.monotonic()
        result = ParallelSupervisor(max_workers=2, max_retries=0).run(tasks)
        elapsed = time.monotonic() - start
        rec = result["tasks"][0]
        self.assertEqual(rec["status"], "failed")
        self.assertIn("timeout", rec["error"])
        self.assertEqual(rec["timeout_attempts"], 1)
        self.assertLess(elapsed, 0.40)

    def test_timeout_is_retried_then_fails(self):
        tasks = [make_task("SLOW", sleep_seconds=0.50, timeout_seconds=0.05)]
        result = ParallelSupervisor(
            max_workers=2, max_retries=1, backoff_base_seconds=0.01).run(tasks)
        rec = result["tasks"][0]
        self.assertEqual(rec["status"], "failed")
        self.assertEqual(rec["attempts"], 2)
        self.assertEqual(rec["timeout_attempts"], 2)
        self.assertEqual(rec["retries_used"], 1)
        self.assertEqual(rec["backoff_delays_seconds"], [0.01])


class TestRetry(unittest.TestCase):
    def test_retry_success(self):
        tasks = [make_task("F", fail_times=1)]
        result = ParallelSupervisor(max_retries=2).run(tasks)
        rec = result["tasks"][0]
        self.assertEqual(rec["status"], "succeeded")
        self.assertEqual(rec["attempts"], 2)
        self.assertEqual(rec["retries_used"], 1)
        self.assertEqual(rec["backoff_delays_seconds"], [0.01])

    def test_retry_exhausted_fails(self):
        tasks = [make_task("F", fail_times=5)]
        result = ParallelSupervisor(
            max_retries=2, backoff_base_seconds=0.01).run(tasks)
        rec = result["tasks"][0]
        self.assertEqual(rec["status"], "failed")
        self.assertEqual(rec["attempts"], 3)
        self.assertEqual(rec["retries_used"], 2)
        self.assertEqual(rec["backoff_delays_seconds"], [0.01, 0.02])
        self.assertIn("transient failure", rec["error"])

    def test_budget_failure_not_retried(self):
        tasks = [make_task("B", work_steps=3, step_budget=2)]
        result = ParallelSupervisor(max_retries=2).run(tasks)
        rec = result["tasks"][0]
        self.assertEqual(rec["status"], "failed")
        self.assertEqual(rec["attempts"], 1)
        self.assertEqual(rec["steps_used"], 2)


class TestBlockedAndCost(unittest.TestCase):
    def test_blocked_dependents_and_transitive(self):
        tasks = [make_task("A", work_steps=3, step_budget=2),
                 make_task("B", deps=["A"]),
                 make_task("C", deps=["B"]),
                 make_task("D")]
        result = ParallelSupervisor(max_retries=1).run(tasks)
        by_id = {r["task_id"]: r for r in result["tasks"]}
        self.assertEqual(by_id["B"]["status"], "blocked")
        self.assertEqual(by_id["C"]["status"], "blocked")
        self.assertEqual(by_id["B"]["attempts"], 0)
        self.assertEqual(by_id["D"]["status"], "succeeded")
        self.assertEqual(result["summary"]["blocked"], 2)

    def test_cost_accounting_per_attempt(self):
        tasks = [make_task("A", cost_units=3, fail_times=1),
                 make_task("B", cost_units=2),
                 make_task("C", deps=["A"], cost_units=5)]
        result = ParallelSupervisor(max_retries=1).run(tasks)
        by_id = {r["task_id"]: r for r in result["tasks"]}
        # A costs 3 per attempt times 2 attempts = 6; B 2; C 5. Total 13.
        self.assertEqual(by_id["A"]["cost_units_total"], 6)
        self.assertEqual(result["summary"]["total_cost_units"], 13)
        self.assertEqual(result["summary"]["total_attempts"], 4)


class TestScenario(unittest.TestCase):
    def setUp(self):
        self.result = ParallelSupervisor(
            max_workers=4, max_retries=2,
            backoff_base_seconds=0.01).run(build_parallel_scenario())
        self.by_id = {r["task_id"]: r for r in self.result["tasks"]}

    def test_waves_exact(self):
        self.assertEqual(self.result["waves"],
                         [["B01", "B02", "B03"], ["B04", "B05", "B06", "B07"],
                          ["B08", "B09", "B10"], ["B11", "B12"]])

    def test_summary_exact(self):
        s = self.result["summary"]
        self.assertEqual(
            (s["total_tasks"], s["succeeded"], s["failed"], s["blocked"],
             s["waves"], s["total_attempts"], s["retries_used"],
             s["timeout_attempts"], s["total_cost_units"],
             s["total_steps_used"], s["trace_length"], s["status"]),
            (12, 8, 2, 2, 4, 13, 3, 3, 34, 13, 15, "partial"))

    def test_timeout_task_exact(self):
        r = self.by_id["B07"]
        self.assertEqual((r["status"], r["attempts"], r["retries_used"],
                          r["timeout_attempts"], r["cost_units_total"],
                          r["steps_used"]), ("failed", 3, 2, 3, 6, 0))
        self.assertEqual(r["backoff_delays_seconds"], [0.01, 0.02])

    def test_flaky_task_exact(self):
        r = self.by_id["B05"]
        self.assertEqual((r["status"], r["attempts"], r["cost_units_total"]),
                         ("succeeded", 2, 8))
        self.assertEqual(r["backoff_delays_seconds"], [0.01])

    def test_blocked_tasks_exact(self):
        self.assertIn("B07", self.by_id["B09"]["error"])
        self.assertIn("B08", self.by_id["B11"]["error"])
        self.assertEqual(self.by_id["B12"]["status"], "succeeded")

    def test_trace_shape(self):
        trace = self.result["trace"]
        self.assertEqual([e["seq"] for e in trace], list(range(1, 16)))
        events = [(e["task_id"], e["event"]) for e in trace]
        self.assertEqual(events.count(("B07", "attempt_timeout")), 3)
        self.assertIn(("B09", "blocked"), events)
        self.assertIn(("B05", "attempt_failed"), events)
        self.assertIn(("B05", "attempt_succeeded"), events)

    def test_backoff_total(self):
        # B05 delays 0.01 plus B07 delays 0.01 and 0.02 = 0.04.
        self.assertEqual(self.result["summary"]["total_backoff_delay_seconds"], 0.04)

    def test_determinism(self):
        again = ParallelSupervisor(
            max_workers=4, max_retries=2,
            backoff_base_seconds=0.01).run(build_parallel_scenario())
        self.assertEqual(again, self.result)


class TestValidation(unittest.TestCase):
    def test_bad_timeout_rejected(self):
        with self.assertRaises(OrchestratorError):
            validate_build_graph([make_task("A", timeout_seconds=0)])

    def test_bad_sleep_rejected(self):
        with self.assertRaises(OrchestratorError):
            validate_build_graph([make_task("A", sleep_seconds=-1)])


if __name__ == "__main__":
    unittest.main()
