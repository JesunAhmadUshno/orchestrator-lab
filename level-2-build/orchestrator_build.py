"""Parallel task graph orchestration, Level 2 Build.

A supervisor splits a job into a task graph, computes dependency
waves, and executes each wave with a real thread pool: tasks in the
same wave run at the same time, and a wave starts only after the
previous wave has finished, so dependencies always complete first.

Timeouts are wall clock, per attempt. Each attempt is collected
with future.result(timeout=task timeout), counted from submit
time. If the deadline passes, the attempt is recorded as timed
out. Python threads cannot be killed, so a timed out toy worker
thread is abandoned (its late result is discarded) and the pool
is shut down without waiting for it. That limit is named in the
level README.

Retries: transient failures and timeouts are retried up to
max_retries times, with exponential backoff delays of
backoff_base_seconds times 2 to the power (retry number minus 1).
The delays are really slept before the retry round and are also
recorded per task, as computed constants, so the results file
stays deterministic. A step budget failure is never retried,
because retrying the same work against the same budget cannot
succeed.

Workers are deterministic toy functions, not LLMs. A worker sleeps
for sleep_seconds to simulate work duration, then returns word and
character counts for its payload, unless it is designed to fail.

Cost is charged per attempt. Blocked tasks cost 0, use 0 steps,
and are never attempted. No wall clock elapsed value is written
to any result record, so two runs of the runner produce an
identical results file.

Only the Python standard library is used.
"""
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

try:
    from orchestrator import OrchestratorError, compute_waves, topological_order
except ImportError:  # when imported with level-1 on the path differently
    raise


class FlakyError(Exception):
    """Transient failure: a task fails its first fail_times attempts."""


class BudgetError(Exception):
    """Raised when a task needs more steps than its step budget."""


class WorkerTimeoutError(Exception):
    """Marker for an attempt that exceeded its wall clock timeout."""


def toy_worker_build(task, attempt):
    """Deterministic toy work with a simulated duration.

    Fails transiently while attempt is at most fail_times, then
    fails on the step budget if work_steps exceeds step_budget.
    All other attempts succeed after sleeping sleep_seconds.
    """
    time.sleep(task["sleep_seconds"])
    if attempt <= task.get("fail_times", 0):
        raise FlakyError(
            "transient failure on attempt %d (deterministic, by design)" % attempt)
    if task["work_steps"] > task["step_budget"]:
        raise BudgetError(
            "step budget exceeded: needs %d steps, budget is %d"
            % (task["work_steps"], task["step_budget"]))
    payload = task["payload"]
    return {"words": len(payload.split()), "chars": len(payload)}


def validate_build_graph(tasks):
    """Validate Build task fields on top of the Learn graph checks."""
    ids = set()
    for task in tasks:
        tid = task.get("id")
        if not isinstance(tid, str) or not tid:
            raise OrchestratorError("every task needs a non-empty string id")
        if tid in ids:
            raise OrchestratorError("duplicate task id: '" + tid + "'")
        ids.add(tid)
        if not isinstance(task.get("worker"), str) or not task["worker"]:
            raise OrchestratorError("task '" + tid + "': worker must be a non-empty string")
        if not isinstance(task.get("cost_units"), int) or task["cost_units"] < 1:
            raise OrchestratorError("task '" + tid + "': cost_units must be a positive integer")
        if not isinstance(task.get("work_steps"), int) or task["work_steps"] < 1:
            raise OrchestratorError("task '" + tid + "': work_steps must be a positive integer")
        if not isinstance(task.get("step_budget"), int) or task["step_budget"] < 1:
            raise OrchestratorError("task '" + tid + "': step_budget must be a positive integer")
        if not isinstance(task.get("payload"), str):
            raise OrchestratorError("task '" + tid + "': payload must be a string")
        deps = task.get("dependencies")
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise OrchestratorError("task '" + tid + "': dependencies must be a list of strings")
        sleep_s = task.get("sleep_seconds")
        if not isinstance(sleep_s, (int, float)) or isinstance(sleep_s, bool) or sleep_s < 0:
            raise OrchestratorError("task '" + tid + "': sleep_seconds must be a non-negative number")
        timeout_s = task.get("timeout_seconds")
        if not isinstance(timeout_s, (int, float)) or isinstance(timeout_s, bool) or timeout_s <= 0:
            raise OrchestratorError("task '" + tid + "': timeout_seconds must be a positive number")
        fail_times = task.get("fail_times", 0)
        if not isinstance(fail_times, int) or fail_times < 0:
            raise OrchestratorError("task '" + tid + "': fail_times must be a non-negative integer")
    for task in tasks:
        for dep in task["dependencies"]:
            if dep not in ids:
                raise OrchestratorError(
                    "task '" + task["id"] + "': unknown dependency '" + dep + "'")
    return ids


