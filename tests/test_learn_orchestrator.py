"""Unit tests for the Level 1 Learn orchestrator. Hand-computed expectations."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-1-learn"))
from orchestrator import (  # noqa: E402
    OrchestratorError, Supervisor, build_report_scenario,
    compute_waves, topological_order, toy_worker, BudgetError, FlakyError,
)


def make_task(tid, deps=None, **over):
    task = {"id": tid, "name": tid.lower(), "worker": "Worker",
            "dependencies": deps or [], "cost_units": 1, "work_steps": 1,
            "step_budget": 3, "flaky": False, "payload": "one two"}
    task.update(over)
    return task


class TestWaves(unittest.TestCase):
    def test_scenario_waves_exact(self):
        # Levels: T01,T02,T03 have no deps (0). T04,T05,T06 sit one level
        # above wave 0 tasks (1). T07 above T04,T05 and T08 above T03,T06
        # (2). T09 above T08 and T10 above T07 (3).
        self.assertEqual(
            compute_waves(build_report_scenario()),
            [["T01", "T02", "T03"], ["T04", "T05", "T06"],
             ["T07", "T08"], ["T09", "T10"]])

    def test_topological_order_exact_and_valid(self):
        tasks = build_report_scenario()
        order = topological_order(tasks)
        self.assertEqual(order, ["T01", "T02", "T03", "T04", "T05", "T06",
                                 "T07", "T08", "T09", "T10"])
        pos = {tid: i for i, tid in enumerate(order)}
        for t in tasks:
            for d in t["dependencies"]:
                self.assertLess(pos[d], pos[t["id"]])

    def test_single_task_wave(self):
        self.assertEqual(compute_waves([make_task("A")]), [["A"]])

    def test_cycle_rejected(self):
        tasks = [make_task("A", deps=["B"]), make_task("B", deps=["A"])]
        with self.assertRaises(OrchestratorError):
            compute_waves(tasks)

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(OrchestratorError):
            compute_waves([make_task("A", deps=["ZZ"])])

    def test_duplicate_id_rejected(self):
        with self.assertRaises(OrchestratorError):
            compute_waves([make_task("A"), make_task("A")])


class TestWorker(unittest.TestCase):
    def test_worker_output_counts(self):
        # "data beats opinion" has 3 words and 18 characters.
        task = make_task("X", payload="data beats opinion")
        self.assertEqual(toy_worker(task, 1), {"words": 3, "chars": 18})

    def test_flaky_fails_first_attempt_only(self):
        task = make_task("X", flaky=True)
        with self.assertRaises(FlakyError):
            toy_worker(task, 1)
        self.assertEqual(toy_worker(task, 2), {"words": 2, "chars": 7})

    def test_budget_failure(self):
        task = make_task("X", work_steps=3, step_budget=2)
        with self.assertRaises(BudgetError):
            toy_worker(task, 1)


class TestRun(unittest.TestCase):
    def setUp(self):
        self.result = Supervisor(max_retries=1).run(build_report_scenario())
        self.by_id = {r["task_id"]: r for r in self.result["tasks"]}

    def test_summary_counts(self):
        s = self.result["summary"]
        self.assertEqual(s["total_tasks"], 10)
        self.assertEqual(s["succeeded"], 8)
        self.assertEqual(s["failed"], 1)
        self.assertEqual(s["blocked"], 1)
        self.assertEqual(s["waves"], 4)
        self.assertEqual(s["status"], "partial")

    def test_retry_behaviour(self):
        r = self.by_id["T05"]
        self.assertEqual(r["status"], "succeeded")
        self.assertEqual(r["attempts"], 2)
        self.assertEqual(r["retries_used"], 1)
        self.assertEqual(self.result["summary"]["retries_used"], 1)
        self.assertEqual(self.result["summary"]["total_attempts"], 10)

    def test_budget_failure_not_retried(self):
        r = self.by_id["T08"]
        self.assertEqual(r["status"], "failed")
        self.assertEqual(r["attempts"], 1)
        self.assertEqual(r["steps_used"], 2)
        self.assertIn("step budget exceeded", r["error"])

    def test_dependency_blocked(self):
        r = self.by_id["T09"]
        self.assertEqual(r["status"], "blocked")
        self.assertEqual(r["attempts"], 0)
        self.assertEqual(r["cost_units_total"], 0)
        self.assertEqual(r["steps_used"], 0)
        self.assertIn("T08", r["error"])

    def test_cost_total_hand_computed(self):
        # Per attempt: T01 2, T02 3, T03 2, T04 3, T05 4 x 2 attempts = 8,
        # T06 3, T07 2, T08 2, T09 0 (blocked), T10 3. Sum = 28.
        self.assertEqual(self.by_id["T05"]["cost_units_total"], 8)
        self.assertEqual(self.result["summary"]["total_cost_units"], 28)

    def test_steps_total_hand_computed(self):
        # work_steps of succeeded tasks: 1+2+1+2+2+1+1+1 = 11, plus T08
        # cut at its budget of 2, plus T09 at 0. Total = 13.
        self.assertEqual(self.result["summary"]["total_steps_used"], 13)

    def test_trace_length_and_shape(self):
        # 10 attempt entries (9 executed tasks, T05 twice) plus 1 blocked
        # entry for T09 = 11. Sequence numbers run 1 to 11 in order.
        trace = self.result["trace"]
        self.assertEqual(len(trace), 11)
        self.assertEqual(self.result["summary"]["trace_length"], 11)
        self.assertEqual([e["seq"] for e in trace], list(range(1, 12)))
        events = [(e["task_id"], e["event"]) for e in trace]
        self.assertIn(("T05", "attempt_failed"), events)
        self.assertIn(("T05", "attempt_succeeded"), events)
        self.assertIn(("T09", "blocked"), events)

    def test_assemble_succeeds_despite_failed_branch(self):
        self.assertEqual(self.by_id["T10"]["status"], "succeeded")
        self.assertEqual(self.by_id["T10"]["worker"], "Assembler")

    def test_worker_assignments(self):
        self.assertEqual(self.by_id["T01"]["worker"], "Planner")
        self.assertEqual(self.by_id["T02"]["worker"], "Researcher")
        self.assertEqual(self.by_id["T05"]["worker"], "Analyst")
        self.assertEqual(self.by_id["T07"]["worker"], "Reviewer")

    def test_determinism(self):
        again = Supervisor(max_retries=1).run(build_report_scenario())
        self.assertEqual(again, self.result)


if __name__ == "__main__":
    unittest.main()
