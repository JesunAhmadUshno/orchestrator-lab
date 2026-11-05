"""Run the Learn scenario and write deterministic results.

Run: python level-1-learn/run_learn.py
Writes level-1-learn/results_learn.json. No timestamps, no randomness,
no wall clock values, so two runs produce an identical file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from orchestrator import Supervisor, build_report_scenario  # noqa: E402


def main():
    tasks = build_report_scenario()
    result = Supervisor(max_retries=1).run(tasks)
    for r in result["tasks"]:
        print(f"{r['task_id']} {r['name']}: wave={r['wave']} worker={r['worker']} "
              f"attempts={r['attempts']} cost={r['cost_units_total']} "
              f"steps={r['steps_used']} status={r['status']}")
    s = result["summary"]
    print(f"Summary: {s['succeeded']} succeeded, {s['failed']} failed, "
          f"{s['blocked']} blocked of {s['total_tasks']} tasks in {s['waves']} waves; "
          f"cost={s['total_cost_units']} attempts={s['total_attempts']} "
          f"retries={s['retries_used']} steps={s['total_steps_used']} "
          f"trace={s['trace_length']} status={s['status']}")
    out = {"scenario": "report-building job, 10 tasks, deterministic toy workers",
           "waves": result["waves"], "tasks": result["tasks"],
           "trace": result["trace"], "summary": s}
    path = os.path.join(HERE, "results_learn.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
