/* Real deployed API check. Credentials stay in the privately operated browser. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const API = 'https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com';
let stage = 'startup';
const results = [];
const workflowOnly = process.env.AIRWISE_WORKFLOW_ONLY === '1';
(async () => {
  // A single readiness request must succeed before opening the private browser.
  const ready = await fetch('http://127.0.0.1:5173/', { signal: AbortSignal.timeout(10000) });
  if (!ready.ok) throw new Error('Frontend is not ready');
  const browser = await chromium.launch({ headless: false, channel: 'chrome', args: ['--start-maximized'] });
  const page = await browser.newPage({ viewport: null });
  page.setDefaultTimeout(90000);
  // Retain an ID token only in browser memory for the negative token-use check.
  if (!workflowOnly) await page.addInitScript(() => {
    const original = window.fetch;
    window.fetch = async (...args) => {
      const response = await original(...args);
      if (String(args[0]).startsWith('https://cognito-idp.')) {
        const data = await response.clone().json().catch(() => null);
        window.__d2IDToken = data?.AuthenticationResult?.IdToken || null;
      }
      return response;
    };
  });
  const login = async role => {
    stage = `${role} private sign-in`;
    console.log(`WAIT: privately sign in as ${role} in Chrome`);
    await page.getByRole('link', { name: role === 'administrator' ? 'Evidence & restrictions' : 'Teacher inbox', exact: true }).waitFor({ timeout: 900000 });
    console.log(`PASS: real ${role} Cognito sign-in`);
  };
  const check = async (name, action, argument) => {
    stage = name;
    const result = await page.evaluate(action, argument);
    results.push({ check: name, ...result });
    console.log('PASS: ' + JSON.stringify(results.at(-1)));
  };
  try {
    stage = 'local frontend navigation';
    await page.goto('http://127.0.0.1:5173');
    await login('administrator');
    await check(workflowOnly ? 'administrator access' : 'administrator and ID-token rejection', async config => {
      const { api, workflowOnly } = config;
      const client = await import('/src/client.ts');
      window.__d2Timings = [];
      window.__d2Call = async (p, method = 'GET', body, expected = 200) => {
        const start = performance.now();
        try {
          const value = await client.api(p, method, body);
          window.__d2Timings.push({ path: p, status: 200, duration_ms: Math.round(performance.now() - start) });
          if (expected !== 200) throw new Error('Expected denial did not occur');
          return value;
        } catch (e) {
          if (expected === 200 || e.status !== expected) window.__d2Failure = { path: p, status: e.status ?? null, error_type: e.name, duration_ms: Math.round(performance.now() - start) };
          if (!e.status || e.status !== expected) throw e;
          window.__d2Timings.push({ path: p, status: e.status, duration_ms: Math.round(performance.now() - start) });
          return null;
        }
      };
      const actor = await window.__d2Call('/me');
      if (actor.role !== 'administrator') throw new Error('Administrator required');
      if (workflowOnly) return { role: actor.role, id_token_status: 'not rerun in workflow-only mode' };
      if (!window.__d2IDToken) throw new Error('No ID token available for negative check');
      const response = await fetch(api + '/me', { headers: { Authorization: 'Bearer ' + window.__d2IDToken } });
      window.__d2IDToken = null;
      if (response.status !== 403) throw new Error('ID-token rejection failed');
      return { role: actor.role, id_token_status: response.status };
    }, { api: API, workflowOnly });
    if (workflowOnly) {
      await check('existing confirmed input', async () => {
        window.__d2 = { confirmed: await window.__d2Call('/inputs') };
        return { input_revision: window.__d2.confirmed.revision, evidence_mode: window.__d2.confirmed.evidence_binding?.mode || 'MANUAL' };
      });
    } else {
    await check('live regional forecast', async () => {
      const live = await window.__d2Call('/evidence/forecast?mode=LIVE');
      if (live.snapshot.mode !== 'LIVE' || live.freshness !== 'FRESH' || live.observations_available !== false) throw new Error('Live provenance/freshness mismatch');
      return { source: live.snapshot.source, retrieved_at: live.snapshot.retrieved_at,
        model_issue_time: live.snapshot.model_issue_time, freshness: live.freshness,
        observations_available: live.observations_available, points: live.snapshot.points.length };
    });
    await check('draft before revision', async () => {
      const input = await window.__d2Call('/inputs');
      window.__d2 = { oldCurrent: await window.__d2Call('/current-plan') };
      window.__d2.stale = await window.__d2Call('/draft-plans', 'POST', input.input);
      if (!window.__d2.stale.successful || !window.__d2.stale.validation?.valid) throw new Error('Initial draft invalid');
      return { draft_id: window.__d2.stale.id, solver_status: window.__d2.stale.solver_status };
    });
    await check('one bounded Nova interpretation', async () => {
      const replay = await window.__d2Call('/evidence/forecast?mode=REPLAY');
      if (replay.snapshot.mode !== 'REPLAY') throw new Error('Replay mode mismatch');
      const result = await window.__d2Call('/notice-analyses', 'POST', {
        notice: 'SYNTHETIC UNVERIFIED D2 DEPLOYMENT CHECK: On 2026-10-12, restrict outdoor PE for section 6A in Monday period 2; use its explicitly approved indoor classroom alternative. Administrator review is required. This is not a legal closure or GRAP activation order.',
        evidence_id: replay.snapshot.id, mode: 'REPLAY', policy_ids: ['ncdc-2025-school-5ii'],
      });
      window.__d2.analysis = result;
      if (result.status !== 'SUCCESS' || !result.interpretation || !result.requires_review) throw new Error('Interpretation unsuccessful: ' + result.status);
      return { analysis_id: result.id, status: result.status, model: result.model, region: result.region, mode: result.mode, usage: result.usage, requires_review: result.requires_review };
    });
    await check('administrator review, revision and stale approval', async () => {
      const d = window.__d2;
      const proposals = d.analysis.interpretation.proposed_restrictions.filter(p => p.kind === 'outdoor_prohibited' && p.activity_ids.includes('6-a:Mon-2') && p.citation_ids.length);
      if (!proposals.length) throw new Error('No supported proposal for reviewed activity');
      d.confirmed = await window.__d2Call('/notice-analyses/' + d.analysis.id + '/confirm', 'POST', {
        expected_revision: d.analysis.input_revision, proposal_ids: [proposals[0].id], calendar_date: '2026-10-12',
        period_ids: ['Mon-2'], notice_reviewed: true, ambiguities_reviewed: true,
      });
      const current = await window.__d2Call('/current-plan');
      if (current.plan_version !== d.oldCurrent.plan_version || !current.needs_review) throw new Error('Revision replaced approved pointer');
      await window.__d2Call('/draft-plans/' + d.stale.id + '/approve', 'POST', undefined, 409);
      return { input_revision: d.confirmed.revision, evidence_mode: d.confirmed.evidence_binding.mode, stale_approval_status: 409, old_approved_pointer_preserved: true };
    });
    }
    await check('repair, independent validation, approval and persistence', async () => {
      const d = window.__d2;
      d.plan = await window.__d2Call('/draft-plans', 'POST', d.confirmed.input);
      if (!d.plan.successful || !d.plan.validation?.valid || d.plan.placements.length !== 240) throw new Error('Repair invalid or dropped activities');
      d.approved = await window.__d2Call('/draft-plans/' + d.plan.id + '/approve', 'POST');
      const duplicate = await window.__d2Call('/draft-plans/' + d.plan.id + '/approve', 'POST');
      const current = await window.__d2Call('/current-plan');
      const stored = await window.__d2Call('/approved-plans/' + d.approved.plan_version);
      if (duplicate.plan_version !== d.approved.plan_version || current.plan_version !== d.approved.plan_version || current.needs_review || !stored.plan.validation.valid) throw new Error('Approval persistence mismatch');
      return { plan_version: d.approved.plan_version, solver_status: d.plan.solver_status, independently_valid: true,
        recommendation: d.plan.recommendation, counts: d.plan.counts, activities: d.plan.placements.length,
        differences: d.plan.differences, duplicate_approval_consistent: true };
    });
    const version = await page.evaluate(() => window.__d2.approved.plan_version);
    await page.getByRole('button', { name: 'Sign out' }).click();
    await login('teacher');
    await check('teacher and permission denials', async version => {
      const actor = await window.__d2Call('/me');
      if (actor.role !== 'teacher' || actor.teacher_id !== 'teacher-6-a') throw new Error('Wrong teacher identity');
      await window.__d2Call('/draft-plans/' + version + '/approve', 'POST', undefined, 403);
      await window.__d2Call('/teachers/teacher-6-b/assignments', 'GET', undefined, 403);
      const assignments = await window.__d2Call('/teachers/teacher-6-a/assignments');
      const expectedMode = window.__d2.confirmed.evidence_binding?.mode || 'MANUAL';
      if (assignments.plan_version !== version || assignments.acknowledged || assignments.evidence_mode !== expectedMode) throw new Error('Teacher version/acknowledgement mismatch');
      await window.__d2Call('/inputs', 'GET', undefined, 403);
      await window.__d2Call('/audit-events', 'GET', undefined, 403);
      return { teacher_id: actor.teacher_id, assignments: assignments.assignments.length, approval_status: 403, other_teacher_status: 403, acknowledged_before_action: false };
    }, version);
    await check('separate acknowledgement and idempotent execution report', async version => {
      await window.__d2Call('/approved-plans/' + version + '/acknowledgements', 'POST');
      const empty = await window.__d2Call('/teachers/teacher-6-a/reports?version=' + version);
      if (empty.length) throw new Error('Acknowledgement created execution');
      const p = '/approved-plans/' + version + '/activities/6-a:Mon-2/report';
      const report = { status: 'COULD_NOT_IMPLEMENT', note: 'SYNTHETIC D2 CHECK: classroom unavailable' };
      const first = await window.__d2Call(p, 'PUT', report);
      const repeated = await window.__d2Call(p, 'PUT', report);
      const records = await window.__d2Call('/teachers/teacher-6-a/reports?version=' + version);
      if (records.length !== 1 || first.timestamp !== repeated.timestamp) throw new Error('Repeated report duplicated execution');
      return { plan_version: version, acknowledged_without_execution: true, execution_status: first.status, repeated_report_total: records.length };
    }, version);
    await page.getByRole('button', { name: 'Sign out' }).click();
    await login('administrator');
    await check('administrator review and version history', async version => {
      const review = await window.__d2Call('/approved-plans/' + version + '/review');
      const history = await window.__d2Call('/approved-plans');
      const audits = await window.__d2Call('/audit-events');
      if (review.counts.reported !== 1 || review.counts.unresolved !== 1 || !history.some(p => p.current && p.plan_version === version) || history.length < 2 || !audits.some(e => e.action === 'EXECUTION_COULD_NOT_IMPLEMENT' && e.plan_version === version)) throw new Error('Review/history mismatch');
      return { counts: review.counts, approved_versions: history.length, audit_events: audits.length, current_plan_version: version };
    }, version);
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByText('SYNTHETIC D2 CHECK: classroom unavailable', { exact: true }).first().waitFor();
    console.log('PASS: deployed administrator Review UI displays the execution exception');
  } catch (error) {
    const navigationCode = stage === 'local frontend navigation' ? error.message.match(/net::ERR_[A-Z_]+/)?.[0] || null : null;
    results.push({ failure_stage: stage, error_type: error.name, http_status: error.status || null, navigation_code: navigationCode });
    console.error(`FAIL: ${stage}; ${error.name}; status ${error.status || 'unknown'}; private contents withheld`);
    process.exitCode = 1;
  } finally {
    const timings = await page.evaluate(() => window.__d2Timings || []).catch(() => []);
    const failedRequest = await page.evaluate(() => window.__d2Failure || null).catch(() => null);
    fs.writeFileSync(path.join(__dirname, '../work/d2-verification.json'), JSON.stringify({ workflow_only: workflowOnly, results, timings, failed_request: failedRequest }, null, 2));
    console.log('Safe results recorded in work/d2-verification.json');
    await browser.close();
  }
})().catch(e => { console.error('FAIL startup: ' + e.name); process.exitCode = 1; });
