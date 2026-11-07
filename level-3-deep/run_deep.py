"""Run the Deep strategy comparison and write deterministic results.

Run: python level-3-deep/run_deep.py
Writes level-3-deep/results_deep.json and the scenario itself as
data in level-3-deep/scenario_deep.json. No timestamps and no wall
clock values are written, so two runs produce an identical file.
The approver is a deterministic simulated approver that rejects
D09 only. It is labelled simulated everywhere it appears; it is
not a real human approver.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from orchestrator_deep import (  # noqa: E402
    SimulatedApprover, build_deep_scenario, run_comparison)


def main():
    approver = SimulatedApprover(reject_ids={"D09"})
    results = run_comparison(approver=approver)
    comparison = {}
    for name, res in results.items():
        s = res["summary"]
        comparison[name] = s
        print(f"{name}: cost={s['total_cost_units']} "
              f"quality_pass={s['quality_pass']} quality_fail={s['quality_fail']} "
              f"escalations={s['escalations']} succeeded={s['succeeded']} "
              f"rejected={s['rejected']} blocked={s['blocked']}")
    routed = comparison["routed"]
    large = comparison["all_large"]
    small = comparison["all_small"]
    saving = large["total_cost_units"] - routed["total_cost_units"]
    print(f"Routed saves {saving} cost units vs all_large "
          f"({large['total_cost_units']} to {routed['total_cost_units']}) "
          f"at the same quality pass count ({routed['quality_pass']}); "
          f"all_small costs {small['total_cost_units']} but passes "
          f"only {small['quality_pass']} of "
          f"{small['quality_pass'] + small['quality_fail']} executed tasks.")
    out = {
        "scenario": ("Deep comparison scenario, 11 tasks, deterministic toy "
                     "workers, two tiers (small cost 2, large cost 5), "
                     "quality threshold 0.80, simulated approver rejects "
                     "D09 only (simulated, not a real human)"),
        "quality_threshold": 0.80,
        "comparison": comparison,
        "strategies": {
            name: {"waves": res["waves"], "tasks": res["tasks"],
                   "trace": res["trace"], "summary": res["summary"]}
            for name, res in results.items()
        },
    }
    path = os.path.join(HERE, "results_deep.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Wrote", path)
    scenario_path = os.path.join(HERE, "scenario_deep.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump({"tasks": build_deep_scenario(),
                   "simulated_reject_ids": ["D09"]},
                  f, indent=2, sort_keys=True)
        f.write("\n")
    print("Wrote", scenario_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