class ParallelSupervisor:
    """Executes waves in parallel with timeouts, retries, and backoff."""

    def __init__(self, max_workers=4, max_retries=2, backoff_base_seconds=0.01):
        if not isinstance(max_workers, int) or max_workers < 1:
            raise OrchestratorError("max_workers must be a positive integer")
        if not isinstance(max_retries, int) or max_retries < 0:
            raise OrchestratorError("max_retries must be a non-negative integer")
        if backoff_base_seconds < 0:
            raise OrchestratorError("backoff_base_seconds must be non-negative")
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def run(self, tasks):
        validate_build_graph(tasks)
        waves = compute_waves(tasks)
        by_id = {t["id"]: t for t in tasks}
        wave_of = {}
        for idx, wave in enumerate(waves):
            for tid in wave:
                wave_of[tid] = idx
        records = {}
        per_task_trace = {}
        for wave in waves:
            active = []
            for tid in wave:
                task = by_id[tid]
                bad = [d for d in task["dependencies"]
                       if records[d]["status"] != "succeeded"]
                if bad:
                    rec, events = self._blocked_record(task, wave_of[tid], bad)
                    records[tid] = rec
                    per_task_trace[tid] = events
                else:
                    active.append(task)
            if active:
                results = self._run_wave(active, wave_of[wave[0]])
                for tid, (rec, events) in results.items():
                    records[tid] = rec
                    per_task_trace[tid] = events
        order = topological_order(tasks)
        ordered = [records[tid] for tid in order]
        trace = []
        for tid in order:
            for ev in per_task_trace[tid]:
                entry = dict(ev)
                entry["seq"] = len(trace) + 1
                trace.append(entry)
        summary = {
            "total_tasks": len(ordered),
            "succeeded": sum(1 for r in ordered if r["status"] == "succeeded"),
            "failed": sum(1 for r in ordered if r["status"] == "failed"),
            "blocked": sum(1 for r in ordered if r["status"] == "blocked"),
            "waves": len(waves),
            "max_workers": self.max_workers,
            "total_attempts": sum(r["attempts"] for r in ordered),
            "retries_used": sum(r["retries_used"] for r in ordered),
            "timeout_attempts": sum(r["timeout_attempts"] for r in ordered),
            "total_cost_units": sum(r["cost_units_total"] for r in ordered),
            "total_steps_used": sum(r["steps_used"] for r in ordered),
            "total_backoff_delay_seconds": round(
                sum(sum(r["backoff_delays_seconds"]) for r in ordered), 10),
            "trace_length": len(trace),
        }
        summary["status"] = (
            "complete" if summary["failed"] == 0 and summary["blocked"] == 0
            else "partial")
        return {"waves": waves, "tasks": ordered, "trace": trace, "summary": summary}

    def _blocked_record(self, task, wave_index, bad_deps):
        error = "blocked by dependency: " + ", ".join(sorted(bad_deps))
        record = self._base_record(task, wave_index)
        record["status"] = "blocked"
        record["error"] = error
        events = [{"wave": wave_index, "task_id": task["id"], "event": "blocked",
                   "attempt": 0, "detail": error}]
        return record, events

    def _base_record(self, task, wave_index):
        return {
            "task_id": task["id"],
            "name": task["name"],
            "worker": task["worker"],
            "dependencies": list(task["dependencies"]),
            "wave": wave_index,
            "status": None,
            "attempts": 0,
            "retries_used": 0,
            "timeout_attempts": 0,
            "cost_units_per_attempt": task["cost_units"],
            "cost_units_total": 0,
            "steps_used": 0,
            "step_budget": task["step_budget"],
            "timeout_seconds": task["timeout_seconds"],
            "sleep_seconds": task["sleep_seconds"],
            "backoff_delays_seconds": [],
            "output": None,
            "error": None,
        }

    def _run_wave(self, tasks, wave_index):
        records = {t["id"]: self._base_record(t, wave_index) for t in tasks}
        traces = {t["id"]: [] for t in tasks}
        pending = list(tasks)
        attempt = 0
        max_attempts = 1 + self.max_retries
        while pending and attempt < max_attempts:
            attempt += 1
            if attempt > 1:
                delay = self.backoff_base_seconds * (2 ** (attempt - 2))
                for t in pending:
                    records[t["id"]]["backoff_delays_seconds"].append(delay)
                    records[t["id"]]["retries_used"] = attempt - 1
                if delay > 0:
                    time.sleep(delay)
            pool = ThreadPoolExecutor(max_workers=self.max_workers)
            futures = {}
            submitted_at = {}
            for t in pending:
                futures[t["id"]] = pool.submit(toy_worker_build, t, attempt)
                submitted_at[t["id"]] = time.monotonic()
            next_pending = []
            had_timeout = False
            for t in pending:
                tid = t["id"]
                rec = records[tid]
                rec["attempts"] = attempt
                rec["cost_units_total"] = attempt * t["cost_units"]
                deadline = submitted_at[tid] + t["timeout_seconds"]
                remaining = max(0.0, deadline - time.monotonic())
                try:
                    output = futures[tid].result(timeout=remaining)
                except FutureTimeout:
                    had_timeout = True
                    rec["timeout_attempts"] += 1
                    detail = ("timeout: attempt exceeded %.2f seconds"
                              % t["timeout_seconds"])
                    traces[tid].append({"wave": wave_index, "task_id": tid,
                                        "event": "attempt_timeout",
                                        "attempt": attempt, "detail": detail})
                    if attempt < max_attempts:
                        next_pending.append(t)
                    else:
                        rec["status"] = "failed"
                        rec["error"] = detail
                        rec["steps_used"] = 0
                    continue
                except FlakyError as exc:
                    traces[tid].append({"wave": wave_index, "task_id": tid,
                                        "event": "attempt_failed",
                                        "attempt": attempt, "detail": str(exc)})
                    if attempt < max_attempts:
                        next_pending.append(t)
                    else:
                        rec["status"] = "failed"
                        rec["error"] = str(exc)
                        rec["steps_used"] = 0
                    continue
                except BudgetError as exc:
                    traces[tid].append({"wave": wave_index, "task_id": tid,
                                        "event": "attempt_failed",
                                        "attempt": attempt, "detail": str(exc)})
                    rec["status"] = "failed"
                    rec["error"] = str(exc)
                    rec["steps_used"] = t["step_budget"]
                    continue
                traces[tid].append({
                    "wave": wave_index, "task_id": tid,
                    "event": "attempt_succeeded", "attempt": attempt,
                    "detail": "words=%d chars=%d" % (output["words"], output["chars"])})
                rec["status"] = "succeeded"
                rec["output"] = output
                rec["steps_used"] = t["work_steps"]
            pool.shutdown(wait=not had_timeout)
            pending = next_pending
        return {t["id"]: (records[t["id"]], traces[t["id"]]) for t in tasks}


