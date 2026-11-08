// Known-answer self-check, run by "npm run build": node src/router.check.mjs
// The browser router must reproduce the Python results files exactly.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { parseConstants, runDeep, estimationSweep, strategyRow, withCosts, STRATEGIES } from './router.js';

const read = (p) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const deep = JSON.parse(read('level-3-deep/results_deep.json'));
const sweep = JSON.parse(read('level-3-deep/results_sweep.json'));
const scenario = JSON.parse(read('level-3-deep/scenario_deep.json'));
const C = parseConstants(read('level-3-deep/orchestrator_deep.py'));
const base = { quality: C, threshold: deep.quality_threshold, cutoff: C.cutoff, rejectIds: scenario.simulated_reject_ids };
assert.equal(C.threshold, deep.quality_threshold);

// 1. Every strategy: waves, task records, 42/39/39-entry traces and summaries, field for field.
for (const s of STRATEGIES) assert.deepEqual(runDeep(scenario.tasks, { ...base, strategy: s }), deep.strategies[s], `strategy ${s}`);
for (const s of STRATEGIES) assert.deepEqual(deep.comparison[s], deep.strategies[s].summary);

// 2. The sweeps written by sweep_deep.py.
assert.deepEqual(estimationSweep(scenario.tasks, { ...base, small: 2, large: 5 }), sweep.estimation_error);
assert.deepEqual(estimationSweep(scenario.tasks, { ...base, small: 2, large: 4 }), sweep.estimation_error_large_cost_4);
for (const row of sweep.threshold)
  for (const s of STRATEGIES) assert.deepEqual(strategyRow(runDeep(scenario.tasks, { ...base, strategy: s, threshold: row.threshold }).summary), row[s], `threshold ${row.threshold} ${s}`);
for (const row of sweep.large_cost)
  for (const s of STRATEGIES) assert.deepEqual(strategyRow(runDeep(withCosts(scenario.tasks, 2, row.large_cost), { ...base, strategy: s }).summary), row[s], `large cost ${row.large_cost} ${s}`);
for (const row of sweep.routing_cutoff)
  assert.deepEqual(strategyRow(runDeep(scenario.tasks, { ...base, cutoff: row.cutoff }).summary), row.routed, `cutoff ${row.cutoff}`);

// 3. Headline saving and the determinism hashes recorded in REPORT.md.
const saving = 1 - deep.comparison.routed.total_cost_units / deep.comparison.all_large.total_cost_units;
assert.equal((saving * 100).toFixed(1), '22.2');
const report = read('REPORT.md');
for (const [file, label] of [['level-3-deep/results_deep.json', 'Deep determinism'], ['level-2-build/results_build.json', 'Build determinism']]) {
  const rec = report.match(new RegExp(`${label} \\|[^|]*sha256 ([0-9a-f]+)`))[1];
  assert.ok(createHash('sha256').update(read(file)).digest('hex').startsWith(rec), `${file} sha256 differs from REPORT record ${rec}`);
}
console.log('router ok', { strategies: STRATEGIES.length, sweeps: 5, routed: deep.comparison.routed.total_cost_units, saving: (saving * 100).toFixed(1) });
