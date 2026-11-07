// Browser port of level-3-deep/orchestrator_deep.py (RoutedSupervisor) and
// level-3-deep/sweep_deep.py (the sweeps). Constants are parsed from the Python
// source at build time, never retyped. router.check.mjs asserts this port
// reproduces results_deep.json and results_sweep.json exactly.

// Reads SMALL_QUALITY, LARGE_QUALITY, DEFAULT_THRESHOLD and DEFAULT_ROUTING_CUTOFF from the .py text.
export function parseConstants(py) {
  const table = (name) => {
    const m = py.match(new RegExp(`${name} = \\{([^}]*)\\}`));
    if (!m) throw new Error(`missing ${name} in orchestrator_deep.py`);
    return Object.fromEntries(m[1].split(',').map((kv) => kv.split(':').map(Number)));
  };
  const num = (name) => {
    const m = py.match(new RegExp(`^${name} = ([0-9.]+)$`, 'm'));
    if (!m) throw new Error(`missing ${name} in orchestrator_deep.py`);
    return Number(m[1]);
  };
  return { small: table('SMALL_QUALITY'), large: table('LARGE_QUALITY'), threshold: num('DEFAULT_THRESHOLD'), cutoff: num('DEFAULT_ROUTING_CUTOFF') };
}

export const STRATEGIES = ['all_small', 'all_large', 'routed'];
const f2 = (x) => x.toFixed(2);

export function computeWaves(tasks) {
  const byId = Object.fromEntries(tasks.map((t) => [t.id, t]));
  const levels = {};
  const visiting = new Set();
  const levelOf = (id) => {
    if (id in levels) return levels[id];
    if (visiting.has(id)) throw new Error(`dependency cycle detected at task '${id}'`);
    visiting.add(id);
    const deps = byId[id].dependencies;
    const lvl = deps.length ? 1 + Math.max(...deps.map(levelOf)) : 0;
    visiting.delete(id);
    levels[id] = lvl;
    return lvl;
  };
  tasks.forEach((t) => levelOf(t.id));
  const max = Math.max(-1, ...Object.values(levels));
  return Array.from({ length: max + 1 }, (_, n) => Object.keys(levels).filter((id) => levels[id] === n).sort());
}

// Same output shape as RoutedSupervisor.run: { waves, tasks, trace, summary }.
export function runDeep(tasks, { strategy = 'routed', threshold, cutoff, quality, rejectIds = [] }) {
  const reject = new Set(rejectIds);
  const waves = computeWaves(tasks);
  const byId = Object.fromEntries(tasks.map((t) => [t.id, t]));
  const records = {};
  const traces = {};
  waves.forEach((wave, wi) => wave.forEach((id) => {
    const [rec, events] = runTask(byId[id], wi, records);
    records[id] = rec;
    traces[id] = events;
  }));

  function runTask(task, wave, recs) {
    const events = [];
    const ev = (event, detail) => events.push({ wave, task_id: task.id, event, detail });
    const r = {
      task_id: task.id, name: task.name, worker: task.worker, dependencies: [...task.dependencies], wave,
      difficulty: task.difficulty, estimated_difficulty: task.estimated_difficulty, requires_approval: task.requires_approval,
      approval: 'not_required', status: null, initial_tier: null, final_tier: null, escalated: false,
      attempts: 0, cost_units_total: 0, quality: null, quality_pass: false, output: null, error: null,
    };
    const bad = task.dependencies.filter((d) => recs[d].status !== 'succeeded');
    if (bad.length) {
      r.status = 'blocked';
      r.error = `blocked by dependency: ${[...bad].sort().join(', ')}`;
      ev('blocked', r.error);
      return [r, events];
    }
    if (task.requires_approval) {
      if (!reject.has(task.id)) {
        r.approval = 'approved';
        ev('approval_granted', 'simulated approver approved task');
      } else {
        r.approval = 'rejected';
        r.status = 'rejected';
        r.error = 'rejected by approver (simulated)';
        ev('approval_rejected', 'simulated approver rejected task');
        return [r, events];
      }
    }
    let tier = strategy === 'all_small' ? 'small' : strategy === 'all_large' ? 'large' : task.estimated_difficulty <= cutoff ? 'small' : 'large';
    r.initial_tier = tier;
    ev('routed', `initial tier ${tier} under strategy ${strategy}`);
    let q = quality[tier][task.difficulty];
    r.attempts = 1;
    r.cost_units_total = tier === 'small' ? task.small_cost : task.large_cost;
    ev('attempt', `tier ${tier} quality ${f2(q)}`);
    if (strategy === 'routed' && tier === 'small' && q < threshold) {
      ev('quality_check_failed', `quality ${f2(q)} below threshold ${f2(threshold)}`);
      tier = 'large';
      q = quality.large[task.difficulty];
      r.attempts = 2;
      r.cost_units_total += task.large_cost;
      r.escalated = true;
      ev('escalated', 'escalated once to large tier');
      ev('attempt', `tier large quality ${f2(q)}`);
    }
    const words = task.payload.split(/\s+/).filter(Boolean).length, chars = task.payload.length;
    r.final_tier = tier;
    r.quality = q;
    r.quality_pass = q >= threshold;
    r.output = { words, chars };
    r.status = 'succeeded';
    ev(r.quality_pass ? 'quality_check_passed' : 'quality_check_failed', `final quality ${f2(q)}, threshold ${f2(threshold)}`);
    ev('succeeded', `words=${words} chars=${chars}`);
    return [r, events];
  }

  const order = waves.flat();
  const ordered = order.map((id) => records[id]);
  const trace = [];
  order.forEach((id) => traces[id].forEach((e) => trace.push({ ...e, seq: trace.length + 1 })));
  const count = (f) => ordered.filter(f).length;
  const executed = ordered.filter((r) => r.status === 'succeeded');
  const summary = {
    strategy, total_tasks: ordered.length,
    succeeded: count((r) => r.status === 'succeeded'), rejected: count((r) => r.status === 'rejected'), blocked: count((r) => r.status === 'blocked'),
    waves: waves.length, total_cost_units: ordered.reduce((s, r) => s + r.cost_units_total, 0),
    quality_pass: executed.filter((r) => r.quality_pass).length, quality_fail: executed.filter((r) => !r.quality_pass).length,
    escalations: count((r) => r.escalated),
    approvals_requested: count((r) => r.approval === 'approved' || r.approval === 'rejected'),
    approvals_granted: count((r) => r.approval === 'approved'), approvals_rejected: count((r) => r.approval === 'rejected'),
    trace_length: trace.length,
  };
  summary.status = summary.rejected === 0 && summary.blocked === 0 ? 'complete' : 'partial';
  return { waves, tasks: ordered, trace, summary };
}

