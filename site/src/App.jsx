import { useMemo, useState, useEffect, useRef, useId } from 'react';
import deep from '../../level-3-deep/results_deep.json';
import sweep from '../../level-3-deep/results_sweep.json';
import scenario from '../../level-3-deep/scenario_deep.json';
import build from '../../level-2-build/results_build.json';
import learn from '../../level-1-learn/results_learn.json';
import deepPy from '../../level-3-deep/orchestrator_deep.py?raw';
import rootReadme from '../../README.md?raw';
import learnReadme from '../../level-1-learn/README.md?raw';
import buildReadme from '../../level-2-build/README.md?raw';
import deepReadme from '../../level-3-deep/README.md?raw';
import roadmap from '../../ROADMAP.md?raw';
import { parseConstants, runDeep, estimationSweep, STRATEGIES } from './router.js';

const REPO = 'https://github.com/JesunAhmadUshno/orchestrator-lab';
const blob = (p) => `${REPO}/blob/main/${p}`;
const SHA = __SHA256__; // computed from the committed results files by vite.config.js at build time

// Pull text straight out of the repo's Markdown so limits and grades are quoted, not retyped.
const mdSection = (md, heading) => {
  const i = md.indexOf(`\n## ${heading}`);
  if (i < 0) return '';
  const rest = md.slice(i + 1);
  const end = rest.indexOf('\n## ');
  return end < 0 ? rest : rest.slice(0, end);
};
const bullets = (text) => text.split('\n- ').slice(1).map((b) => b.split('\n\n')[0].replace(/\s*\n\s*/g, ' ').trim());
const grade = (md) => md.match(/Grade: ([\d,]+) of ([\d,]+)/).slice(1);
const RECORDED_ON = deepReadme.match(/DONE \((\d{4}-\d{2}-\d{2})\)/)[1];

const Q = parseConstants(deepPy);
const DEFAULTS = { threshold: deep.quality_threshold, cutoff: Q.cutoff, small: scenario.tasks[0].small_cost, large: scenario.tasks[0].large_cost, rejectIds: scenario.simulated_reject_ids };
const CMP = deep.comparison;
const canon = (v) => (Array.isArray(v) ? v.map(canon) : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, canon(v[k])])) : v);
const same = (a, b) => JSON.stringify(canon(a)) === JSON.stringify(canon(b));
const executedCount = (s) => s.quality_pass + s.quality_fail;
const designedEscalation = deep.strategies.routed.tasks.find((t) => t.escalated);
const approvalTasks = scenario.tasks.filter((t) => t.requires_approval).map((t) => t.id);
const LABEL = { all_small: 'all_small', all_large: 'all_large', routed: 'routed' };
const SCOLOR = { all_small: 'var(--warn)', all_large: 'var(--muted)', routed: 'var(--primary)' };

const OUT = {
  small: ['Small tier, passed', 'var(--good)'],
  large: ['Large tier, passed', 'var(--primary)'],
  escalated: ['Escalated small to large', 'var(--warn)'],
  fail: ['Quality fail', 'var(--bad)'],
  rejected: ['Rejected by simulated approver', 'var(--bad)'],
  blocked: ['Blocked by a dependency', 'var(--muted)'],
};
const outcome = (r) => (r.status === 'blocked' ? 'blocked' : r.status === 'rejected' ? 'rejected' : r.escalated ? 'escalated' : !r.quality_pass ? 'fail' : r.final_tier);

const SECTIONS = [['top', 'Overview', '◎'], ['compare', 'Strategies', '▥'], ['playground', 'Router', '⇄'], ['sweep', 'Sweep', '∿'], ['graph', 'Task graph', '◇'], ['trace', 'Trace', '≡'], ['build', 'Build + Learn', '▦'], ['limits', 'Limits', '!'], ['reproduce', 'Reproduce', '❯_']];

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

function MenuBar() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 30000); return () => clearInterval(t); }, []);
  return (
    <div className="menubar" role="banner">
      <span className="apple" aria-hidden="true">◆</span>
      <a className="app" href="#top">Orchestrator Lab</a>
      <a className="m" href={blob('SPEC.md')}>Spec</a>
      <a className="m" href={blob('level-3-deep/README.md')}>Deep level</a>
      <a className="m" href={blob('docs/research-review.md')}>Research review</a>
      <span className="spacer" />
      <span className="status"><i /> Deterministic results</span>
      <a href={REPO}>GitHub ↗</a>
      <span className="clock">{now.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</span>
    </div>
  );
}

function Dock() {
  const [active, setActive] = useState('top');
  useEffect(() => {
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)), { rootMargin: '-45% 0px -50% 0px' });
    SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);
  return (
    <nav className="dock" aria-label="Sections">
      {SECTIONS.map(([id, label, icon]) => (
        <a key={id} href={`#${id}`} className={active === id ? 'on' : ''} aria-current={active === id ? 'true' : undefined}>
          <span className="ico" aria-hidden="true">{icon}</span><span className="lbl">{label}</span>
        </a>
      ))}
    </nav>
  );
}

function Range({ label, value, min, max, step, onChange, show }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label} <span>{show}</span></label>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} />
    </div>
  );
}

function Seg({ label, value, options, onChange }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map(([k, l]) => <button key={k} aria-pressed={value === k} onClick={() => onChange(k)}>{l}</button>)}
    </div>
  );
}

