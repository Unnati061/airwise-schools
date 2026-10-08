import { useState } from 'react';
import { ArrowRight, Check, Plus } from 'lucide-react';
import { api, type Actor, type Schema } from './client';
import type { AdminData } from './App';
import { ActionNotice, Empty, Heading, Metrics, Mode, Refresh, ResourceState, short, stamp, useAction, useResource, Version } from './ui';

export function changeExplanation(plan: Schema<'DraftPlan'>, difference: Schema<'Difference'>) {
  const activity = plan.input_snapshot.activities.find(a => a.id === difference.activity_id)!;
  const proposed = difference.proposed;
  if (proposed.deferred) return 'Explicitly permitted deferral; activity remains accounted for.';
  const alternative = (activity.approved_alternatives ?? []).find(a => a.id === proposed.alternative_id);
  const facts = [];
  if (alternative) facts.push(`Approved substitution: ${alternative.label}`);
  if (difference.original.period_id !== proposed.period_id) facts.push(`Period ${difference.original.period_id} to ${proposed.period_id}`);
  if (difference.original.room_id !== proposed.room_id) facts.push(`Room ${difference.original.room_id} to ${proposed.room_id}`);
  if (difference.original.period_id === proposed.period_id) facts.push('Original period retained');
  return facts.join('. ') + '.';
}