function* combinations(arr, k, start = 0, acc = []) {
  if (acc.length === k) { yield acc; return; }
  for (let i = start; i < arr.length; i++) yield* combinations(arr, k, i + 1, [...acc, arr[i]]);
}

const withCosts = (tasks, small, large) => tasks.map((t) => ({ ...t, small_cost: small, large_cost: large }));

// Mirror of sweep_deep.estimation_sweep: oracle estimates, then every subset of k executed tasks underestimated to 1.
export function estimationSweep(tasks, { small, large, quality, threshold, cutoff, rejectIds }) {
  const opts = { threshold, cutoff, quality, rejectIds };
  const oracle = withCosts(tasks, small, large).map((t) => ({ ...t, estimated_difficulty: t.difficulty }));
  const executed = runDeep(oracle, opts).tasks.filter((r) => r.status === 'succeeded').map((r) => r.task_id);
  const allLarge = runDeep(oracle, { ...opts, strategy: 'all_large' }).summary.total_cost_units;
  const rows = [];
  for (let k = 0; k <= executed.length; k++) {
    const costs = [], passes = [], escs = [];
    for (const subset of combinations(executed, k)) {
      const low = new Set(subset);
      const s = runDeep(oracle.map((t) => (low.has(t.id) ? { ...t, estimated_difficulty: 1 } : t)), opts).summary;
      costs.push(s.total_cost_units); passes.push(s.quality_pass); escs.push(s.escalations);
    }
    const sum = costs.reduce((a, b) => a + b, 0);
    rows.push({
      k, subsets: costs.length, cost_min: Math.min(...costs), cost_max: Math.max(...costs), cost_sum: sum,
      cost_mean: Math.round((sum / costs.length) * 1e4) / 1e4,
      quality_pass_min: Math.min(...passes), quality_pass_max: Math.max(...passes),
      escalations_sum: escs.reduce((a, b) => a + b, 0),
      subsets_at_or_above_all_large: costs.filter((c) => c >= allLarge).length,
    });
  }
  const firstK = (key) => rows.find((r) => r[key] >= allLarge)?.k ?? null;
  return {
    small_cost: small, large_cost: large, executed_tasks: executed, all_large_cost: allLarge, rows,
    break_even_k_worst_case: firstK('cost_max'), break_even_k_mean: firstK('cost_mean'),
  };
}

export const strategyRow = (s) => ({ cost: s.total_cost_units, quality_pass: s.quality_pass, quality_fail: s.quality_fail, escalations: s.escalations });
export { withCosts };
