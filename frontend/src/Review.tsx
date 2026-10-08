import { useState, type FormEvent } from 'react';
import { Check, MessageSquare } from 'lucide-react';
import { api, type Schema } from './client';
import type { AdminData } from './App';
import { changeExplanation } from './Plan';
import { ActionNotice, Dialog, Empty, Heading, Metrics, Mode, Refresh, ResourceState, short, stamp, useAction, useResource, Version, words } from './ui';

export default function Review({ data, reload }: { data: AdminData; reload: () => void }) {
  const [version, setVersion] = useState('');
  const [includeResolved, setIncludeResolved] = useState(false);
  const [resolution, setResolution] = useState<{ report: Schema<'ExecutionReport'>; requestId: string } | null>(null);
  const [note, setNote] = useState('');
  const action = useAction();
  const selectedVersion = version || data.current.plan_version || data.history[0]?.plan_version;
  const resource = useResource(async () => {
    if (!selectedVersion) return null;
    const [detail, execution, audits] = await Promise.all([api<Schema<'ApprovedPlanDetail'>>(`/approved-plans/${selectedVersion}`), api<Schema<'ExecutionReview'>>(`/approved-plans/${selectedVersion}/review`), api<Schema<'AuditEvent'>[]>('/audit-events')]);
    return { detail, execution, audits };
  }, [selectedVersion]);
  const records = resource.value;
  const changes = records?.detail.plan.differences ?? [];
  const exceptions = records?.execution.reports.filter(r => r.status !== 'COMPLETED' && (includeResolved || records.execution.unresolved_activity_ids.includes(r.activity_id))) ?? [];
  function openResolution(report: Schema<'ExecutionReport'>) { setResolution({ report, requestId: crypto.randomUUID() }); setNote(''); }
  function saveResolution(event: FormEvent) {
    event.preventDefault();
    if (!resolution) return;
    const body: Schema<'ResolutionInput'> = { request_id: resolution.requestId, note };
    void action.run(() => api<Schema<'Resolution'>>(`/approved-plans/${resolution.report.plan_version}/activities/${encodeURIComponent(resolution.report.activity_id)}/resolution`, 'POST', body), () => { setResolution(null); resource.reload(); }, 'Resolution note recorded for this exception.');
  }
  return <><Heading title="Review"><Refresh onClick={() => { resource.reload(); reload(); }} disabled={action.busy} /></Heading><p className="lead">Validated planned changes, teacher-reported execution and version history.</p>{data.current.needs_review && <div className="notice warning">Current approved plan needs review. Revised inputs do not replace it automatically.</div>}<ResourceState resource={resource} />{!resolution && <ActionNotice action={action} />}
    {!selectedVersion && <Empty>No approved version is available for execution review.</Empty>}
    {selectedVersion && <div className="section-heading"><div><span className="muted">Viewing approved version</span><p><Version value={selectedVersion} /></p></div><label className="inline-field">Review version<select aria-label="Review version" value={selectedVersion} onChange={e => setVersion(e.target.value)}>{data.history.map(p => <option key={p.plan_version} value={p.plan_version}>{short(p.plan_version)} · {p.current ? 'Current' : 'Previous'} · {stamp(p.timestamp)}</option>)}</select></label></div>}
    {records && <>
      <p><Mode mode={records.detail.evidence_binding?.mode || 'MANUAL'} /> · Approved {stamp(records.detail.approval.timestamp)}</p>
      <section><h2>Planned changes</h2><Metrics counts={records.detail.plan.counts} />{changes.length ? <div className="table-scroll"><table><thead><tr><th>Activity</th><th>Validated change</th></tr></thead><tbody>{changes.map(d => <tr key={d.activity_id}><td>{d.activity_id}</td><td>{changeExplanation(records.detail.plan, d)}</td></tr>)}</tbody></table></div> : <Empty>The approved plan has no activity changes.</Empty>}</section>
      <section><h2>Teacher-reported execution</h2><dl className="metrics execution-metrics">{[['Reported activities', records.execution.counts.reported], ['Completed', records.execution.counts.completed], ['Could not implement', records.execution.counts.could_not_implement], ['Needs clarification', records.execution.counts.needs_clarification], ['Unresolved exceptions', records.execution.counts.unresolved]].map(([label, count]) => <div key={label}><dt>{label}</dt><dd>{count}</dd></div>)}</dl>{records.execution.reports.length ? <div className="table-scroll"><table><thead><tr><th>Activity / teacher</th><th>Reported execution</th><th>Note</th><th>Reported at</th></tr></thead><tbody>{records.execution.reports.map(report => <tr key={report.activity_id}><td>{report.activity_id}<small>{report.teacher_id}</small></td><td>{words(report.status)}</td><td>{report.note || 'No note'}</td><td>{stamp(report.timestamp)}</td></tr>)}</tbody></table></div> : <Empty>No execution reports for this version. Acknowledgements are not counted as execution.</Empty>}</section>
      <section><div className="section-heading"><h2>Execution exceptions</h2><label className="check-label"><input type="checkbox" checked={includeResolved} onChange={e => setIncludeResolved(e.target.checked)} />Include resolved exceptions</label></div>{exceptions.length ? <div className="table-scroll"><table><thead><tr><th>Activity / status</th><th>Exception and resolution notes</th><th>Review state</th><th>Action</th></tr></thead><tbody>{exceptions.map(report => { const unresolved = records.execution.unresolved_activity_ids.includes(report.activity_id); return <tr key={report.activity_id}><td>{report.activity_id}<small>{words(report.status)}</small></td><td><p>{report.note || 'No teacher note'}</p>{records.execution.resolutions.filter(n => n.activity_id === report.activity_id).map(n => <p key={n.request_id}><strong>Resolution:</strong> {n.note}<small>{stamp(n.timestamp)}</small></p>)}</td><td><span className="badge">{unresolved ? 'Unresolved' : 'Resolution recorded'}</span></td><td><button className="secondary" disabled={action.busy} onClick={() => openResolution(report)}><MessageSquare size={16} />Record note</button></td></tr>; })}</tbody></table></div> : <Empty>No unresolved execution exceptions for this version.</Empty>}</section>
      <section><h2>Approval history</h2><div className="table-scroll"><table><thead><tr><th>Version</th><th>Approved at</th><th>Current state</th></tr></thead><tbody>{data.history.map(p => <tr key={p.plan_version}><td><button className="text-link" onClick={() => setVersion(p.plan_version)}>{p.plan_version}</button></td><td>{stamp(p.timestamp)}</td><td>{p.current ? p.needs_review ? 'Current — needs review' : 'Current approved' : 'Previous version'}</td></tr>)}</tbody></table></div></section>
      <section><h2>Audit history</h2><div className="table-scroll"><table><thead><tr><th>Time</th><th>Action</th><th>Actor</th><th>Activity / version</th></tr></thead><tbody>{[...records.audits].sort((a, b) => b.timestamp.localeCompare(a.timestamp)).map(event => <tr key={event.event_id}><td>{stamp(event.timestamp)}</td><td>{words(event.action)}</td><td title={event.actor}>Actor {short(event.actor)}</td><td>{event.activity_id || 'Whole plan / input'}<small>{event.plan_version || 'No plan version'}</small></td></tr>)}</tbody></table></div></section>
      {resolution && <Dialog title="Resolution note" close={() => setResolution(null)} busy={action.busy}><p>{resolution.report.activity_id} · {words(resolution.report.status)}</p><p>Plan version <Version value={resolution.report.plan_version} /></p><form onSubmit={saveResolution}><label>Administrator resolution note<textarea required rows={4} maxLength={1000} value={note} onChange={e => setNote(e.target.value)} /></label><ActionNotice action={action} /><button className="primary" disabled={!note.trim() || action.busy}><Check size={16} />Record resolution</button></form></Dialog>}
    </>}
  </>;
}