export default function App() {
  useReveal();
  return (
    <div className="wrap">
      <MenuBar />
      <div className="glow" aria-hidden="true" />
      <Hero />
      <Compare />
      <Playground />
      <Sweep />
      <Graph />
      <Trace />
      <BuildLearn />
      <Limits />
      <Reproduce />
      <Dock />
      <footer>
        Code: Apache-2.0. Every number on this page is read at build time from the committed <code>level-*/results_*.json</code>, <code>scenario_deep.json</code>, <code>orchestrator_deep.py</code> and the level READMEs; the router and the sweep rerun in your browser and are checked against the Python results on every build.
      </footer>
    </div>
  );
}

function Hero() {
  const r = CMP.routed, L = CMP.all_large, S = CMP.all_small;
  return (
    <header className="card hero window" id="top" data-title="orchestrator.app — overview">
      <div className="head">
        <p className="eyebrow">Multi-agent orchestration · three levels · stdlib Python</p>
        <span className="pill warn">● Toy model, simulated approver</span>
      </div>
      <h1>Routing each task by estimated difficulty <em>cut cost</em> from {L.total_cost_units} to {r.total_cost_units} units while keeping all {r.quality_pass} quality passes.</h1>
      <p className="sub">
        One supervisor runs a task graph wave by wave. For each task it picks a cheap small tier or an expensive large tier from an estimate of difficulty, checks quality, escalates once if the small tier falls short, and pauses flagged tasks for an approver.
        The result above is from one designed {r.total_tasks}-task toy scenario, so read it as a property of the scenario and its quality table, not of real models.
      </p>
      <p className="scope">
        <b>Scope:</b> workers are deterministic toy functions, quality is a fixed table by true difficulty, the approver is a simulated reject list, and every run was on a CPU VM. Costs are unit counts, not money or tokens.
      </p>
      <div className="actions">
        <a className="btn primary" href="#playground">Rerun the router</a>
        <a className="btn ghost" href={blob('level-3-deep/README.md')}>Read the Deep level</a>
        <span className="hint">Reproduce with <code>python level-3-deep/run_deep.py</code></span>
      </div>
      <div className="tiles">
        <div className="tile"><div className="num">{r.total_cost_units}</div><div className="cap">routed cost units, {r.quality_pass} of {executedCount(r)} pass</div></div>
        <div className="tile"><div className="num">{L.total_cost_units}</div><div className="cap">all_large cost units, {L.quality_pass} of {executedCount(L)} pass</div></div>
        <div className="tile"><div className="num">{S.total_cost_units}</div><div className="cap">all_small cost units, only {S.quality_pass} of {executedCount(S)} pass</div></div>
        <div className="tile"><div className="num">{r.escalations}</div><div className="cap">escalation ({designedEscalation.task_id}, underestimated on purpose)</div></div>
      </div>
    </header>
  );
}