export function Comparison({ plan }: { plan: Schema<'DraftPlan'> }) {
  const [section, setSection] = useState('all');
  const [changesOnly, setChangesOnly] = useState(false);
  const periods = new Map(plan.input_snapshot.periods.map(p => [p.id, p]));
  const placements = new Map(plan.placements.map(p => [p.activity_id, p]));
  const differences = new Map((plan.differences ?? []).map(d => [d.activity_id, d]));
  const activities = plan.input_snapshot.activities.filter(a => periods.get(a.original_period_id)?.day === plan.input_snapshot.affected_day && (section === 'all' || a.section_id === section) && (!changesOnly || differences.has(a.id))).sort((a, b) => periods.get(a.original_period_id)!.number - periods.get(b.original_period_id)!.number || a.section_id.localeCompare(b.section_id));
  return <section><div className="section-heading"><h2>Original / proposed timetable</h2><div className="toolbar"><label className="inline-field">Section<select value={section} onChange={e => setSection(e.target.value)}><option value="all">All sections</option>{plan.input_snapshot.sections.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label><label className="check-label"><input type="checkbox" checked={changesOnly} onChange={e => setChangesOnly(e.target.checked)} />Changed activities only</label></div></div><p className="muted">Affected day: {plan.input_snapshot.affected_day}. Other weekdays remain unchanged.</p>{activities.length ? <div className="table-scroll"><table className="comparison-table"><thead><tr><th>Section / activity</th><th>Original</th><th>Proposed</th><th>Change / reason</th></tr></thead><tbody>{activities.map(activity => {
    const placement = placements.get(activity.id), difference = differences.get(activity.id);
    const label = (activity.approved_alternatives ?? []).find(a => a.id === placement?.alternative_id)?.label ?? activity.label;
    return <tr key={activity.id} className={difference ? 'changed-row' : ''}><td><strong>{activity.section_id} · {activity.label}</strong><small>{activity.id}{activity.fixed ? ' · Fixed lesson' : ''}</small></td><td>{activity.original_period_id}<small>{activity.original_room_id}</small></td><td>{placement ? placement.deferred ? 'Deferred' : placement.period_id : 'No placement returned'}<small>{placement?.room_id || 'No room'} · {label}</small></td><td>{difference ? <><span className="badge">Changed</span><p>{changeExplanation(plan, difference)}</p></> : <span>Unchanged</span>}</td></tr>;
  })}</tbody></table></div> : <Empty>No changed activities match this section.</Empty>}</section>;
}

export default function Plan({ actor, data, reload, refreshing }: { actor: Actor; data: AdminData; reload: () => void; refreshing: boolean }) {
  const storageKey = `airwise.draft.${actor.sub}`;
  const [planId, setPlanId] = useState(() => sessionStorage.getItem(storageKey) || data.current.plan_version || '');
  const [generated, setGenerated] = useState<Schema<'DraftPlan'> | null>(null);
  const [approvedHere, setApprovedHere] = useState('');
  const action = useAction();
  const loaded = useResource(async () => {
    if (!planId) return null;
    const plan = await api<Schema<'DraftPlan'>>(`/draft-plans/${planId}`);
    const input = plan.input_versions.timetable === data.confirmed.revision ? data.confirmed : await api<Schema<'ConfirmedInput'>>(`/inputs/${plan.input_versions.timetable}`);
    return { plan, input };
  }, [planId, data.confirmed.revision]);
  const plan = generated?.id === planId ? generated : loaded.value?.plan;
  const source = plan?.input_versions.timetable === data.confirmed.revision ? data.confirmed.evidence_binding : loaded.value?.input.evidence_binding;
  const sourceMode = plan && (plan.input_versions.timetable === data.confirmed.revision || loaded.value?.plan.id === plan.id) ? source?.mode || 'MANUAL' : 'UNKNOWN';
  const stale = plan && plan.input_versions.timetable !== data.confirmed.revision;
  const approved = plan && (approvedHere === plan.id || data.history.some(p => p.plan_version === plan.id));
  function generate() {
    if (refreshing) return;
    void action.run(async () => {
      const latest = await api<Schema<'ConfirmedInput'>>('/inputs');
      return api<Schema<'DraftPlan'>>('/draft-plans', 'POST', latest.input);
    }, result => { setGenerated(result); setPlanId(result.id); sessionStorage.setItem(storageKey, result.id); reload(); }, 'Draft generated; approval is still required.');
  }
  function approve() {
    if (!plan) return;
    void action.run(() => api<Schema<'ApprovedPlan'>>(`/draft-plans/${plan.id}/approve`, 'POST'), result => { setApprovedHere(result.plan_version); reload(); }, 'Approval recorded for this version.');
  }
  return <><Heading title="Plan comparison"><Refresh onClick={() => { loaded.reload(); reload(); }} disabled={action.busy || refreshing} /><button className="primary" onClick={generate} disabled={action.busy || refreshing}><Plus size={17} />Generate draft</button></Heading><p className="lead">A validated draft does not replace the approved timetable until administrator approval.</p>{data.current.needs_review && <div className="notice warning"><strong>Approved plan needs review</strong><p>A confirmed input revision changed. The previous approved version remains in effect until a new approval.</p></div>}
    <div className="section-heading"><div><span className="muted">Current approved version</span><p>{data.current.plan_version ? <Version value={data.current.plan_version} /> : 'None'}</p></div>{data.history.length > 0 && <label className="inline-field">Inspect approved version<select aria-label="Inspect approved version" value={data.history.some(p => p.plan_version === planId) ? planId : ''} onChange={e => { if (e.target.value) { setGenerated(null); setPlanId(e.target.value); sessionStorage.setItem(storageKey, e.target.value); } }}><option value="">Selected draft</option>{data.history.map(p => <option value={p.plan_version} key={p.plan_version}>{short(p.plan_version)} · {p.current ? 'Current' : 'Previous'} · {stamp(p.timestamp)}</option>)}</select></label>}</div>
    <ActionNotice action={action} /><ResourceState resource={loaded} />{!planId && <Empty>No draft selected. Current confirmed inputs are ready for draft generation.</Empty>}
    {plan && <>
      <div className="plan-status"><div><span className="eyebrow">{approved ? 'Approved version' : 'Draft version'}</span><Version value={plan.id} /></div><div className="status-labels"><span className="badge">Solver: {plan.solver_status}</span><span className={`badge ${plan.validation?.valid ? 'good' : 'bad'}`}>Independent validation: {plan.validation?.valid ? 'Passed' : 'Not passed'}</span><Mode mode={sourceMode} /></div></div>
      <p><strong>Recommendation:</strong> {plan.recommendation === 'baseline' ? 'Keep original periods using the approved classroom alternatives (baseline).' : plan.recommendation === 'repair' ? 'Use the validated repair.' : 'No successful permitted plan.'}</p>
      <p className="muted">Baseline validation: {plan.baseline.validation.valid ? 'Passed' : 'Not passed'}. {plan.solver_status === 'UNKNOWN' ? 'Time limit or unknown status is not proven infeasibility.' : ''}</p>
      {plan.diagnostic && <div className="notice warning">{plan.diagnostic}</div>}
      {plan.validation && !plan.validation.valid && <div className="notice danger"><ul>{plan.validation.errors.map((e, i) => <li key={i}>{e}</li>)}</ul></div>}
      <Metrics counts={plan.counts} />{stale && <div className="notice warning" role="alert">This draft uses an older input/restriction revision. Approval is disabled; generate a draft from the current confirmed inputs.</div>}<div className="approval-row"><div>Input revision <Version value={plan.input_versions.timetable} />{source && <small>Evidence {source.mode} · Reviewed date {source.calendar_date}</small>}</div><button className="primary" onClick={approve} disabled={action.busy || loaded.loading || !!stale || !!approved || !plan.successful || !plan.validation?.valid}><Check size={17} />{approved ? 'Approval recorded' : 'Approve this version'}</button></div><Comparison key={plan.id} plan={plan} /><a className="next-link" href="#review">Review execution and history <ArrowRight size={17} /></a>
    </>}</>;
}
