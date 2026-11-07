"""Sensitivity sweeps for the Deep routing comparison.

Run: python level-3-deep/sweep_deep.py
Writes level-3-deep/results_sweep.json. Deterministic: no random
values, no timestamps, so two runs produce an identical file.

Every number comes from the real RoutedSupervisor on the Deep
scenario with the simulated approver (rejects D09 only). The
quality model is still the fixed teaching table, so these sweeps
describe that table and that scenario, not real models.

1. Estimation error. Start from oracle estimates (estimated
   difficulty equals true difficulty, so routed never escalates),
   then underestimate k of the 9 executed tasks by setting their
   estimate to 1, for every subset of size k (512 subsets in all).
   Underestimating an easy task changes nothing; underestimating a
   hard task sends it small first, it fails the quality check and
   escalates, costing small + large instead of large. The shipped
   scenario is the single subset {D07} at k = 1.
2. Quality threshold, 0.60 to 0.95, on the shipped scenario, all
   three strategies. At 0.90 and above the large tier fails at
   difficulty 5 (0.88), which exercises the no-second-escalation
   path.
3. Large tier cost, 3 to 8 (small stays 2), on the shipped
   scenario, all three strategies.
4. Routing cutoff, 1 to 5: routed sends a task small when its
   estimated difficulty is at most the cutoff. The shipped rule
   is 2.
"""
import json
import os
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from orchestrator_deep import (  # noqa: E402
    STRATEGIES, RoutedSupervisor, SimulatedApprover, build_deep_scenario)

REJECT_IDS = {"D09"}
THRESHOLDS = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
LARGE_COSTS = [3, 4, 5, 6, 7, 8]
CUTOFFS = [1, 2, 3, 4, 5]


def run(tasks, strategy="routed", threshold=0.80, cutoff=2):
    sup = RoutedSupervisor(strategy=strategy, quality_threshold=threshold,
                           approver=SimulatedApprover(REJECT_IDS),
                           routing_cutoff=cutoff)
    return sup.run([dict(t) for t in tasks])["summary"]


def with_costs(tasks, small_cost, large_cost):
    return [dict(t, small_cost=small_cost, large_cost=large_cost)
            for t in tasks]


def strategy_row(summary):
    return {"cost": summary["total_cost_units"],
            "quality_pass": summary["quality_pass"],
            "quality_fail": summary["quality_fail"],
            "escalations": summary["escalations"]}


def estimation_sweep(small_cost=2, large_cost=5):
    tasks = with_costs(build_deep_scenario(), small_cost, large_cost)
    oracle = [dict(t, estimated_difficulty=t["difficulty"]) for t in tasks]
    full = RoutedSupervisor(strategy="routed",
                            approver=SimulatedApprover(REJECT_IDS)).run(
        [dict(t) for t in oracle])
    executed = [r["task_id"] for r in full["tasks"]
                if r["status"] == "succeeded"]
    all_large = run(oracle, "all_large")["total_cost_units"]
    rows = []
    for k in range(len(executed) + 1):
        costs, passes, escs = [], [], []
        for subset in combinations(executed, k):
            low = set(subset)
            variant = [dict(t, estimated_difficulty=1) if t["id"] in low
                       else t for t in oracle]
            s = run(variant)
            costs.append(s["total_cost_units"])
            passes.append(s["quality_pass"])
            escs.append(s["escalations"])
        rows.append({"k": k, "subsets": len(costs),
                     "cost_min": min(costs), "cost_max": max(costs),
                     "cost_sum": sum(costs),
                     "cost_mean": round(sum(costs) / len(costs), 4),
                     "quality_pass_min": min(passes),
                     "quality_pass_max": max(passes),
                     "escalations_sum": sum(escs),
                     "subsets_at_or_above_all_large": sum(
                         1 for c in costs if c >= all_large)})

    def first_k(key):
        hits = [r["k"] for r in rows if r[key] >= all_large]
        return hits[0] if hits else None

    return {"small_cost": small_cost, "large_cost": large_cost,
            "executed_tasks": executed, "all_large_cost": all_large,
            "rows": rows,
            "break_even_k_worst_case": first_k("cost_max"),
            "break_even_k_mean": first_k("cost_mean")}


def main():
    base = build_deep_scenario()
    out = {
        "note": ("Sensitivity sweeps on the Deep toy scenario: fixed quality "
                 "table, deterministic toy workers, simulated approver that "
                 "rejects D09 only. Not a real model result."),
        "estimation_error": estimation_sweep(2, 5),
        "estimation_error_large_cost_4": estimation_sweep(2, 4),
        "threshold": [
            {"threshold": th, **{s: strategy_row(run(base, s, th))
                                 for s in STRATEGIES}}
            for th in THRESHOLDS],
        "large_cost": [
            {"large_cost": lc, **{s: strategy_row(run(with_costs(base, 2, lc), s))
                                  for s in STRATEGIES}}
            for lc in LARGE_COSTS],
        "routing_cutoff": [
            {"cutoff": c, "routed": strategy_row(run(base, "routed", cutoff=c))}
            for c in CUTOFFS],
    }
    est = out["estimation_error"]
    print(f"estimation error (small 2, large 5): all_large {est['all_large_cost']}, "
          f"routed cost by k (min/mean/max): "
          + "; ".join(f"k={r['k']} {r['cost_min']}/{r['cost_mean']}/{r['cost_max']}"
                      for r in est["rows"]))
    print(f"break-even k worst case: {est['break_even_k_worst_case']}, "
          f"mean: {est['break_even_k_mean']}")
    est4 = out["estimation_error_large_cost_4"]
    print(f"with large cost 4: break-even k worst case "
          f"{est4['break_even_k_worst_case']}, mean {est4['break_even_k_mean']}")
    path = os.path.join(HERE, "results_sweep.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
