// Ensaio do codigo publico sem alterar seu modelo ou sua implementacao.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { Tokenizer } from './router-publico/node_modules/tokenizers/index.js';
import { Lfm2Router, route, buildPrefix, buildInputs } from './router-publico/src/router.ts';

const ROOT = import.meta.dirname;
const OUT = path.join(ROOT, 'resultados/router-local-v01');
const ASSETS = path.join(ROOT, 'router-assets');
const phase = process.argv[2];
if (!['prepare', 'development', 'evaluation'].includes(phase)) throw new Error('Use prepare, development ou evaluation.');
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const save = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n');
const source = fs.readFileSync(path.join(ROOT, 'resultados/casos_jev.jsonl'));
const cases = source.toString('utf8').trim().split(/\r?\n/).map(JSON.parse);
const originalQuestions = read(path.join(ROOT, 'resultados/perguntas_jev.json')).questions;
const config = {
  version: 'router-local-v01',
  model: 'onnx/model_quantized.onnx', executionProviders: ['cpu'], threads: 6,
  language: 'English',
  note: 'Compact factual representation and conditional category descriptions; no expected labels in inference. Two routes per opportunity. No retraining, threshold, deterministic correction or output cache.',
  questions: {
    qualification: {
      labels: ['incomplete_profile', 'discovery_required', 'negotiation_reviewable', 'human_review'],
      cats: ['Missing account: incomplete profile.', 'Known account, Prospecting: discovery required.', 'Known account, Engaging: negotiation reviewable.', 'Invalid or contradictory data: human review.'],
    },
    next_action: {
      labels: ['identify_account', 'qualify_prospect', 'review_old_negotiation', 'continue_negotiation_review', 'human_review'],
      cats: ['Missing account: identify the company.', 'Known account, Prospecting: qualify needs.', 'Known account, Engaging, age above reference: review old negotiation.', 'Known account, Engaging, age not above reference: review next step.', 'Invalid or contradictory data: human review.'],
    },
  },
};

function stateText(state) {
  if (typeof state.account_identified !== 'boolean' || typeof state.age_exceeds_reference_p90 !== 'boolean') throw new Error('Invalid source field type');
  return `Account identified: ${state.account_identified ? 'yes' : 'no'}. Stage: ${state.stage}. Age days: ${state.age_days ?? 'unknown'}; reference days: ${state.reference_p90_days}. Age above reference: ${state.age_exceeds_reference_p90 ? 'yes' : 'no'}.`;
}

const tok = await Tokenizer.fromFile(path.join(ASSETS, 'tokenizer.json'));
const scriptHash = digest(fs.readFileSync(import.meta.filename));
const configHash = digest(JSON.stringify(config));
const caseHash = digest(source);
const summaryStats = values => {
  const sorted = [...values].sort((a, b) => a - b);
  const p = q => sorted[Math.max(0, Math.ceil(sorted.length * q) - 1)];
  return {n: sorted.length, min: sorted[0], p50: p(.5), p95: p(.95), max: sorted.at(-1)};
};

