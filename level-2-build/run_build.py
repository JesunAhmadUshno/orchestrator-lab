"""Run the Build scenario and write deterministic results.

Run: python level-2-build/run_build.py
Writes level-2-build/results_build.json. No timestamps and no
elapsed wall clock values are written, so two runs produce an
identical file. Parallel timing is real but is only printed to
the console as a non-recorded observation, never stored.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "level-1-learn"))
sys.path.insert(0, HERE)
from orchestrator_build import ParallelSupervisor, build_parallel_scenario  # noqa: E402


def main():
    tasks = build_parallel_scenario()
    start = time.monotonic()
    result = ParallelSupervisor(
        max_workers=4, max_retries=2, backoff_base_seconds=0.01).run(tasks)
    elapsed = time.monotonic() - start
    for r in result["tasks"]:
        print(f"{r['task_id']} {r['name']}: wave={r['wave']} worker={r['worker']} "
              f"attempts={r['attempts']} cost={r['cost_units_total']} "
              f"steps={r['steps_used']} status={r['status']}")
    s = result["summary"]
    print(f"Summary: {s['succeeded']} succeeded, {s['failed']} failed, "
          f"{s['blocked']} blocked of {s['total_tasks']} tasks in {s['waves']} waves; "
          f"cost={s['total_cost_units']} attempts={s['total_attempts']} "
          f"retries={s['retries_used']} timeout_attempts={s['timeout_attempts']} "
          f"steps={s['total_steps_used']} trace={s['trace_length']} status={s['status']}")
    print(f"Observed wall clock for this console run only (not stored): {elapsed:.3f}s")
    out = {"scenario": "parallel report pipeline, 12 tasks, deterministic toy workers, "
                       "real thread pool, wall clock timeouts",
           "waves": result["waves"], "tasks": result["tasks"],
           "trace": result["trace"], "summary": s}
    path = os.path.join(HERE, "results_build.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
