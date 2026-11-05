"""Unit tests for the Level 3 Deep routed orchestrator."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-3-deep"))
from orchestrator_deep import (  # noqa: E402
    DeepError, RoutedSupervisor, SimulatedApprover, build_deep_scenario,
    choose_tier, quality_for, run_comparison, validate_deep_graph,
)


def make_task(tid, deps=None, **over):
    task = {"id": tid, "name": tid.lower(), "worker": "Worker",
            "dependencies": deps or [], "difficulty": 1,
            "estimated_difficulty": 1, "small_cost": 2, "large_cost": 5,
            "requires_approval": False, "payload": "one two three"}
    task.update(over)
    return task


def run(strategy, tasks, reject=None):
    return RoutedSupervisor(
        strategy=strategy,
        approver=SimulatedApprover(reject_ids=reject or set())).run(tasks)


class TestQualityTable(unittest.TestCase):
    def test_small_passes_only_easy(self):
        self.assertGreaterEqual(quality_for("small", 1), 0.80)
        self.assertGreaterEqual(quality_for("small", 2), 0.80)
        for d in (3, 4, 5):
            self.assertLess(quality_for("small", d), 0.80)

    def test_large_passes_all(self):
        for d in (1, 2, 3, 4, 5):
            self.assertGreaterEqual(quality_for("large", d), 0.80)

    def test_unknown_tier_rejected(self):
        with self.assertRaises(DeepError):
            quality_for("medium", 1)


class TestRoutingChoice(unittest.TestCase):
    def test_routed_easy_goes_small_hard_goes_large(self):
        self.assertEqual(choose_tier(make_task("A", difficulty=1,
                                               estimated_difficulty=2),
                                     "routed"), "small")
        self.assertEqual(choose_tier(make_task("B", difficulty=3,
                                               estimated_difficulty=3),
                                     "routed"), "large")
        self.assertEqual(choose_tier(make_task("C", difficulty=5,
                                               estimated_difficulty=5),
                                     "routed"), "large")

    def test_router_uses_estimate_not_true_difficulty(self):
        task = make_task("U", difficulty=5, estimated_difficulty=1)
        self.assertEqual(choose_tier(task, "routed"), "small")

    def test_forced_strategies(self):
        task = make_task("A", difficulty=1, estimated_difficulty=1)
        self.assertEqual(choose_tier(task, "all_small"), "small")
        self.assertEqual(choose_tier(task, "all_large"), "large")

    def test_routed_run_records_tiers_and_costs(self):
        tasks = [make_task("E", difficulty=1, estimated_difficulty=1),
                 make_task("H", difficulty=4, estimated_difficulty=4)]
        result = run("routed", tasks)
        by_id = {r["task_id"]: r for r in result["tasks"]}
        self.assertEqual((by_id["E"]["final_tier"],
                          by_id["E"]["cost_units_total"]), ("small", 2))
        self.assertEqual((by_id["H"]["final_tier"],
                          by_id["H"]["cost_units_total"]), ("large", 5))


class TestEscalation(unittest.TestCase):
    def test_underestimated_task_escalates_once(self):
        tasks = [make_task("U", difficulty=3, estimated_difficulty=1)]
        result = run("routed", tasks)
        rec = result["tasks"][0]
        self.assertTrue(rec["escalated"])
        self.assertEqual(rec["initial_tier"], "small")
        self.assertEqual(rec["final_tier"], "large")
        self.assertEqual(rec["attempts"], 2)
        self.assertEqual(rec["cost_units_total"], 7)
        self.assertEqual(rec["quality"], 0.95)
        self.assertTrue(rec["quality_pass"])
        self.assertEqual(result["summary"]["escalations"], 1)
        events = [e["event"] for e in result["trace"]]
        self.assertIn("escalated", events)
        self.assertIn("quality_check_failed", events)

    def test_easy_small_task_does_not_escalate(self):
        result = run("routed", [make_task("E", difficulty=2,
                                          estimated_difficulty=2)])
        rec = result["tasks"][0]
        self.assertFalse(rec["escalated"])
        self.assertEqual(rec["attempts"], 1)
        self.assertEqual(result["summary"]["escalations"], 0)

    def test_no_escalation_outside_routed(self):
        tasks = [make_task("U", difficulty=3, estimated_difficulty=1)]
        rec = run("all_small", tasks)["tasks"][0]
        self.assertFalse(rec["escalated"])
        self.assertFalse(rec["quality_pass"])
        self.assertEqual(rec["cost_units_total"], 2)


class TestApprovalGates(unittest.TestCase):
    def test_approved_task_runs(self):
        tasks = [make_task("G", requires_approval=True)]
        result = run("routed", tasks, reject=set())
        rec = result["tasks"][0]
        self.assertEqual(rec["approval"], "approved")
        self.assertEqual(rec["status"], "succeeded")
        self.assertEqual(result["summary"]["approvals_granted"], 1)
        self.assertIn("approval_granted",
                      [e["event"] for e in result["trace"]])

    def test_rejected_task_blocked_dependents(self):
        tasks = [make_task("G", requires_approval=True),
                 make_task("D", deps=["G"]),
                 make_task("T", deps=["D"]),
                 make_task("F")]
        result = run("routed", tasks, reject={"G"})
        by_id = {r["task_id"]: r for r in result["tasks"]}
        self.assertEqual(by_id["G"]["status"], "rejected")
        self.assertEqual(by_id["G"]["approval"], "rejected")
        self.assertEqual(by_id["G"]["cost_units_total"], 0)
        self.assertEqual(by_id["G"]["attempts"], 0)
        self.assertEqual(by_id["D"]["status"], "blocked")
        self.assertEqual(by_id["T"]["status"], "blocked")
        self.assertEqual(by_id["F"]["status"], "succeeded")
        s = result["summary"]
        self.assertEqual((s["approvals_requested"], s["approvals_rejected"],
                          s["rejected"], s["blocked"]), (1, 1, 1, 2))

    def test_unflagged_task_needs_no_approval(self):
        result = run("routed", [make_task("P")], reject={"P"})
        rec = result["tasks"][0]
        self.assertEqual(rec["approval"], "not_required")
        self.assertEqual(rec["status"], "succeeded")


class TestComparisonArithmetic(unittest.TestCase):
    def setUp(self):
        self.results = run_comparison()
        self.comp = {k: v["summary"] for k, v in self.results.items()}

    def test_scenario_waves(self):
        self.assertEqual(self.results["routed"]["waves"],
                         [["D01", "D02", "D09"], ["D03", "D06", "D07", "D10"],
                          ["D04", "D05", "D08"], ["D11"]])

    def test_all_small_exact(self):
        s = self.comp["all_small"]
        self.assertEqual((s["total_cost_units"], s["quality_pass"],
                          s["quality_fail"], s["escalations"],
                          s["succeeded"], s["rejected"], s["blocked"]),
                         (18, 4, 5, 0, 9, 1, 1))

    def test_all_large_exact(self):
        s = self.comp["all_large"]
        self.assertEqual((s["total_cost_units"], s["quality_pass"],
                          s["quality_fail"], s["escalations"],
                          s["succeeded"], s["rejected"], s["blocked"]),
                         (45, 9, 0, 0, 9, 1, 1))

    def test_routed_exact(self):
        s = self.comp["routed"]
        self.assertEqual((s["total_cost_units"], s["quality_pass"],
                          s["quality_fail"], s["escalations"],
                          s["succeeded"], s["rejected"], s["blocked"]),
                         (35, 9, 0, 1, 9, 1, 1))

    def test_routed_saving_arithmetic(self):
        saving = (self.comp["all_large"]["total_cost_units"]
                  - self.comp["routed"]["total_cost_units"])
        self.assertEqual(saving, 10)
        self.assertEqual(self.comp["routed"]["quality_pass"],
                         self.comp["all_large"]["quality_pass"])
        self.assertLess(self.comp["all_small"]["quality_pass"],
                        self.comp["routed"]["quality_pass"])

    def test_approvals_same_across_strategies(self):
        for s in self.comp.values():
            self.assertEqual((s["approvals_requested"],
                              s["approvals_granted"],
                              s["approvals_rejected"]), (2, 1, 1))

    def test_cost_recomputes_from_task_records(self):
        for res in self.results.values():
            total = sum(r["cost_units_total"] for r in res["tasks"])
            self.assertEqual(total, res["summary"]["total_cost_units"])
            passes = sum(1 for r in res["tasks"]
                         if r["status"] == "succeeded" and r["quality_pass"])
            self.assertEqual(passes, res["summary"]["quality_pass"])

    def test_escalated_task_record_exact(self):
        by_id = {r["task_id"]: r for r in self.results["routed"]["tasks"]}
        d07 = by_id["D07"]
        self.assertEqual((d07["initial_tier"], d07["final_tier"],
                          d07["cost_units_total"], d07["quality"]),
                         ("small", "large", 7, 0.95))
        self.assertTrue(d07["escalated"])

    def test_determinism(self):
        again = run_comparison()
        self.assertEqual(again, self.results)


class TestValidation(unittest.TestCase):
    def test_bad_difficulty_rejected(self):
        with self.assertRaises(DeepError):
            validate_deep_graph([make_task("A", difficulty=6)])

    def test_large_must_cost_more_than_small(self):
        with self.assertRaises(DeepError):
            validate_deep_graph([make_task("A", small_cost=5, large_cost=5)])

    def test_unknown_strategy_rejected(self):
        with self.assertRaises(DeepError):
            RoutedSupervisor(strategy="cheapest")

    def test_cycle_rejected(self):
        tasks = [make_task("A", deps=["B"]), make_task("B", deps=["A"])]
        with self.assertRaises(DeepError):
            run("routed", tasks)


if __name__ == "__main__":
    unittest.main()