if (phase === 'prepare') {
  if (fs.existsSync(OUT)) throw new Error('Output directory already exists; preserve previous evidence.');
  const full = [], compact = [];
  for (const c of cases) {
    for (const [name, question] of Object.entries(originalQuestions)) {
      const text = question.instructions + '\n' + JSON.stringify(c.state);
      const cats = Object.values(question.criteria);
      const count = (await tok.encode(buildPrefix(cats) + text)).getIds().length;
      let rejected = false;
      try { await buildInputs(text, cats, tok); }
      catch (error) {
        if (!String(error).includes('the router allows at most 128')) throw error;
        rejected = true;
      }
      full.push({case_id: c.case_id, question: name, tokens: count, rejected});
    }
    for (const [name, question] of Object.entries(config.questions)) {
      const feed = await buildInputs(stateText(c.state), question.cats, tok);
      compact.push({case_id: c.case_id, question: name, tokens: feed.count});
    }
  }
  fs.mkdirSync(OUT, {recursive: true});
  const assets = read(path.join(ASSETS, 'manifesto.json'));
  for (const [name, metadata] of Object.entries(assets.files)) {
    if (digest(fs.readFileSync(path.join(ASSETS, name))) !== metadata.sha256) throw new Error('Asset hash mismatch');
  }
  const manifest = {
    prepared_at: new Date().toISOString(), script_sha256: scriptHash, config_sha256: configHash,
    cases_sha256: caseHash, config, assets,
    code_revision: execFileSync('git', ['rev-parse', 'HEAD'], {cwd: path.join(ROOT, 'router-publico'), encoding: 'utf8'}).trim(),
    node: process.version, platform: process.platform, arch: process.arch,
    cpu: os.cpus()[0].model, logical_cpus: os.cpus().length, total_ram_bytes: os.totalmem(),
    tokenizers: read(path.join(ROOT, 'router-publico/node_modules/tokenizers/package.json')).version,
    baseline_note: 'Full Jev instructions, state and criteria tested against the public buildInputs; unsupported payloads are not inference errors or accuracy results.',
  };
  save(path.join(OUT, 'manifesto.json'), manifest);
  save(path.join(OUT, 'preflight.json'), {full, compact});
  console.log(JSON.stringify({full_payload_tokens: summaryStats(full.map(x => x.tokens)), full_rejected: full.filter(x => x.rejected).length, compact_tokens: summaryStats(compact.map(x => x.tokens))}, null, 2));
} else {
  const manifest = read(path.join(OUT, 'manifesto.json'));
  if (manifest.script_sha256 !== scriptHash || manifest.config_sha256 !== configHash || manifest.cases_sha256 !== caseHash) throw new Error('Frozen inputs or runner changed.');
  const output = path.join(OUT, `${phase}.jsonl`);
  if (fs.existsSync(output)) throw new Error('Phase already started. Do not overwrite evidence.');
  if (phase === 'evaluation' && !fs.existsSync(path.join(OUT, 'development-summary.json'))) throw new Error('Complete development first.');
  const initStart = performance.now();
  const model = await Lfm2Router.fromFile({
    modelPath: path.join(ASSETS, config.model), configPath: path.join(ASSETS, 'config.json'),
    numThreads: config.threads, executionProviders: config.executionProviders,
  });
  const initMs = performance.now() - initStart;
  const coldStart = performance.now();
  const smoke = await route({model, tok, text: 'Set a timer.', cats: ['Simple tool use', 'Creative writing']});
  const coldMs = performance.now() - coldStart;
  if (smoke.topIndex !== 0) throw new Error('Upstream sanity check failed');
  const records = [];
  for (const c of cases.filter(c => c.split === phase)) {
    const outputs = {}, timings = {};
    let firstStart;
    for (const [name, question] of Object.entries(config.questions)) {
      const text = stateText(c.state);
      const request = {text, cats: question.cats};
      const start = performance.now();
      firstStart ??= start;
      const result = await route({model, tok, ...request});
      timings[name] = performance.now() - start;
      if (result.probs.length !== question.labels.length || result.probs.some(p => !Number.isFinite(p) || p < 0 || p > 1) || Math.abs(result.probs.reduce((a,b) => a+b,0)-1) > 1e-6) throw new Error('Invalid probability output');
      outputs[name] = {request, request_sha256: digest(JSON.stringify(request)), ...result, predicted: question.labels[result.topIndex]};
    }
    const durationMs = performance.now() - firstStart;
    const correctness = Object.fromEntries(Object.entries(outputs).map(([name, value]) => [name, value.predicted === c.expected_by_policy[name]]));
    const record = {case_id: c.case_id, split: c.split, at: new Date().toISOString(), outputs, timings_ms: timings, duration_ms: durationMs, expected_by_policy: c.expected_by_policy, correct: correctness, both_correct: Object.values(correctness).every(Boolean), rss_bytes: process.memoryUsage().rss};
    fs.appendFileSync(output, JSON.stringify(record) + '\n');
    records.push(record);
    if (records.length % 10 === 0) console.log(`${phase}: ${records.length}/60, both correct ${records.filter(r => r.both_correct).length}`);
  }
  const summary = {
    phase, completed_at: new Date().toISOString(), n: records.length,
    correct: Object.fromEntries(Object.keys(config.questions).map(q => [q, records.filter(r => r.correct[q]).length])),
    both_correct: records.filter(r => r.both_correct).length,
    human_review_predictions: Object.fromEntries(Object.keys(config.questions).map(q => [q, records.filter(r => r.outputs[q].predicted === 'human_review').length])),
    opportunity_duration_ms: summaryStats(records.map(r => r.duration_ms)),
    route_duration_ms: summaryStats(records.flatMap(r => Object.values(r.timings_ms))),
    init_ms: initMs, cold_smoke_ms: coldMs, smoke, peak_observed_rss_bytes: Math.max(...records.map(r => r.rss_bytes)),
    frozen: {script_sha256: scriptHash, config_sha256: configHash, cases_sha256: caseHash},
  };
  save(path.join(OUT, `${phase}-summary.json`), summary);
  console.log(JSON.stringify(summary, null, 2));
}
