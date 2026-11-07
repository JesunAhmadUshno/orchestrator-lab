"""Unit tests for the Deep sensitivity sweep and the large-tier fail path."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-3-deep"))
from orchestrator_deep import (  # noqa: E402
    RoutedSupervisor, SimulatedApprover, build_deep_scenario, choose_tier)
import sweep_deep  # noqa: E402


def task(tid, difficulty, estimated):
    return {"id": tid, "name": tid.lower(), "worker": "Worker",
            "dependencies": [], "difficulty": difficulty,
            "estimated_difficulty": estimated, "small_cost": 2,
            "large_cost": 5, "requires_approval": False,
            "payload": "one two three"}


class TestLargeTierFails(unittest.TestCase):
    def test_large_routed_task_fails_threshold_without_escalation(self):
        res = RoutedSupervisor(quality_threshold=0.90).run([task("A", 5, 5)])
        rec = res["tasks"][0]
        self.assertEqual(rec["status"], "succeeded")
        self.assertEqual(rec["final_tier"], "large")
        self.assertFalse(rec["quality_pass"])
        self.assertFalse(rec["escalated"])
        self.assertEqual(rec["attempts"], 1)
        self.assertEqual(rec["cost_units_total"], 5)

    def test_escalated_task_fails_again_with_no_second_escalation(self):
        res = RoutedSupervisor(quality_threshold=0.90).run([task("A", 5, 1)])
        rec = res["tasks"][0]
        self.assertTrue(rec["escalated"])
        self.assertEqual(rec["attempts"], 2)
        self.assertEqual(rec["cost_units_total"], 7)
        self.assertEqual(rec["quality"], 0.88)
        self.assertFalse(rec["quality_pass"])
        self.assertEqual(res["summary"]["quality_fail"], 1)


class TestRoutingCutoff(unittest.TestCase):
    def test_default_cutoff_is_two(self):
        self.assertEqual(choose_tier(task("A", 3, 2), "routed"), "small")
        self.assertEqual(choose_tier(task("A", 3, 3), "routed"), "large")

    def test_cutoff_moves_the_split(self):
        self.assertEqual(choose_tier(task("A", 3, 3), "routed", cutoff=3), "small")
        self.assertEqual(choose_tier(task("A", 1, 2), "routed", cutoff=1), "large")


class TestEstimationSweep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sweep = sweep_deep.estimation_sweep(2, 5)

    def test_oracle_estimates_cost_33(self):
        row = self.sweep["rows"][0]
        self.assertEqual((row["k"], row["subsets"], row["cost_min"]), (0, 1, 33))

    def test_shipped_scenario_is_one_k1_subset(self):
        # Underestimating D07 alone reproduces the recorded routed cost 35.
        tasks = [dict(t, estimated_difficulty=t["difficulty"])
                 for t in build_deep_scenario()]
        tasks = [dict(t, estimated_difficulty=1) if t["id"] == "D07" else t
                 for t in tasks]
        res = RoutedSupervisor(approver=SimulatedApprover({"D09"})).run(tasks)
        self.assertEqual(res["summary"]["total_cost_units"], 35)
        self.assertEqual(self.sweep["rows"][1]["cost_max"], 35)

    def test_no_break_even_at_cost_2_and_5(self):
        self.assertEqual(self.sweep["all_large_cost"], 45)
        self.assertEqual(self.sweep["rows"][-1]["cost_max"], 43)
        self.assertIsNone(self.sweep["break_even_k_worst_case"])
        for row in self.sweep["rows"]:
            self.assertEqual(row["quality_pass_min"], 9)

    def test_break_even_exists_at_large_cost_4(self):
        sweep = sweep_deep.estimation_sweep(2, 4)
        self.assertEqual(sweep["break_even_k_worst_case"], 4)
        self.assertEqual(sweep["break_even_k_mean"], 8)

    def test_subset_counts_are_binomial(self):
        self.assertEqual(sum(r["subsets"] for r in self.sweep["rows"]), 512)

    def test_committed_results_match_a_fresh_run(self):
        with open(os.path.join(ROOT, "level-3-deep", "results_sweep.json"),
                  encoding="utf-8") as f:
            committed = json.load(f)
        self.assertEqual(committed["estimation_error"], self.sweep)


if __name__ == "__main__":
    unittest.main()
