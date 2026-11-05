"""Cost and quality routing with approval gates, Level 3 Deep.

A supervisor runs a task graph wave by wave. For each task it
chooses a worker tier, checks output quality, and, for tasks that
need it, asks an approver before any work starts.

Tiers:
  small: cheap (small_cost units), lower quality on hard tasks.
  large: expensive (large_cost units), higher quality on all
  tasks in this teaching model.

Router (strategy "routed"): it sees only the estimated difficulty
of a task. Estimated difficulty at most 2 routes to small, above
2 routes to large. The quality check uses the true difficulty.
If a small tier output scores below the quality threshold, the
task escalates once to the large tier: the large cost is charged
on top of the small cost, the large output replaces the small
output, and the escalation is recorded in the task record and
in the trace.

Approval gates: a task flagged requires_approval is paused
before routing. The approver is a callback that receives the
task dict and returns True (approved) or False (rejected). An
approved task runs normally. A rejected task is marked
"rejected", costs 0, is never attempted, and every task that
depends on it (directly or transitively) is marked "blocked".
In the shipped runner the approver is a deterministic simulated
approver, labelled as simulated. It is not a real human.

Strategies for the comparison benchmark:
  all_small: every executed task uses the small tier only, with
    no escalation. Quality is recorded, low quality stands.
  all_large: every executed task uses the large tier only.
  routed: the router above, with one escalation on a failed
    quality check for small tier tasks.

Quality model: a deterministic table by tier and true difficulty
(1 to 5). Small passes the 0.80 threshold only at difficulty 1
and 2. Large passes at every difficulty. The table is a teaching
model, not a measurement of any real model.

Workers are deterministic toy functions, not LLMs. A worker
returns word and character counts for its payload plus the
quality score from the table. Execution is sequential inside a
wave, in sorted task order, so results are fully deterministic
and do not depend on thread timing. No timestamp, random value,
or wall clock value is written to any record.

Only the Python standard library is used.
"""


class DeepError(Exception):
    """Named error for invalid Deep graphs and task definitions."""


SMALL_QUALITY = {1: 0.95, 2: 0.90, 3: 0.70, 4: 0.55, 5: 0.40}
LARGE_QUALITY = {1: 0.98, 2: 0.97, 3: 0.95, 4: 0.92, 5: 0.88}
DEFAULT_THRESHOLD = 0.80
STRATEGIES = ("all_small", "all_large", "routed")


def quality_for(tier, difficulty):
    """Deterministic quality score for a tier at a true difficulty."""
    if tier == "small":
        return SMALL_QUALITY[difficulty]
    if tier == "large":
        return LARGE_QUALITY[difficulty]
    raise DeepError("unknown tier: '" + str(tier) + "'")


def toy_worker_deep(task, tier):
    """Deterministic toy work for one tier. Returns counts and quality."""
    payload = task["payload"]
    return {"words": len(payload.split()), "chars": len(payload),
            "quality": quality_for(tier, task["difficulty"]), "tier": tier}


class SimulatedApprover:
    """Deterministic test approver. Simulated, not a real human.

    Approves every task except the ids in reject_ids.
    """

    def __init__(self, reject_ids=None):
        self.reject_ids = set(reject_ids or [])

    def __call__(self, task):
        return task["id"] not in self.reject_ids


