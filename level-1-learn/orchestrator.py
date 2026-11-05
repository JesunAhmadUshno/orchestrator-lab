"""Supervisor and task graph orchestration, Level 1 Learn.

One supervisor splits a small report-building job into a task graph,
computes parallel-ready waves by topological level, assigns named
workers with cost units, and executes wave by wave.

Workers are deterministic toy functions, not LLMs and not real agents.
They take a payload string and return its word and character counts.
No API is called, nothing is learned, and no wall clock timing is
used: the timeout is enforced as a per-task step budget so every run
is deterministic. A real worker pool is Build level scope.

Only the Python standard library is used.
"""


class OrchestratorError(Exception):
    """Named error for invalid graphs and invalid task definitions."""


class FlakyError(Exception):
    """Deterministic first-attempt failure for a task marked flaky."""


class BudgetError(Exception):
    """Raised when a task needs more steps than its step budget."""


def toy_worker(task, attempt):
    """Deterministic toy work. Fails in named ways by task design.

    Order of checks is fixed: a flaky task fails its first attempt,
    then a task whose work_steps exceed its step_budget fails on
    every attempt. All other attempts succeed.
    """
    if task.get("flaky") and attempt == 1:
        raise FlakyError("flaky failure on attempt 1 (deterministic, by design)")
    if task["work_steps"] > task["step_budget"]:
        raise BudgetError(
            "step budget exceeded: needs %d steps, budget is %d"
            % (task["work_steps"], task["step_budget"]))
    payload = task["payload"]
    return {"words": len(payload.split()), "chars": len(payload)}


def validate_graph(tasks):
    """Check ids, workers, costs, steps, and dependency references."""
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
    for task in tasks:
        for dep in task["dependencies"]:
            if dep not in ids:
                raise OrchestratorError(
                    "task '" + task["id"] + "': unknown dependency '" + dep + "'")
    return ids


def compute_waves(tasks):
    """Return waves by topological level: a list of sorted id lists.

    A task sits at level 0 when it has no dependencies, else at one
    plus the maximum level of its dependencies. Raises on a cycle.
    """
    validate_graph(tasks)
    by_id = {t["id"]: t for t in tasks}
    levels = {}
    visiting = set()

    def level_of(tid):
        if tid in levels:
            return levels[tid]
        if tid in visiting:
            raise OrchestratorError("dependency cycle detected at task '" + tid + "'")
        visiting.add(tid)
        deps = by_id[tid]["dependencies"]
        lvl = 0 if not deps else 1 + max(level_of(d) for d in deps)
        visiting.discard(tid)
        levels[tid] = lvl
        return lvl

    for task in tasks:
        level_of(task["id"])
    if not levels:
        return []
    waves = []
    for lvl in range(max(levels.values()) + 1):
        waves.append(sorted(tid for tid, l in levels.items() if l == lvl))
    return waves


def topological_order(tasks):
    """Flattened wave order: every dependency comes before its task."""
    order = []
    for wave in compute_waves(tasks):
        order.extend(wave)
    return order


