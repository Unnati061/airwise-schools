import { useState, type FormEvent } from 'react';
import { Check, ClipboardPen } from 'lucide-react';
import { api, type Actor, type Schema } from './client';
import { ActionNotice, Dialog, Empty, Heading, Mode, Refresh, ResourceState, short, stamp, useAction, useResource, Version, words } from './ui';

export default function TeacherInbox({ actor }: { actor: Actor }) {
  const [version, setVersion] = useState('');
  const [day, setDay] = useState('Mon');
  const [selected, setSelected] = useState<Schema<'Assignment'> | null>(null);
  const [status, setStatus] = useState<Schema<'ExecutionInput'>['status'] | ''>('');
  const [note, setNote] = useState('');
  const acknowledgement = useAction(), reporting = useAction();
  const resource = useResource(async () => {
    const history = await api<Schema<'PlanVersionSummary'>[]>('/approved-plans');
    const current = history.find(p => p.current);
    const chosen = version || current?.plan_version;
    if (!chosen) return { history, current, assignments: null, reports: [] as Schema<'ExecutionReport'>[] };
    const teacher = encodeURIComponent(actor.teacher_id!);
    const [assignments, reports] = await Promise.all([api<Schema<'TeacherAssignments'>>(`/teachers/${teacher}/assignments?version=${encodeURIComponent(chosen)}`), api<Schema<'ExecutionReport'>[]>(`/teachers/${teacher}/reports?version=${encodeURIComponent(chosen)}`)]);
    return { history, current, assignments, reports };
  }, [version, actor.teacher_id]);
  const data = resource.value;
  const assignments = data?.assignments;
  const historic = assignments && assignments.plan_version !== data?.current?.plan_version;
  const days = [...new Set((assignments?.assignments.map(a => a.placement.period_id?.split('-')[0]).filter(Boolean) ?? []) as string[])];
  const selectedDay = days.includes(day) ? day : days[0];
  const rows = assignments?.assignments.filter(a => a.placement.deferred || a.placement.period_id?.startsWith(`${selectedDay}-`)).sort((a, b) => (a.placement.period_id || '').localeCompare(b.placement.period_id || '') || a.activity_id.localeCompare(b.activity_id)) ?? [];
  function acknowledge() {
    if (!assignments) return;
    void acknowledgement.run(() => api<Schema<'Acknowledgement'>>(`/approved-plans/${assignments.plan_version}/acknowledgements`, 'POST'), resource.reload, 'Acknowledgement recorded. It does not report execution.');
  }
  function openReport(assignment: Schema<'Assignment'>) {
    const previous = data?.reports.find(r => r.activity_id === assignment.activity_id);
    setSelected(assignment); setStatus(previous?.status || ''); setNote(previous?.note || '');
  }
  function report(event: FormEvent) {
    event.preventDefault();
    if (!selected || !assignments || !status) return;
    const body: Schema<'ExecutionInput'> = { status, note };
    void reporting.run(() => api<Schema<'ExecutionReport'>>(`/approved-plans/${assignments.plan_version}/activities/${encodeURIComponent(selected.activity_id)}/report`, 'PUT', body), () => { setSelected(null); resource.reload(); }, 'Execution report saved for this activity and plan version.');
  }
  return <><Heading title="Teacher inbox"><Refresh onClick={resource.reload} disabled={acknowledgement.busy || reporting.busy} /></Heading><p className="lead">Your approved assignments · {actor.teacher_id}</p><ResourceState resource={resource} /><ActionNotice action={acknowledgement} />{!selected && <ActionNotice action={reporting} />}
    {data && !assignments && <Empty>No approved assignments are available yet.</Empty>}
    {data && assignments && <><div className="section-heading"><div><span className="muted">Current approved version</span><p><Version value={data.current?.plan_version || assignments.plan_version} /></p></div><label className="inline-field">Plan version<select aria-label="Teacher plan version" value={assignments.plan_version} onChange={e => setVersion(e.target.value)}>{data.history.map(p => <option key={p.plan_version} value={p.plan_version}>{short(p.plan_version)} · {p.current ? 'Current' : 'Previous'} · {stamp(p.timestamp)}</option>)}</select></label></div>
      {data.current?.needs_review && <div className="notice warning"><strong>Current approved plan needs review</strong><p>The administrator has revised inputs. The approved version remains on record until a new approval.</p></div>}
      {historic && <div className="notice neutral"><strong>Archived version — read only</strong><p>Viewing <Version value={assignments.plan_version} />. Previous acknowledgement and reports are retained; they do not transfer to a new version.</p></div>}
      <div className="approval-row"><div><Mode mode={assignments.evidence_mode} /><p>Acknowledgement: <strong>{assignments.acknowledged ? 'Recorded for this version' : 'Not recorded'}</strong></p></div><button className="primary" disabled={!!historic || assignments.acknowledged || acknowledgement.busy || resource.loading} onClick={acknowledge}><Check size={17} />{assignments.acknowledged ? 'Acknowledged' : 'Acknowledge this version'}</button></div>
      <section><div className="section-heading"><h2>Assignments</h2><label className="inline-field">Weekday<select value={selectedDay || ''} onChange={e => setDay(e.target.value)}>{days.map(d => <option key={d}>{d}</option>)}</select></label></div>{rows.length ? <div className="table-scroll"><table><thead><tr><th>Period / section</th><th>Approved activity</th><th>Execution report</th><th>Action</th></tr></thead><tbody>{rows.map(assignment => { const report = data.reports.find(r => r.activity_id === assignment.activity_id); return <tr key={assignment.activity_id} data-activity={assignment.activity_id}><td>{assignment.placement.period_id || 'Deferred'}<small>{assignment.section_id}</small></td><td><strong>{assignment.proposed_label}</strong><small>{assignment.placement.room_id || 'No room'} · {assignment.activity_id}</small></td><td>{report ? <><span className="badge">{words(report.status)}</span><p>{report.note || 'No note'}</p><small>{stamp(report.timestamp)}</small></> : 'Not reported'}</td><td><button className="secondary" aria-label={`Report ${assignment.activity_id}`} disabled={!!historic || reporting.busy} onClick={() => openReport(assignment)}><ClipboardPen size={16} />Report</button></td></tr>; })}</tbody></table></div> : <Empty>No assignments for this weekday.</Empty>}</section>
      {selected && <Dialog title="Execution report" close={() => setSelected(null)} busy={reporting.busy}><p><strong>{selected.proposed_label}</strong> · {selected.placement.period_id || 'Deferred'}</p><p>{selected.activity_id}</p><p>Plan version <Version value={assignments.plan_version} /></p><form onSubmit={report}><label>Execution status<select required value={status} onChange={e => setStatus(e.target.value as typeof status)}><option value="">Select status</option><option value="COMPLETED" disabled={selected.placement.deferred}>Completed</option><option value="COULD_NOT_IMPLEMENT">Could not implement</option><option value="NEEDS_CLARIFICATION">Needs clarification</option></select></label><label>Note (optional)<textarea rows={4} maxLength={1000} value={note} onChange={e => setNote(e.target.value)} /></label><ActionNotice action={reporting} /><button className="primary" disabled={!status || reporting.busy || !!historic}><Check size={16} />Save execution report</button></form></Dialog>}
    </>}
  </>;
}