def validate_deep_graph(tasks):
    """Check Deep task fields and dependency references."""
    ids = set()
    for task in tasks:
        tid = task.get("id")
        if not isinstance(tid, str) or not tid:
            raise DeepError("every task needs a non-empty string id")
        if tid in ids:
            raise DeepError("duplicate task id: '" + tid + "'")
        ids.add(tid)
        if not isinstance(task.get("name"), str) or not task["name"]:
            raise DeepError("task '" + tid + "': name must be a non-empty string")
        if not isinstance(task.get("worker"), str) or not task["worker"]:
            raise DeepError("task '" + tid + "': worker must be a non-empty string")
        for field in ("difficulty", "estimated_difficulty"):
            val = task.get(field)
            if not isinstance(val, int) or isinstance(val, bool) or val < 1 or val > 5:
                raise DeepError(
                    "task '" + tid + "': " + field + " must be an integer from 1 to 5")
        for field in ("small_cost", "large_cost"):
            val = task.get(field)
            if not isinstance(val, int) or isinstance(val, bool) or val < 1:
                raise DeepError(
                    "task '" + tid + "': " + field + " must be a positive integer")
        if task["large_cost"] <= task["small_cost"]:
            raise DeepError(
                "task '" + tid + "': large_cost must exceed small_cost")
        if not isinstance(task.get("payload"), str):
            raise DeepError("task '" + tid + "': payload must be a string")
        if not isinstance(task.get("requires_approval"), bool):
            raise DeepError(
                "task '" + tid + "': requires_approval must be a boolean")
        deps = task.get("dependencies")
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise DeepError(
                "task '" + tid + "': dependencies must be a list of strings")
    for task in tasks:
        for dep in task["dependencies"]:
            if dep not in ids:
                raise DeepError(
                    "task '" + task["id"] + "': unknown dependency '" + dep + "'")
    return ids


def compute_waves_deep(tasks):
    """Waves by topological level, as in Learn, for Deep tasks."""
    validate_deep_graph(tasks)
    by_id = {t["id"]: t for t in tasks}
    levels = {}
    visiting = set()

    def level_of(tid):
        if tid in levels:
            return levels[tid]
        if tid in visiting:
            raise DeepError("dependency cycle detected at task '" + tid + "'")
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
    return [sorted(tid for tid, lvl in levels.items() if lvl == n)
            for n in range(max(levels.values()) + 1)]


def topological_order_deep(tasks):
    order = []
    for wave in compute_waves_deep(tasks):
        order.extend(wave)
    return order


def choose_tier(task, strategy):
    """Initial tier for a task under a strategy (routed uses estimate)."""
    if strategy == "all_small":
        return "small"
    if strategy == "all_large":
        return "large"
    if strategy == "routed":
        return "small" if task["estimated_difficulty"] <= 2 else "large"
    raise DeepError("unknown strategy: '" + str(strategy) + "'")