class Supervisor:
    """Executes a task graph wave by wave with one retry for flaky tasks.

    Retry rule: only a FlakyError is retried, at most max_retries
    times. A BudgetError is never retried. A task whose dependency
    failed or was blocked is marked blocked and never attempted.
    Cost is charged per attempt, so a retried task costs twice its
    cost_units. A blocked task costs 0 and uses 0 steps.
    """

    def __init__(self, max_retries=1):
        if not isinstance(max_retries, int) or max_retries < 0:
            raise OrchestratorError("max_retries must be a non-negative integer")
        self.max_retries = max_retries

    def run(self, tasks):
        waves = compute_waves(tasks)
        by_id = {t["id"]: t for t in tasks}
        wave_of = {}
        for idx, wave in enumerate(waves):
            for tid in wave:
                wave_of[tid] = idx
        records = {}
        trace = []
        for wave in waves:
            for tid in wave:
                task = by_id[tid]
                record = self._run_task(task, wave_of[tid], records, trace)
                records[tid] = record
        ordered = [records[tid] for tid in topological_order(tasks)]
        summary = {
            "total_tasks": len(ordered),
            "succeeded": sum(1 for r in ordered if r["status"] == "succeeded"),
            "failed": sum(1 for r in ordered if r["status"] == "failed"),
            "blocked": sum(1 for r in ordered if r["status"] == "blocked"),
            "waves": len(waves),
            "total_attempts": sum(r["attempts"] for r in ordered),
            "retries_used": sum(r["retries_used"] for r in ordered),
            "total_cost_units": sum(r["cost_units_total"] for r in ordered),
            "total_steps_used": sum(r["steps_used"] for r in ordered),
            "trace_length": len(trace),
        }
        summary["status"] = (
            "complete" if summary["failed"] == 0 and summary["blocked"] == 0
            else "partial")
        return {"waves": waves, "tasks": ordered, "trace": trace, "summary": summary}

    def _run_task(self, task, wave_index, records, trace):
        tid = task["id"]
        record = {
            "task_id": tid,
            "name": task["name"],
            "worker": task["worker"],
            "dependencies": list(task["dependencies"]),
            "wave": wave_index,
            "status": None,
            "attempts": 0,
            "retries_used": 0,
            "cost_units_per_attempt": task["cost_units"],
            "cost_units_total": 0,
            "steps_used": 0,
            "step_budget": task["step_budget"],
            "output": None,
            "error": None,
        }
        bad_deps = [d for d in task["dependencies"]
                    if records[d]["status"] != "succeeded"]
        if bad_deps:
            record["status"] = "blocked"
            record["error"] = "blocked by dependency: " + ", ".join(sorted(bad_deps))
            trace.append({"seq": len(trace) + 1, "wave": wave_index, "task_id": tid,
                          "event": "blocked", "attempt": 0,
                          "detail": record["error"]})
            return record
        max_attempts = 1 + self.max_retries
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            record["attempts"] = attempt
            record["cost_units_total"] = attempt * task["cost_units"]
            try:
                output = toy_worker(task, attempt)
            except FlakyError as exc:
                trace.append({"seq": len(trace) + 1, "wave": wave_index, "task_id": tid,
                              "event": "attempt_failed", "attempt": attempt,
                              "detail": str(exc)})
                if attempt < max_attempts:
                    record["retries_used"] = attempt
                    continue
                record["status"] = "failed"
                record["error"] = str(exc)
                record["steps_used"] = 0
                return record
            except BudgetError as exc:
                trace.append({"seq": len(trace) + 1, "wave": wave_index, "task_id": tid,
                              "event": "attempt_failed", "attempt": attempt,
                              "detail": str(exc)})
                record["status"] = "failed"
                record["error"] = str(exc)
                record["steps_used"] = task["step_budget"]
                return record
            trace.append({"seq": len(trace) + 1, "wave": wave_index, "task_id": tid,
                          "event": "attempt_succeeded", "attempt": attempt,
                          "detail": "words=%d chars=%d" % (output["words"], output["chars"])})
            record["status"] = "succeeded"
            record["output"] = output
            record["steps_used"] = task["work_steps"]
            return record
        return record


def build_report_scenario():
    """The Learn scenario: one small report-building job, 10 tasks.

    Hand-computed expectations (see the level README):
    waves are [T01, T02, T03], [T04, T05, T06], [T07, T08], [T09, T10].
    T05 is flaky (fails attempt 1, succeeds on the retry). T08 needs
    3 steps against a budget of 2, so it fails and T09 is blocked.
    T10 does not depend on that branch, so the report still assembles.
    """
    return [
        {"id": "T01", "name": "outline", "worker": "Planner", "dependencies": [],
         "cost_units": 2, "work_steps": 1, "step_budget": 3, "flaky": False,
         "payload": "scope method results"},
        {"id": "T02", "name": "gather_numbers", "worker": "Researcher", "dependencies": [],
         "cost_units": 3, "work_steps": 2, "step_budget": 3, "flaky": False,
         "payload": "sales rose in the north region"},
        {"id": "T03", "name": "gather_quotes", "worker": "Researcher", "dependencies": [],
         "cost_units": 2, "work_steps": 1, "step_budget": 3, "flaky": False,
         "payload": "data beats opinion"},
        {"id": "T04", "name": "draft_intro", "worker": "Writer", "dependencies": ["T01"],
         "cost_units": 3, "work_steps": 2, "step_budget": 3, "flaky": False,
         "payload": "this report explains the quarter"},
        {"id": "T05", "name": "analyse_trend", "worker": "Analyst",
         "dependencies": ["T01", "T02"],
         "cost_units": 4, "work_steps": 2, "step_budget": 3, "flaky": True,
         "payload": "numbers show a steady climb"},
        {"id": "T06", "name": "chart_spec", "worker": "Analyst", "dependencies": ["T02"],
         "cost_units": 3, "work_steps": 1, "step_budget": 3, "flaky": False,
         "payload": "line chart of monthly totals"},
        {"id": "T07", "name": "fact_check", "worker": "Reviewer",
         "dependencies": ["T04", "T05"],
         "cost_units": 2, "work_steps": 1, "step_budget": 3, "flaky": False,
         "payload": "check every claim once"},
        {"id": "T08", "name": "verify_source", "worker": "Reviewer",
         "dependencies": ["T03", "T06"],
         "cost_units": 2, "work_steps": 3, "step_budget": 2, "flaky": False,
         "payload": "trace the source document fully"},
        {"id": "T09", "name": "appendix", "worker": "Writer", "dependencies": ["T08"],
         "cost_units": 2, "work_steps": 1, "step_budget": 3, "flaky": False,
         "payload": "appendix of source notes"},
        {"id": "T10", "name": "assemble_report", "worker": "Assembler",
         "dependencies": ["T04", "T05", "T06", "T07"],
         "cost_units": 3, "work_steps": 1, "step_budget": 3, "flaky": False,
         "payload": "final assembled report package"},
    ]
