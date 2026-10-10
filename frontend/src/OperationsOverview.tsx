import { ArrowRight, CircleAlert } from 'lucide-react';
import { api, type Actor, type Schema } from './client';
import type { AdminData } from './App';
import { PlanNumbers } from './Timetable';
import { activityName, activityRef, roomName } from './names';
import { Empty, ResourceState, useResource, words } from './ui';
import type { ForecastResource } from './Today';

export default function OperationsOverview({ actor, data, forecast }: { actor: Actor; data: AdminData; forecast: ForecastResource }) {
  const version = data.current.plan_version;
  const selected = sessionStorage.getItem(`airwise.draft.${actor.sub}`);
  const resource = useResource(async () => {
    const draft = selected && selected !== version ? await api<Schema<'DraftPlan'>>(`/draft-plans/${selected}`) : null;
    if (!version) return { draft, detail: null, execution: null };
    const [detail, execution] = await Promise.all([api<Schema<'ApprovedPlanDetail'>>(`/approved-plans/${version}`), api<Schema<'ExecutionReview'>>(`/approved-plans/${version}/review`)]);
    return { draft, detail, execution };
  }, [version, selected, data.confirmed.revision]);
  const records = resource.value, plan = records?.draft || records?.detail?.plan, execution = records?.execution;
  const unresolved = execution?.reports.filter(r => execution.unresolved_activity_ids.includes(r.activity_id)) || [];
  return <><div className="decision-banner"><div><strong>{data.current.needs_review ? 'Review a revised timetable' : records?.draft ? 'A draft is ready for review' : 'Your approved timetable is in effect'}</strong><span>{forecast.error || forecast.value && !['FRESH', 'REPLAY'].includes(forecast.value.freshness) ? 'Forecast needs attention. ' : ''}Restrictions need administrator confirmation, not automatic forecast rules.</span></div><a href="#plan">Review plan <ArrowRight size={20} /></a></div><ResourceState resource={resource} />
    <div className="today-operations"><div className="plan-card"><div className="section-heading"><div><span className="eyebrow">{records?.draft ? 'Proposed draft · not approved' : 'Approved plan'}</span><h2>Timetable repair</h2></div><a href="#plan" className="inline-link">Compare <ArrowRight size={20} /></a></div>{plan ? <><PlanNumbers plan={plan} /><div className="change-preview">{(plan.differences ?? []).slice(0, 3).map(d => { const a = plan.input_snapshot.activities.find(a => a.id === d.activity_id)!; return <div key={d.activity_id}><strong>{activityRef(a.id)}</strong><span>{activityName(a.label)} · {d.original.period_id} <ArrowRight size={16} /> {d.proposed.period_id} · {roomName(d.proposed.room_id)}</span></div>; })}</div><span className="status-line">{plan.validation?.valid ? 'Independently validated' : 'Not ready for approval'} · {plan.recommendation === 'baseline' ? 'Original periods retained' : plan.successful ? 'Repair available' : 'No successful repair'}</span></> : <Empty>Confirm restrictions and generate your first draft.</Empty>}</div>
      <div className={`implementation-card ${unresolved.length ? 'has-exception' : ''}`}><span className="eyebrow">Teacher-reported · approved plan only</span><h2>Implementation</h2>{execution ? <><div className="implementation-counts"><strong>{execution.counts.completed}<span>Completed</span></strong><strong>{execution.counts.reported}<span>Reported</span></strong></div><h3><CircleAlert size={20} />{execution.counts.unresolved} unresolved exception{execution.counts.unresolved === 1 ? '' : 's'}</h3>{unresolved.slice(0, 1).map(r => <div key={r.activity_id}><strong>{activityRef(r.activity_id)} · {words(r.status)}</strong><p>{r.note || 'No teacher note supplied'}</p></div>)}<a className="review-action" href="#review">Review exceptions <ArrowRight size={20} /></a><p className="muted">Acknowledgement is receipt, not completion.</p></> : <Empty>Reports become available after approval.</Empty>}</div>
    </div></>;
}