class RoutedSupervisor:
    """Runs a Deep graph with routing, escalation, and approval gates."""

    def __init__(self, strategy="routed", quality_threshold=DEFAULT_THRESHOLD,
                 approver=None):
        if strategy not in STRATEGIES:
            raise DeepError("strategy must be one of: " + ", ".join(STRATEGIES))
        if not (0 < quality_threshold <= 1):
            raise DeepError("quality_threshold must be in (0, 1]")
        self.strategy = strategy
        self.quality_threshold = quality_threshold
        # Default approver approves everything; runners pass an
        # explicit simulated approver so the gate is visible.
        self.approver = approver if approver is not None else SimulatedApprover()

    def run(self, tasks):
        waves = compute_waves_deep(tasks)
        by_id = {t["id"]: t for t in tasks}
        wave_of = {}
        for idx, wave in enumerate(waves):
            for tid in wave:
                wave_of[tid] = idx
        records = {}
        traces = {}
        for wave in waves:
            for tid in wave:
                rec, events = self._run_task(
                    by_id[tid], wave_of[tid], records)
                records[tid] = rec
                traces[tid] = events
        order = topological_order_deep(tasks)
        ordered = [records[tid] for tid in order]
        trace = []
        for tid in order:
            for ev in traces[tid]:
                entry = dict(ev)
                entry["seq"] = len(trace) + 1
                trace.append(entry)
        executed = [r for r in ordered
                    if r["status"] in ("succeeded",)]
        summary = {
            "strategy": self.strategy,
            "total_tasks": len(ordered),
            "succeeded": sum(1 for r in ordered if r["status"] == "succeeded"),
            "rejected": sum(1 for r in ordered if r["status"] == "rejected"),
            "blocked": sum(1 for r in ordered if r["status"] == "blocked"),
            "waves": len(waves),
            "total_cost_units": sum(r["cost_units_total"] for r in ordered),
            "quality_pass": sum(1 for r in executed if r["quality_pass"]),
            "quality_fail": sum(1 for r in executed if not r["quality_pass"]),
            "escalations": sum(1 for r in ordered if r["escalated"]),
            "approvals_requested": sum(
                1 for r in ordered if r["approval"] in ("approved", "rejected")),
            "approvals_granted": sum(
                1 for r in ordered if r["approval"] == "approved"),
            "approvals_rejected": sum(
                1 for r in ordered if r["approval"] == "rejected"),
            "trace_length": len(trace),
        }
        summary["status"] = (
            "complete" if summary["rejected"] == 0 and summary["blocked"] == 0
            else "partial")
        return {"waves": waves, "tasks": ordered, "trace": trace,
                "summary": summary}

    def _run_task(self, task, wave_index, records):
        tid = task["id"]
        events = []

        def ev(event, detail):
            events.append({"wave": wave_index, "task_id": tid,
                           "event": event, "detail": detail})

        record = {
            "task_id": tid, "name": task["name"], "worker": task["worker"],
            "dependencies": list(task["dependencies"]), "wave": wave_index,
            "difficulty": task["difficulty"],
            "estimated_difficulty": task["estimated_difficulty"],
            "requires_approval": task["requires_approval"],
            "approval": "not_required", "status": None,
            "initial_tier": None, "final_tier": None, "escalated": False,
            "attempts": 0, "cost_units_total": 0,
            "quality": None, "quality_pass": False, "output": None,
            "error": None,
        }
        bad = [d for d in task["dependencies"]
               if records[d]["status"] != "succeeded"]
        if bad:
            record["status"] = "blocked"
            record["error"] = ("blocked by dependency: "
                               + ", ".join(sorted(bad)))
            ev("blocked", record["error"])
            return record, events
        if task["requires_approval"]:
            approved = bool(self.approver(task))
            if approved:
                record["approval"] = "approved"
                ev("approval_granted", "simulated approver approved task")
            else:
                record["approval"] = "rejected"
                record["status"] = "rejected"
                record["error"] = "rejected by approver (simulated)"
                ev("approval_rejected", "simulated approver rejected task")
                return record, events
        tier = choose_tier(task, self.strategy)
        record["initial_tier"] = tier
        ev("routed", "initial tier " + tier + " under strategy " + self.strategy)
        output = toy_worker_deep(task, tier)
        record["attempts"] = 1
        record["cost_units_total"] = (
            task["small_cost"] if tier == "small" else task["large_cost"])
        ev("attempt", "tier " + tier + " quality %.2f" % output["quality"])
        if (self.strategy == "routed" and tier == "small"
                and output["quality"] < self.quality_threshold):
            ev("quality_check_failed",
               "quality %.2f below threshold %.2f"
               % (output["quality"], self.quality_threshold))
            tier = "large"
            output = toy_worker_deep(task, tier)
            record["attempts"] = 2
            record["cost_units_total"] += task["large_cost"]
            record["escalated"] = True
            ev("escalated", "escalated once to large tier")
            ev("attempt", "tier large quality %.2f" % output["quality"])
        record["final_tier"] = tier
        record["quality"] = output["quality"]
        record["quality_pass"] = output["quality"] >= self.quality_threshold
        record["output"] = {"words": output["words"], "chars": output["chars"]}
        record["status"] = "succeeded"
        ev("quality_check_passed" if record["quality_pass"]
           else "quality_check_failed",
           "final quality %.2f, threshold %.2f"
           % (output["quality"], self.quality_threshold))
        ev("succeeded", "words=%d chars=%d" % (output["words"], output["chars"]))
        return record, events


