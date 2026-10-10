import { ArrowRight, CheckCircle2, CircleAlert, ClipboardCheck } from 'lucide-react';
import { api, type Actor, type Schema } from './client';
import type { AdminData } from './App';
import { Comparison } from './Plan';
import { Empty, Metrics, ResourceState, useResource, words } from './ui';
import type { ForecastResource } from './Today';

export default function OperationsOverview({ actor, data, forecast }: { actor: Actor; data: AdminData; forecast: ForecastResource }) {
  const version = data.current.plan_version;
  const selectedDraft = sessionStorage.getItem(`airwise.draft.${actor.sub}`);
  const resource = useResource(async () => {
    const draft = selectedDraft && selectedDraft !== version ? await api<Schema<'DraftPlan'>>(`/draft-plans/${selectedDraft}`) : null;
    if (!version) return { draft, detail: null, execution: null };
    const [detail, execution] = await Promise.all([
      api<Schema<'ApprovedPlanDetail'>>(`/approved-plans/${version}`),
      api<Schema<'ExecutionReview'>>(`/approved-plans/${version}/review`),
    ]);
    return { draft, detail, execution };
  }, [version, selectedDraft, data.confirmed.revision]);
  const records = resource.value;
  const draft = records?.draft;
  const draftCurrent = draft?.input_versions.timetable === data.confirmed.revision;
  const plan = draft || records?.detail?.plan;
  const execution = records?.execution;
  const unresolved = execution?.reports.filter(r => execution.unresolved_activity_ids.includes(r.activity_id)) ?? [];
  const staleEvidence = forecast.value && !['FRESH', 'REPLAY'].includes(forecast.value.freshness);
  const evidenceState = forecast.error ? 'Forecast unavailable' : staleEvidence ? 'Evidence needs refresh' : forecast.loading ? 'Checking regional evidence' : forecast.value?.snapshot.mode === 'REPLAY' ? 'Replay scenario selected' : 'Regional forecast available';
  const actionState = data.current.needs_review ? 'Review revised inputs' : draft ? draftCurrent && draft.successful && draft.validation?.valid ? 'A draft is ready for your decision' : 'Selected draft needs review' : version ? 'Approved timetable remains in effect' : 'Generate a first draft';
  return <>
    <section className="attention-band" aria-label="School day attention">
      <div><span className="eyebrow">Evidence needing attention</span><strong><CircleAlert size={17} />{evidenceState}</strong><p>{forecast.value?.snapshot.mode === 'REPLAY' ? 'Invented values; not current conditions.' : 'No campus station observations. Review the source before changing restrictions.'}</p><a href="#evidence">Review evidence <ArrowRight size={15} /></a></div>
      <div><span className="eyebrow">Next administrator action</span><strong><ClipboardCheck size={17} />{actionState}</strong><p>{data.current.needs_review ? 'New inputs do not replace the approved version. Generate and validate a new draft.' : draft ? 'Approval rechecks permissions, validation and the current input version.' : 'Confirm restrictions before generating a change; do not infer them from forecast values.'}</p><a href="#plan">Open plan comparison <ArrowRight size={15} /></a></div>
    </section>
    <ResourceState resource={resource} />
    <section className="day-plan"><div className="section-heading"><div><span className="eyebrow">{draft ? 'Proposed draft · not approved' : 'Current approved timetable'}</span><h2>What changes in the school day</h2></div><a className="inline-link" href="#plan">Inspect plan <ArrowRight size={15} /></a></div>
      {plan ? <><div className="plan-summary"><span className="badge">Solver: {plan.solver_status}</span><span className={`badge ${plan.validation?.valid ? 'good' : 'bad'}`}>Validation: {plan.validation?.valid ? 'Passed' : 'Not passed'}</span><span>{plan.recommendation === 'baseline' ? 'Original periods retained with approved alternatives' : plan.recommendation === 'repair' ? 'Validated period repair' : 'No successful permitted plan'}</span></div><Metrics counts={plan.counts} /><Comparison plan={plan} compact /></> : <Empty>No draft or approved timetable yet. Start with confirmed restrictions.</Empty>}
    </section>
    <section><div className="section-heading"><div><span className="eyebrow">Teacher-reported · approved version only</span><h2>What has actually been implemented</h2></div><a className="inline-link" href="#review">Review reports <ArrowRight size={15} /></a></div>
      {execution ? <><dl className="metrics execution-overview"><div><dt>Reported activities</dt><dd>{execution.counts.reported}</dd></div><div><dt>Teacher-reported completed</dt><dd>{execution.counts.completed}</dd></div><div><dt>Unresolved exceptions</dt><dd>{execution.counts.unresolved}</dd></div></dl>
        {unresolved.length ? <div className="exception-list">{unresolved.map(report => <article key={report.activity_id}><CircleAlert size={18} /><div><strong>{report.activity_id} · {words(report.status)}</strong><p>{report.note || 'No note supplied'}</p><small>{report.teacher_id} · Version {report.plan_version.slice(0, 8)}</small></div><a href="#review">Review</a></article>)}</div> : <p className="status-line"><CheckCircle2 size={17} />No unresolved exceptions reported for this approved version.</p>}
        <p className="muted">Acknowledgement is receipt, not execution. Missing reports are not assumed completed.</p></> : <Empty>Execution reporting starts after administrator approval.</Empty>}
    </section>
  </>;
}