function Compare() {
  const saving = 1 - CMP.routed.total_cost_units / CMP.all_large.total_cost_units;
  const n = executedCount(CMP.routed);
  const W = 960, H = 320, pad = { l: 56, r: 24, t: 56, b: 44 };
  const xmax = Math.ceil((CMP.all_large.total_cost_units * 1.15) / 10) * 10;
  const x = (c) => pad.l + (c / xmax) * (W - pad.l - pad.r);
  const y = (p) => pad.t + (1 - p / n) * (H - pad.t - pad.b);
  return (
    <section id="compare" className="card window reveal" data-title="results_deep.json — strategy comparison">
      <p className="eyebrow">Recorded benchmark · {RECORDED_ON}</p>
      <h2>Same quality as going large every time, for <em>{(saving * 100).toFixed(1)}%</em> less.</h2>
      <p className="sub">
        Three strategies on the same graph and the same simulated approver. all_small is cheapest but fails the {deep.quality_threshold.toFixed(2)} quality threshold on every task harder than difficulty 2.
        Routed spends {CMP.routed.total_cost_units - CMP.all_small.total_cost_units} units more than all_small to buy back those passes, and {CMP.all_large.total_cost_units - CMP.routed.total_cost_units} units less than all_large.
      </p>
      <div className="scroll-x chartwrap">
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Cost against quality passes for the three strategies">
        {Array.from({ length: n + 1 }, (_, p) => p).filter((p) => p % 3 === 0 || p === n).map((p) => (
          <g key={p}><line className="axis" x1={pad.l} x2={W - pad.r} y1={y(p)} y2={y(p)} /><text x={pad.l - 10} y={y(p) + 4} textAnchor="end">{p}</text></g>
        ))}
        {Array.from({ length: xmax / 10 + 1 }, (_, i) => i * 10).map((c) => <text key={c} x={x(c)} y={H - 24} textAnchor="middle">{c}</text>)}
        <text x={pad.l} y={14}>quality passes (of {n} executed tasks)</text>
        <text x={W - pad.r} y={H - 6} textAnchor="end">total cost units</text>
        <line x1={x(CMP.routed.total_cost_units)} x2={x(CMP.all_large.total_cost_units)} y1={y(n) + 22} y2={y(n) + 22} stroke="var(--good)" strokeWidth="2" markerEnd="url(#arr)" />
        <defs><marker id="arr" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M10 0L0 5l10 5z" fill="var(--good)" /></marker></defs>
        <text x={(x(CMP.routed.total_cost_units) + x(CMP.all_large.total_cost_units)) / 2} y={y(n) + 40} textAnchor="middle" style={{ fill: 'var(--good)', fontWeight: 600 }}>−{CMP.all_large.total_cost_units - CMP.routed.total_cost_units} units</text>
        {STRATEGIES.map((s) => (
          <g key={s}>
            <line x1={x(0)} x2={x(CMP[s].total_cost_units)} y1={y(CMP[s].quality_pass)} y2={y(CMP[s].quality_pass)} stroke={SCOLOR[s]} strokeOpacity="0.35" strokeWidth="6" strokeLinecap="round" />
            <circle cx={x(CMP[s].total_cost_units)} cy={y(CMP[s].quality_pass)} r="9" fill={SCOLOR[s]} stroke="var(--surface-strong)" strokeWidth="3" />
            <text x={x(CMP[s].total_cost_units)} y={y(CMP[s].quality_pass) - 16} textAnchor="middle" style={{ fill: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{LABEL[s]}: {CMP[s].total_cost_units} units, {CMP[s].quality_pass}/{n}</text>
          </g>
        ))}
      </svg>
      </div>
      <div className="scroll-x">
        <table>
          <thead><tr><th>Strategy</th><th>Cost units</th><th>Quality pass</th><th>Quality fail</th><th>Escalations</th><th>Rejected</th><th>Blocked</th><th>Trace entries</th></tr></thead>
          <tbody>
            {STRATEGIES.map((s) => (
              <tr key={s}><td className="mono">{LABEL[s]}</td><td>{CMP[s].total_cost_units}</td><td>{CMP[s].quality_pass}</td><td className={CMP[s].quality_fail ? 'no' : ''}>{CMP[s].quality_fail}</td><td>{CMP[s].escalations}</td><td>{CMP[s].rejected}</td><td>{CMP[s].blocked}</td><td>{CMP[s].trace_length}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Playground() {
  const [cutoff, setCutoff] = useState(DEFAULTS.cutoff);
  const [threshold, setThreshold] = useState(DEFAULTS.threshold);
  const [small, setSmall] = useState(DEFAULTS.small);
  const [large, setLarge] = useState(DEFAULTS.large);
  const [est, setEst] = useState(designedEscalation.estimated_difficulty);
  const [reject, setReject] = useState(() => new Set(DEFAULTS.rejectIds));
  const largeCost = Math.max(large, small + 1);
  const res = useMemo(() => {
    const tasks = scenario.tasks.map((t) => ({ ...t, small_cost: small, large_cost: largeCost, ...(t.id === designedEscalation.task_id ? { estimated_difficulty: est } : {}) }));
    return Object.fromEntries(STRATEGIES.map((s) => [s, runDeep(tasks, { strategy: s, threshold, cutoff, quality: Q, rejectIds: [...reject] })]));
  }, [cutoff, threshold, small, largeCost, est, reject]);
  const matches = STRATEGIES.every((s) => same(res[s].summary, CMP[s]));
  const reset = () => { setCutoff(DEFAULTS.cutoff); setThreshold(DEFAULTS.threshold); setSmall(DEFAULTS.small); setLarge(DEFAULTS.large); setEst(designedEscalation.estimated_difficulty); setReject(new Set(DEFAULTS.rejectIds)); };
  const toggle = (id) => setReject((r) => { const n = new Set(r); n.has(id) ? n.delete(id) : n.add(id); return n; });
  return (
    <section id="playground" className="card window reveal" data-title="router.py — live in your browser">
      <div className="head">
        <div>
          <p className="eyebrow">Live router playground</p>
          <h2>Move the knobs and the supervisor <em>reruns</em> all three strategies.</h2>
          <p className="sub">
            A line-for-line JavaScript port of <a href={blob('level-3-deep/orchestrator_deep.py')}>orchestrator_deep.py</a>: topological waves, tier choice from the estimate, the quality table lookup, one escalation, and the approval gate with transitive blocking.
            The quality table is read from the Python source. At the default settings every build checks that this port reproduces <a href={blob('level-3-deep/results_deep.json')}>results_deep.json</a> field for field.
          </p>
        </div>
        <span className={`pill ${matches ? 'good' : 'info'}`}>{matches ? '● Matches results_deep.json' : '● What-if, not recorded'}</span>
      </div>
      <div className="controls">
        <Range label="Routing cutoff" value={cutoff} min={1} max={5} step={1} onChange={setCutoff} show={`est. ≤ ${cutoff} → small`} />
        <Range label="Quality threshold" value={threshold} min={0.6} max={0.95} step={0.05} onChange={(v) => setThreshold(Math.round(v * 100) / 100)} show={threshold.toFixed(2)} />
        <Range label="Small tier cost" value={small} min={1} max={4} step={1} onChange={setSmall} show={`${small} units`} />
        <Range label="Large tier cost" value={largeCost} min={small + 1} max={8} step={1} onChange={setLarge} show={`${largeCost} units`} />
        <Range label={`${designedEscalation.task_id} estimate (true ${designedEscalation.difficulty})`} value={est} min={1} max={5} step={1} onChange={setEst} show={est} />
        <div className="field checks">
          <span className="flabel">Simulated approver rejects</span>
          {approvalTasks.map((id) => (
            <label key={id} className="check"><input type="checkbox" checked={reject.has(id)} onChange={() => toggle(id)} /> {id} ({scenario.tasks.find((t) => t.id === id).name})</label>
          ))}
        </div>
      </div>
      <div className="actions" style={{ marginTop: 0, marginBottom: 16 }}>
        <button className="btn ghost" onClick={reset}>Reset to recorded settings</button>
        <span className="hint">Quality table (true difficulty 1 to 5): small {Object.values(Q.small).map((v) => v.toFixed(2)).join(' ')}, large {Object.values(Q.large).map((v) => v.toFixed(2)).join(' ')}.</span>
      </div>
      <div className="tiles" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', marginTop: 0 }}>
        {STRATEGIES.map((s) => {
          const m = res[s].summary;
          return (
            <div className={`tile strat ${s === 'routed' ? 'focus' : ''}`} key={s}>
              <div className="mono">{LABEL[s]}</div>
              <div className="num">{m.total_cost_units}<small> units</small></div>
              <div className="cap">{m.quality_pass} of {executedCount(m)} pass · {m.escalations} escalated · {m.rejected} rejected · {m.blocked} blocked</div>
            </div>
          );
        })}
      </div>
      <h3 style={{ marginTop: 20 }}>Routed run, task by task</h3>
      <div className="scroll-x">
        <table>
          <thead><tr><th>Task</th><th>Estimate / true</th><th>Path</th><th>Cost</th><th>Quality</th><th>Outcome</th></tr></thead>
          <tbody>
            {res.routed.tasks.map((t) => (
              <tr key={t.task_id}>
                <td><span className="mono">{t.task_id}</span> {t.name}</td>
                <td>{t.estimated_difficulty} / {t.difficulty}</td>
                <td>{t.initial_tier ? (t.escalated ? `${t.initial_tier} → ${t.final_tier}` : t.final_tier) : '—'}</td>
                <td>{t.cost_units_total}</td>
                <td className={t.quality == null ? '' : t.quality_pass ? 'ok' : 'no'}>{t.quality == null ? '—' : t.quality.toFixed(2)}</td>
                <td><span className="dot" style={{ background: OUT[outcome(t)][1] }} />{OUT[outcome(t)][0]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Sweep() {
  const [small, setSmall] = useState(sweep.estimation_error.small_cost);
  const [large, setLarge] = useState(sweep.estimation_error.large_cost);
  const lc = Math.max(large, small + 1);
  const res = useMemo(() => estimationSweep(scenario.tasks, { small, large: lc, quality: Q, threshold: DEFAULTS.threshold, cutoff: DEFAULTS.cutoff, rejectIds: DEFAULTS.rejectIds }), [small, lc]);
  const recorded = [sweep.estimation_error, sweep.estimation_error_large_cost_4].find((r) => r.small_cost === small && r.large_cost === lc);
  const matches = recorded && same(recorded, res);
  const rows = res.rows, K = rows.length - 1;
  const W = 960, H = 280, pad = { l: 48, r: 110, t: 16, b: 40 };
  const ymax = Math.ceil(Math.max(res.all_large_cost, ...rows.map((r) => r.cost_max)) * 1.1 / 5) * 5;
  const x = (k) => pad.l + (k / K) * (W - pad.l - pad.r);
  const y = (c) => pad.t + (1 - c / ymax) * (H - pad.t - pad.b);
  const band = [...rows.map((r) => `${x(r.k)},${y(r.cost_max)}`), ...rows.slice().reverse().map((r) => `${x(r.k)},${y(r.cost_min)}`)].join(' ');
  const be = res.break_even_k_worst_case, bm = res.break_even_k_mean;
  const last = rows[K];
  return (
    <section id="sweep" className="card window reveal" data-title="sweep.js — estimation error, live">
      <div className="head">
        <div>
          <p className="eyebrow">Live sensitivity model</p>
          <h2>How wrong can the estimates be <em>before routing stops paying</em>?</h2>
          <p className="sub">
            Start with perfect estimates, then underestimate k of the {res.executed_tasks.length} executed tasks (estimate set to 1) for every one of the {rows.reduce((s, r) => s + r.subsets, 0)} possible subsets.
            Each underestimated hard task goes small first, fails, and escalates, costing small + large instead of large. The band is the best and worst subset at each k; the line is the mean.
            This is a model on the toy quality table, computed in your browser, and it matches <a href={blob('level-3-deep/sweep_deep.py')}>sweep_deep.py</a> at the recorded cost settings.
          </p>
        </div>
        <span className={`pill ${matches ? 'good' : 'info'}`}>{matches ? '● Matches results_sweep.json' : '● What-if, not recorded'}</span>
      </div>
      <div className="controls" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        <Range label="Small tier cost" value={small} min={1} max={4} step={1} onChange={setSmall} show={`${small} units`} />
        <Range label="Large tier cost" value={lc} min={small + 1} max={8} step={1} onChange={setLarge} show={`${lc} units`} />
      </div>
      <div className="scroll-x chartwrap">
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Routed cost against number of underestimated tasks, with the all_large cost line">
        {Array.from({ length: Math.floor(ymax / 10) + 1 }, (_, i) => i * 10).map((c) => (
          <g key={c}><line className="axis" x1={pad.l} x2={W - pad.r} y1={y(c)} y2={y(c)} /><text x={pad.l - 8} y={y(c) + 4} textAnchor="end">{c}</text></g>
        ))}
        {rows.map((r) => <text key={r.k} x={x(r.k)} y={H - 20} textAnchor="middle">{r.k}</text>)}
        <text x={(pad.l + W - pad.r) / 2} y={H - 2} textAnchor="middle">tasks underestimated (k)</text>
        <polygon points={band} fill="var(--primary)" opacity="0.14" />
        <polyline fill="none" stroke="var(--primary)" strokeWidth="2.5" points={rows.map((r) => `${x(r.k)},${y(r.cost_mean)}`).join(' ')} />
        {rows.map((r) => <circle key={r.k} cx={x(r.k)} cy={y(r.cost_mean)} r="3.5" fill="var(--primary)" />)}
        <line x1={pad.l} x2={W - pad.r} y1={y(res.all_large_cost)} y2={y(res.all_large_cost)} stroke="var(--bad)" strokeDasharray="6 5" strokeWidth="1.5" />
        <text x={W - pad.r + 8} y={y(res.all_large_cost) + 4} style={{ fill: 'var(--bad)' }}>all_large {res.all_large_cost}</text>
        <text x={W - pad.r + 8} y={y(last.cost_mean) + (Math.abs(y(last.cost_mean) - y(res.all_large_cost)) < 16 ? 18 : 4)} style={{ fill: 'var(--primary)' }}>routed mean</text>
        {be != null && <line x1={x(be)} x2={x(be)} y1={pad.t} y2={H - pad.b} stroke="var(--warn)" strokeWidth="1.5" />}
      </svg>
      </div>
      <div className="tiles" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
        <div className="tile"><div className="num">{rows[0].cost_min}</div><div className="cap">routed cost with perfect estimates (k = 0)</div></div>
        <div className="tile"><div className="num">{last.cost_max}</div><div className="cap">worst case, all {K} underestimated, vs all_large {res.all_large_cost}</div></div>
        <div className="tile"><div className="num">{be == null ? 'none' : `k = ${be}`}</div><div className="cap">{be == null ? 'routed never reaches all_large at these costs' : `first k where some subset costs at least all_large${bm != null ? `; the mean crosses at k = ${bm}` : ''}`}</div></div>
      </div>
      <h3 style={{ marginTop: 24 }}>Recorded threshold sweep (sweep_deep.py, shipped scenario)</h3>
      <p className="hint" style={{ marginTop: 4, marginBottom: 8 }}>At thresholds of {sweep.threshold.find((r) => r.all_large.quality_fail > 0).threshold.toFixed(2)} and above the large tier itself fails the hardest task and there is no second escalation, so even all_large loses passes.</p>
      <div className="scroll-x">
        <table>
          <thead><tr><th>Threshold</th>{STRATEGIES.map((s) => <th key={s}>{LABEL[s]} cost / pass</th>)}<th>Routed escalations</th></tr></thead>
          <tbody>
            {sweep.threshold.map((r) => (
              <tr key={r.threshold} className={r.threshold === deep.quality_threshold ? 'cur' : ''}>
                <td>{r.threshold.toFixed(2)}{r.threshold === deep.quality_threshold ? ' (shipped)' : ''}</td>
                {STRATEGIES.map((s) => <td key={s} className={s === 'routed' && r.routed.cost > r.all_large.cost ? 'no' : ''}>{r[s].cost} / {r[s].quality_pass}</td>)}
                <td>{r.routed.escalations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 style={{ marginTop: 24 }}>Recorded cost-ratio and cutoff sweeps</h3>
      <div className="grid2" style={{ marginTop: 8 }}>
        <div className="scroll-x">
          <table>
            <thead><tr><th>Large cost (small {sweep.estimation_error.small_cost})</th><th>routed</th><th>all_large</th><th>Saving</th></tr></thead>
            <tbody>{sweep.large_cost.map((r) => <tr key={r.large_cost}><td>{r.large_cost}</td><td>{r.routed.cost}</td><td>{r.all_large.cost}</td><td>{(100 * (1 - r.routed.cost / r.all_large.cost)).toFixed(1)}%</td></tr>)}</tbody>
          </table>
        </div>
        <div className="scroll-x">
          <table>
            <thead><tr><th>Routing cutoff</th><th>routed cost</th><th>Passes</th><th>Escalations</th></tr></thead>
            <tbody>{sweep.routing_cutoff.map((r) => <tr key={r.cutoff} className={r.cutoff === DEFAULTS.cutoff ? 'cur' : ''}><td>{r.cutoff}{r.cutoff === DEFAULTS.cutoff ? ' (shipped)' : ''}</td><td>{r.routed.cost}</td><td>{r.routed.quality_pass}</td><td>{r.routed.escalations}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Graph() {
  const [strategy, setStrategy] = useState('routed');
  const [sel, setSel] = useState(designedEscalation.task_id);
  const run = deep.strategies[strategy];
  const recs = Object.fromEntries(run.tasks.map((t) => [t.task_id, t]));
  const W = 760, colW = W / run.waves.length, rowH = 64, H = Math.max(...run.waves.map((w) => w.length)) * rowH + 40, nw = 132, nh = 40;
  const pos = {};
  run.waves.forEach((w, wi) => w.forEach((id, i) => { pos[id] = [wi * colW + colW / 2, 40 + i * rowH + (H - 40 - w.length * rowH) / 2 + rowH / 2]; }));
  const r = recs[sel];
  return (
    <section id="graph" className="card window reveal" data-title={`task_graph.svg — ${run.tasks.length} tasks, ${run.waves.length} waves`}>
      <div className="head">
        <div>
          <p className="eyebrow">Recorded task graph</p>
          <h2>{run.waves.length} waves, coloured by what <em>actually happened</em> to each task.</h2>
          <p className="sub">Columns are topological waves. Lines are dependencies. Rejecting one task blocks everything downstream of it. Click a task to open its recorded record.</p>
        </div>
        <Seg label="Strategy shown" value={strategy} onChange={setStrategy} options={STRATEGIES.map((s) => [s, LABEL[s]])} />
      </div>
      <div className="scroll-x chartwrap">
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Task graph for the ${strategy} strategy`}>
        {run.waves.map((_, wi) => <text key={wi} x={wi * colW + colW / 2} y={16} textAnchor="middle">wave {wi + 1}</text>)}
        {run.tasks.flatMap((t) => t.dependencies.map((d) => {
          const [x1, y1] = pos[d], [x2, y2] = pos[t.task_id];
          return <path key={d + t.task_id} d={`M${x1 + nw / 2},${y1} C${x1 + nw / 2 + 30},${y1} ${x2 - nw / 2 - 30},${y2} ${x2 - nw / 2},${y2}`} fill="none" stroke="var(--muted)" strokeOpacity={sel === t.task_id || sel === d ? 0.9 : 0.3} strokeWidth={sel === t.task_id || sel === d ? 2 : 1.2} />;
        }))}
        {run.tasks.map((t) => {
          const [cx, cy] = pos[t.task_id], o = outcome(t);
          return (
            <g key={t.task_id} className="node" role="button" tabIndex={0} aria-label={`${t.task_id} ${t.name}: ${OUT[o][0]}`} aria-pressed={sel === t.task_id}
              onClick={() => setSel(t.task_id)} onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), setSel(t.task_id))}>
              <rect x={cx - nw / 2} y={cy - nh / 2} width={nw} height={nh} rx="10" fill="var(--surface-strong)" stroke={sel === t.task_id ? 'var(--text)' : 'var(--border)'} strokeWidth={sel === t.task_id ? 2 : 1} strokeDasharray={o === 'rejected' || o === 'blocked' ? '4 3' : ''} />
              <rect x={cx - nw / 2 + 6} y={cy - nh / 2 + 6} width="6" height={nh - 12} rx="3" fill={OUT[o][1]} />
              <text x={cx - nw / 2 + 20} y={cy - 3} style={{ fill: 'var(--text)', fontWeight: 600, fontSize: 12 }}>{t.task_id}</text>
              <text x={cx - nw / 2 + 20} y={cy + 12}>{t.name.length > 16 ? `${t.name.slice(0, 15)}…` : t.name}</text>
            </g>
          );
        })}
      </svg>
      </div>
      <div className="legend">{Object.entries(OUT).map(([k, [l, c]]) => <span key={k}><i style={{ background: c }} />{l}</span>)}</div>
      {r && (
        <div className="record" aria-live="polite">
          <div className="head" style={{ marginBottom: 8 }}><h3><span className="mono">{r.task_id}</span> {r.name} · {r.worker}</h3><span className="pill info">{OUT[outcome(r)][0]}</span></div>
          <dl>
            <div><dt>Wave</dt><dd>{r.wave + 1}</dd></div>
            <div><dt>Depends on</dt><dd>{r.dependencies.join(', ') || 'nothing'}</dd></div>
            <div><dt>Difficulty est. / true</dt><dd>{r.estimated_difficulty} / {r.difficulty}</dd></div>
            <div><dt>Approval</dt><dd>{r.approval.replace('_', ' ')}</dd></div>
            <div><dt>Tier</dt><dd>{r.initial_tier ? (r.escalated ? `${r.initial_tier} → ${r.final_tier}` : r.final_tier) : '—'}</dd></div>
            <div><dt>Attempts / cost</dt><dd>{r.attempts} / {r.cost_units_total} units</dd></div>
            <div><dt>Quality</dt><dd>{r.quality == null ? '—' : `${r.quality.toFixed(2)} ${r.quality_pass ? 'pass' : 'fail'}`}</dd></div>
            <div><dt>Error</dt><dd>{r.error || 'none'}</dd></div>
          </dl>
        </div>
      )}
    </section>
  );
}

function Trace() {
  const [strategy, setStrategy] = useState('routed');
  const trace = deep.strategies[strategy].trace;
  const [step, setStep] = useState(trace.length);
  const [playing, setPlaying] = useState(false);
  const box = useRef(null);
  const cur = Math.min(step, trace.length);
  useEffect(() => { setStep(trace.length); setPlaying(false); }, [strategy, trace.length]);
  useEffect(() => {
    if (!playing) return undefined;
    if (cur >= trace.length) { setPlaying(false); return undefined; }
    const t = setTimeout(() => setStep((s) => s + 1), 350);
    return () => clearTimeout(t);
  }, [playing, cur, trace.length]);
  useEffect(() => {
    const el = box.current?.querySelector('.now');
    if (el && box.current) box.current.scrollTop = el.offsetTop - box.current.clientHeight / 2;
  }, [cur]);
  const tone = (e) => (/rejected|failed|blocked/.test(e) ? 'no' : /escalated/.test(e) ? 'warnc' : /passed|succeeded|granted/.test(e) ? 'ok' : '');
  return (
    <section id="trace" className="card window reveal" data-title="trace.log — recorded replay">
      <div className="head">
        <div>
          <p className="eyebrow">Recorded run, {RECORDED_ON} · replay, not live</p>
          <h2>Step through every decision the supervisor <em>wrote down</em>.</h2>
          <p className="sub">The full trace from <a href={blob('level-3-deep/results_deep.json')}>results_deep.json</a>: {STRATEGIES.map((s) => `${deep.strategies[s].trace.length} entries for ${LABEL[s]}`).join(', ')}. Nothing here is recomputed; it replays the stored log.</p>
        </div>
        <Seg label="Trace to replay" value={strategy} onChange={setStrategy} options={STRATEGIES.map((s) => [s, LABEL[s]])} />
      </div>
      <div className="controls" style={{ gridTemplateColumns: 'minmax(0, 1fr) auto', alignItems: 'end' }}>
        <Range label="Trace step" value={cur} min={0} max={trace.length} step={1} onChange={(v) => { setPlaying(false); setStep(v); }} show={`${cur} of ${trace.length}`} />
        <div className="actions" style={{ marginTop: 0 }}>
          <button className="btn ghost" onClick={() => { setPlaying(false); setStep(Math.max(0, cur - 1)); }} aria-label="Previous step">←</button>
          <button className="btn primary" onClick={() => { if (cur >= trace.length) setStep(0); setPlaying((p) => !p); }}>{playing ? 'Pause' : 'Replay'}</button>
          <button className="btn ghost" onClick={() => { setPlaying(false); setStep(Math.min(trace.length, cur + 1)); }} aria-label="Next step">→</button>
        </div>
      </div>
      <div className="log" ref={box} style={{ overflow: 'auto' }} tabIndex={0} aria-label="Trace log">
        {trace.map((e, i) => (
          <div key={e.seq} className={`line ${i < cur ? 'done' : 'todo'} ${i === cur - 1 ? 'now' : ''}`}>
            <span className="seq">{String(e.seq).padStart(2, '0')}</span>
            <span className="w">w{e.wave + 1}</span>
            <span className="tid">{e.task_id}</span>
            <span className={`ev ${tone(e.event)}`}>{e.event}</span>
            <span className="det">{e.detail}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function BuildLearn() {
  const s = build.summary, l = learn.summary;
  const statusPill = (st) => <span className={`pill ${st === 'succeeded' ? 'good' : st === 'failed' ? 'bad' : 'warn'}`}>{st}</span>;
  return (
    <>
      <section id="build" className="card window reveal" data-title="results_build.json — thread pool run">
        <p className="eyebrow">Level 2, Build · recorded run</p>
        <h2>A real thread pool with timeouts, retries and <em>transitive blocking</em>.</h2>
        <p className="sub">
          {s.total_tasks} tasks in {s.waves} waves on a {s.max_workers}-worker pool. Transient failures and wall-clock timeouts retry with backoff; step-budget failures never retry; a failed task blocks everything that depends on it.
          Real thread timing is deliberately left out of the results file so it stays byte-identical across runs, so no timing chart is shown here.
        </p>
        <div className="tiles">
          <div className="tile"><div className="num">{s.succeeded}/{s.total_tasks}</div><div className="cap">tasks succeeded ({s.failed} failed, {s.blocked} blocked)</div></div>
          <div className="tile"><div className="num">{s.total_cost_units}</div><div className="cap">cost units over {s.total_attempts} attempts</div></div>
          <div className="tile"><div className="num">{s.retries_used}</div><div className="cap">retries used, {s.total_backoff_delay_seconds}s total backoff</div></div>
          <div className="tile"><div className="num">{s.timeout_attempts}</div><div className="cap">attempts killed by the wall-clock timeout</div></div>
        </div>
        <div className="scroll-x" style={{ marginTop: 16 }}>
          <table>
            <thead><tr><th>Task</th><th>Wave</th><th>Worker</th><th>Attempts</th><th>Timeouts</th><th>Steps / budget</th><th>Cost</th><th>Status</th><th>Error</th></tr></thead>
            <tbody>
              {build.tasks.map((t) => (
                <tr key={t.task_id}>
                  <td><span className="mono">{t.task_id}</span> {t.name}</td><td>{t.wave + 1}</td><td>{t.worker}</td><td>{t.attempts}</td><td>{t.timeout_attempts}</td>
                  <td>{t.steps_used} / {t.step_budget}</td><td>{t.cost_units_total}</td><td>{statusPill(t.status)}</td><td className="hint">{t.error || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card window reveal" data-title="results_learn.json — supervisor waves">
        <p className="eyebrow">Level 1, Learn · recorded run</p>
        <h2>The core idea in {l.total_tasks} tasks: waves, one retry, a <em>step budget</em>.</h2>
        <p className="sub">{l.succeeded} succeeded, {l.failed} failed, {l.blocked} blocked; {l.total_cost_units} cost units over {l.total_attempts} attempts and {l.total_steps_used} steps. Tasks inside a wave run one after another at this level.</p>
        <div className="waves" style={{ marginTop: 16 }}>
          {learn.waves.map((w, wi) => (
            <div className="wave" key={wi}>
              <div className="hint">Wave {wi + 1}</div>
              {w.map((id) => { const t = learn.tasks.find((x) => x.task_id === id); return (
                <div className="wtask" key={id}><span className="mono">{id}</span> {t.name}<div>{statusPill(t.status)}{t.retries_used ? <span className="hint"> {t.retries_used} retry</span> : null}</div></div>
              ); })}
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

function Limits() {
  const levels = { learn: ['Learn', learnReadme, 'level-1-learn/README.md'], build: ['Build', buildReadme, 'level-2-build/README.md'], deep: ['Deep', deepReadme, 'level-3-deep/README.md'] };
  const [lvl, setLvl] = useState('deep');
  const [name, md, path] = levels[lvl];
  const [g, of] = grade(md);
  const deductions = bullets(mdSection(md, 'Grade'));
  const backlog = bullets(mdSection(roadmap, 'v1.1 backlog'));
  return (
    <section id="limits" className="card window reveal" data-title="README.md — failure modes and limits">
      <div className="head">
        <div>
          <p className="eyebrow">Limits, threats and the repo's own grades</p>
          <h2>What this does <em>not</em> show.</h2>
          <p className="sub">Quoted from the level READMEs at build time. The grades are the repo's self-assessment, not an external review; the PhD-rubric review is in <a href={blob('docs/research-review.md')}>docs/research-review.md</a>.</p>
        </div>
        <Seg label="Level" value={lvl} onChange={setLvl} options={Object.entries(levels).map(([k, [n]]) => [k, n])} />
      </div>
      <div className="grid2">
        <div>
          <h3>Failure modes and limits ({name})</h3>
          <ul className="limits">{bullets(mdSection(md, 'Failure modes and limits')).map((b) => <li key={b}>{b}</li>)}</ul>
        </div>
        <div>
          <div className="tile">
            <div className="num">{g}<small> of {of}</small></div>
            <div className="cap">self-assessed grade, {name} level (<a href={blob(path)}>{path}</a>)</div>
          </div>
          <ul className="limits">{deductions.map((b) => <li key={b}>{b}</li>)}</ul>
        </div>
      </div>
      <h3 style={{ marginTop: 20 }}>v1.1 backlog (ROADMAP.md, not built)</h3>
      <div className="docs" style={{ marginTop: 10 }}>
        {backlog.map((b) => { const [t, ...rest] = b.split(': '); return <div className="doc" key={t}><b>{t}</b><small>{rest.join(': ')}</small></div>; })}
      </div>
    </section>
  );
}

function Reproduce() {
  const recorded = (label) => rootReadme.match(new RegExp(`${label} \\|[^|]*sha256 ([0-9a-f]+)`))?.[1];
  const rows = Object.entries(SHA).map(([f, h]) => {
    const rec = f.includes('deep.json') ? recorded('Deep determinism') : f.includes('build.json') ? recorded('Build determinism') : null;
    return { f, h, rec };
  });
  const docs = [
    ['SPEC.md', 'Spec', 'Scope and acceptance criteria'],
    ['level-1-learn/README.md', 'Learn', 'Supervisor and waves'],
    ['level-2-build/README.md', 'Build', 'Thread pool, timeouts, retries'],
    ['level-3-deep/README.md', 'Deep', 'Routing and approval gates'],
    ['docs/research-review.md', 'Research review', 'Graded gaps and fixes'],
    ['NOVELTY.md', 'Novelty', 'Honest size of the claim'],
  ];
  return (
    <section id="reproduce" className="card window reveal" data-title="Terminal — python level-3-deep/run_deep.py">
      <p className="eyebrow">Reproduce it</p>
      <h2>Standard library only. Every result file rebuilds <em>byte for byte</em>.</h2>
      <ol className="steps" style={{ marginTop: 16 }}>
        <li><span className="n">1</span><div><b>Clone</b><div className="hint"><code>git clone {REPO}.git && cd orchestrator-lab</code></div></div></li>
        <li><span className="n">2</span><div><b>Rerun the three levels and the sweep</b><div className="hint"><code>python level-1-learn/run_learn.py && python level-2-build/run_build.py && python level-3-deep/run_deep.py && python level-3-deep/sweep_deep.py</code></div></div></li>
        <li><span className="n">3</span><div><b>Run the tests</b><div className="hint"><code>python -m unittest discover -s tests</code></div></div></li>
        <li><span className="n">4</span><div><b>Check the browser port</b><div className="hint"><code>cd site && npm ci && npm run build</code> fails if the JavaScript router disagrees with any Python result.</div></div></li>
      </ol>
      <h3 style={{ marginTop: 20 }}>sha256 of the committed results (computed at build)</h3>
      <div className="scroll-x">
        <table>
          <thead><tr><th>File</th><th>sha256 (first 16)</th><th>README record</th></tr></thead>
          <tbody>{rows.map(({ f, h, rec }) => (
            <tr key={f}><td className="mono">{f}</td><td className="mono">{h.slice(0, 16)}</td><td>{rec ? <span className={h.startsWith(rec) ? 'ok' : 'no'}>{h.startsWith(rec) ? 'matches ' : 'differs from '}{rec}</span> : <span className="hint">no hash recorded</span>}</td></tr>
          ))}</tbody>
        </table>
      </div>
      <div className="docs" style={{ marginTop: 20 }}>
        {docs.map(([p, t, d]) => <a key={p} href={blob(p)}><b>{t}</b><small>{d}</small></a>)}
      </div>
    </section>
  );
}