def build_deep_scenario():
    """The Deep comparison scenario: 11 tasks, one report pipeline.

    Hand-computed expectations (threshold 0.80, small cost 2,
    large cost 5, simulated approver rejects D09 only):
    waves are [D01, D02, D09], [D03, D06, D07, D10],
    [D04, D05, D08], [D11] by topological level, sorted in wave.
    Executed tasks are 9: D09 is rejected and D10, which depends
    on D09, is blocked. All other tasks succeed in every strategy.

    all_small: cost 9 x 2 = 18. Quality passes only at true
    difficulty 1 and 2: D01, D02, D06, D11, so 4 passes, 5 fails,
    0 escalations.
    all_large: cost 9 x 5 = 45. Large passes at every difficulty,
    so 9 passes, 0 fails, 0 escalations.
    routed: small for D01, D02, D06, D11 (estimated at most 2 and
    truly easy, 4 x 2 = 8); large for D03, D04, D05, D08
    (4 x 5 = 20); D07 is underestimated (estimated 1, true 3),
    so it starts small, fails the quality check at 0.70, and
    escalates once to large (2 + 5 = 7, 1 escalation, then
    passes at 0.95). Total 8 + 20 + 7 = 35, 9 quality passes.
    Approvals in every strategy: 2 requested (D08, D09),
    1 granted (D08), 1 rejected (D09).
    """
    base = {"small_cost": 2, "large_cost": 5, "requires_approval": False}
    tasks = [
        {"id": "D01", "name": "outline", "worker": "Planner", "dependencies": [],
         "difficulty": 1, "estimated_difficulty": 1,
         "payload": "scope method results"},
        {"id": "D02", "name": "gather_numbers", "worker": "Researcher",
         "dependencies": [], "difficulty": 2, "estimated_difficulty": 2,
         "payload": "sales rose in the north region"},
        {"id": "D09", "name": "publish_external_summary", "worker": "Writer",
         "dependencies": [], "difficulty": 1, "estimated_difficulty": 1,
         "requires_approval": True,
         "payload": "external summary draft for release"},
        {"id": "D03", "name": "deep_analysis", "worker": "Analyst",
         "dependencies": ["D01", "D02"], "difficulty": 3,
         "estimated_difficulty": 3,
         "payload": "numbers show a steady climb over time"},
        {"id": "D06", "name": "chart_spec", "worker": "Analyst",
         "dependencies": ["D01"], "difficulty": 2, "estimated_difficulty": 2,
         "payload": "line chart of monthly totals"},
        {"id": "D07", "name": "subtle_fact_check", "worker": "Reviewer",
         "dependencies": ["D02"], "difficulty": 3, "estimated_difficulty": 1,
         "payload": "check every subtle claim once carefully"},
        {"id": "D10", "name": "external_appendix", "worker": "Writer",
         "dependencies": ["D09"], "difficulty": 2, "estimated_difficulty": 2,
         "payload": "appendix for the external summary"},
        {"id": "D04", "name": "risk_model", "worker": "Analyst",
         "dependencies": ["D03"], "difficulty": 4, "estimated_difficulty": 4,
         "payload": "model the downside cases in full detail"},
        {"id": "D05", "name": "hard_proof", "worker": "Reviewer",
         "dependencies": ["D03"], "difficulty": 5, "estimated_difficulty": 5,
         "payload": "prove the central claim with no gaps left"},
        {"id": "D08", "name": "release_review", "worker": "Reviewer",
         "dependencies": ["D03"], "difficulty": 4, "estimated_difficulty": 4,
         "requires_approval": True,
         "payload": "review the release package end to end"},
        {"id": "D11", "name": "assemble_report", "worker": "Assembler",
         "dependencies": ["D04", "D05", "D08"], "difficulty": 2,
         "estimated_difficulty": 2,
         "payload": "final assembled report package"},
    ]
    for t in tasks:
        merged = dict(base)
        merged.update(t)
        t.clear()
        t.update(merged)
    return tasks


def run_comparison(tasks=None, approver=None):
    """Run all three strategies on the same scenario and approver."""
    if tasks is None:
        tasks = build_deep_scenario()
    if approver is None:
        approver = SimulatedApprover(reject_ids={"D09"})
    results = {}
    for strategy in STRATEGIES:
        sup = RoutedSupervisor(strategy=strategy, approver=approver)
        # Fresh copies per strategy so runs cannot share mutation.
        results[strategy] = sup.run([dict(t) for t in tasks])
    return results
