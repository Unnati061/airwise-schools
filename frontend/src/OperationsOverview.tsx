import { ArrowRight, CircleAlert, DoorOpen } from 'lucide-react';
import { api, type Actor, type Schema } from './client';
import type { AdminData } from './App';
import TodayTimetable from './TodayTimetable';
import { activityName, activityRef, roomName } from './names';
import { ResourceState, useResource } from './ui';
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
  const pending = !!records?.draft;
  const usable = !!plan?.successful && !!plan.validation?.valid;
  const indoor = plan?.placements.filter(p => p.alternative_id && !p.deferred &&
    plan.input_snapshot.rooms.some(r => r.id === p.room_id && r.kind !== 'outdoor') &&
    plan.input_snapshot.activities.some(a => a.id === p.activity_id &&
      plan.input_snapshot.rooms.some(r => r.id === a.original_room_id && r.kind === 'outdoor'))).length || 0;
  const changes = plan?.counts?.changed_periods || 0;
  const snapshot = forecast.value?.snapshot;
  const validTime = snapshot?.points.find(p => snapshot.mode === 'REPLAY' || Date.parse(p.valid_time) >= Date.now())?.valid_time;
  const pm10 = snapshot?.points.find(p => p.pollutant === 'PM10' && p.valid_time === validTime);
  const summary = !plan ? 'Review restrictions, then generate a timetable draft.' : !usable ? 'This draft has no validated repair to approve.' : indoor ?
    `${indoor} outdoor lesson${indoor === 1 ? '' : 's'}: ${pending ? 'proposed' : 'approved'} indoor alternatives.` :
    changes ? `${changes} lesson period${changes === 1 ? '' : 's'} ${pending ? 'would change in this draft' : 'change in the approved plan'}.` :
    `${pending ? 'This draft retains' : 'The approved plan retains'} the original lesson periods.`;
  return <section className="today-decision" aria-label="Timetable decision">
    <ResourceState resource={resource} />
    {records && <>
      <div className="today-decision-summary"><div className="today-headline"><h2>{summary}</h2>
        {snapshot && <span className="today-air-chip">PM10 {pm10?.value ?? 'unavailable'} µg/m³ · {snapshot.mode === 'LIVE' ? 'regional forecast · LIVE' : 'Severe-day scenario'}</span>}
        {pending && <p>Proposed draft · not approved. Review before a separate approval.</p>}
        {!plan && <p>Only an administrator confirms restrictions.</p>}
      </div>{(!data.current.needs_review || pending) && <a className="today-action" href={plan ? '#plan' : '#evidence'}>{plan ? pending ? 'Review draft' : 'View plan' : 'Review evidence'}<ArrowRight size={18} /></a>}</div>
      {data.current.needs_review && <div className="today-stale-plan" role="status"><CircleAlert size={20} /><strong>Plan inputs changed since approval. Review before relying on this plan.</strong><a href="#plan">Review plan <ArrowRight size={18} /></a></div>}
      {plan && usable && <>
        <dl className="plan-numbers">{[['Changed periods', changes], ['Indoor substitutions', indoor], ['Room moves', plan.counts?.room_moves ?? '—']].map(([label, value]) => <div key={label}><dd>{value}</dd><dt>{label}</dt></div>)}</dl>
        <div className="today-timetable-heading"><strong>Timetable · independently validated</strong>
          <a className="today-room-action" href="#plan"><DoorOpen size={20} /><span>What if a room is unavailable?</span><ArrowRight size={18} /></a></div>
        <TodayTimetable plan={plan} proposed={pending} />
        <p className="today-retained"><strong>{plan.placements.length}</strong> activities retained across the weekly plan</p>
        <details className="today-change-details"><summary>Detailed lesson changes ({plan.differences?.length || 0})</summary>{plan.differences?.length ? plan.differences.map(d => {
          const a = plan.input_snapshot.activities.find(a => a.id === d.activity_id);
          return <p key={d.activity_id}><strong>{activityRef(d.activity_id)} · {activityName(a?.label || 'Lesson')}</strong><br />{d.original.period_id} · {roomName(d.original.room_id)} → {d.proposed.period_id || 'Deferred'} · {roomName(d.proposed.room_id)}</p>;
        }) : <p>No changes from the original timetable.</p>}</details>
      </>}
      {execution ? <section className="today-implementation" aria-label="Teacher-reported implementation"><div><h2>Implementation</h2><span>Teacher-reported · reports refer to the approved version</span></div><p><strong>{execution.counts.completed}</strong> completed · <strong>{execution.counts.reported}</strong> reported</p><a href="#review">View reports <ArrowRight size={16} /></a>
        {execution.counts.unresolved > 0 && <div className="today-exception"><CircleAlert size={20} /><strong>{execution.counts.unresolved} unresolved exception{execution.counts.unresolved === 1 ? '' : 's'}</strong><a href="#review">Review exceptions <ArrowRight size={16} /></a></div>}
      </section> : <p className="today-empty-report">Teacher-reported implementation becomes available after approval.</p>}
    </>}
    {(forecast.error || forecast.value && !['FRESH', 'REPLAY'].includes(forecast.value.freshness)) && <p className="today-review-needed">Forecast evidence needs attention; review its source details below.</p>}
  </section>;
}