def build_parallel_scenario():
    """The Build scenario: one parallel report pipeline, 12 tasks.

    Hand-computed expectations (see the level README):
    waves are [B01, B02, B03], [B04, B05, B06, B07],
    [B08, B09, B10], [B11, B12]. B05 fails transiently on attempt 1
    and succeeds on its first retry. B07 sleeps 0.50 seconds against
    a 0.10 second timeout on every attempt, so it times out on all
    3 attempts (1 plus 2 retries) and B09 is blocked by it. B08
    needs 3 steps against a budget of 2, fails without a retry, and
    B11 is blocked by it. B12 does not depend on either failed
    branch, so the report still assembles.
    """
    base = {"step_budget": 3, "fail_times": 0, "timeout_seconds": 2.0,
            "sleep_seconds": 0.05}
    tasks = [
        {"id": "B01", "name": "outline", "worker": "Planner", "dependencies": [],
         "cost_units": 2, "work_steps": 1, "payload": "scope method results",
         "sleep_seconds": 0.20},
        {"id": "B02", "name": "gather_numbers", "worker": "Researcher",
         "dependencies": [], "cost_units": 3, "work_steps": 2,
         "payload": "sales rose in the north region", "sleep_seconds": 0.20},
        {"id": "B03", "name": "gather_quotes", "worker": "Researcher",
         "dependencies": [], "cost_units": 2, "work_steps": 1,
         "payload": "data beats opinion", "sleep_seconds": 0.20},
        {"id": "B04", "name": "draft_intro", "worker": "Writer",
         "dependencies": ["B01"], "cost_units": 3, "work_steps": 2,
         "payload": "this report explains the quarter", "sleep_seconds": 0.20},
        {"id": "B05", "name": "analyse_trend", "worker": "Analyst",
         "dependencies": ["B01", "B02"], "cost_units": 4, "work_steps": 2,
         "payload": "numbers show a steady climb", "fail_times": 1},
        {"id": "B06", "name": "chart_spec", "worker": "Analyst",
         "dependencies": ["B02"], "cost_units": 3, "work_steps": 1,
         "payload": "line chart of monthly totals", "sleep_seconds": 0.20},
        {"id": "B07", "name": "slow_source", "worker": "Reviewer",
         "dependencies": ["B03"], "cost_units": 2, "work_steps": 1,
         "payload": "trace the source document fully",
         "sleep_seconds": 0.50, "timeout_seconds": 0.10},
        {"id": "B08", "name": "verify_source", "worker": "Reviewer",
         "dependencies": ["B03", "B06"], "cost_units": 2, "work_steps": 3,
         "step_budget": 2, "payload": "trace the source document fully"},
        {"id": "B09", "name": "appendix", "worker": "Writer",
         "dependencies": ["B07"], "cost_units": 2, "work_steps": 1,
         "payload": "appendix of source notes"},
        {"id": "B10", "name": "fact_check", "worker": "Reviewer",
         "dependencies": ["B04", "B05"], "cost_units": 2, "work_steps": 1,
         "payload": "check every claim once"},
        {"id": "B11", "name": "source_appendix", "worker": "Writer",
         "dependencies": ["B08"], "cost_units": 2, "work_steps": 1,
         "payload": "appendix of verified sources"},
        {"id": "B12", "name": "assemble_report", "worker": "Assembler",
         "dependencies": ["B04", "B05", "B06", "B10"], "cost_units": 3,
         "work_steps": 1, "payload": "final assembled report package"},
    ]
    for t in tasks:
        merged = dict(base)
        merged.update(t)
        t.clear()
        t.update(merged)
    return tasks
