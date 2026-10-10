import { useState } from 'react';
import { LockKeyhole } from 'lucide-react';
import type { Schema } from './client';
import { activityName, className, roomName } from './names';

const dayNames: Record<string, string> = { Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday' };

export default function TodayTimetable({ plan, proposed, stale = false }: { plan: Schema<'DraftPlan'>; proposed: boolean; stale?: boolean }) {
  const input = plan.input_snapshot;
  const periodById = new Map(input.periods.map(p => [p.id, p]));
  const changed = new Set((plan.differences || []).map(d => d.activity_id));
  const days = new Set([input.affected_day]);
  for (const d of plan.differences || []) {
    for (const id of [d.original.period_id, d.proposed.period_id]) {
      const day = id && periodById.get(id)?.day;
      if (day) days.add(day);
    }
  }
  const affectedDays = [...new Set(input.periods.map(p => p.day))].filter(day => days.has(day));
  const firstChanged = input.activities.find(a => changed.has(a.id));
  const [section, setSection] = useState(firstChanged?.section_id || input.sections[0]?.id || '');
  const [day, setDay] = useState(input.affected_day);
  const selectedSection = input.sections.some(s => s.id === section) ? section : input.sections[0]?.id;
  const selectedDay = affectedDays.includes(day) ? day : affectedDays[0];
  const periods = input.periods.filter(p => p.day === selectedDay).sort((a, b) => a.number - b.number);
  const activities = input.activities.filter(a => a.section_id === selectedSection);
  const placements = new Map(plan.placements.map(p => [p.activity_id, p]));
  const comparisonLabel = proposed ? 'Proposed · not approved' : stale ? 'Previously approved' : 'Approved';
  const swaps = activities.flatMap(activity => {
    const original = periodById.get(activity.original_period_id);
    const placement = placements.get(activity.id);
    const next = placement?.period_id && periodById.get(placement.period_id);
    if (!changed.has(activity.id) || placement?.deferred || !original || !next || original.day !== selectedDay || next.day !== selectedDay || original.number >= next.number) return [];
    const reciprocal = activities.find(other => other.original_period_id === placement?.period_id && changed.has(other.id) &&
      placements.get(other.id)?.period_id === activity.original_period_id && !placements.get(other.id)?.deferred);
    return reciprocal ? [`Period ${original.number} ↔ Period ${next.number}`] : [];
  });
  const displayLabel = (label: string) => { const name = activityName(label); return name ? name[0].toUpperCase() + name.slice(1) : name; };
  function lesson(periodId: string, after: boolean) {
    const activity = activities.find(a => (after ? placements.get(a.id)?.period_id : a.original_period_id) === periodId);
    if (!activity) return <div className="today-lesson vacant">No activity assigned</div>;
    const placement = placements.get(activity.id);
    const alternative = after && activity.approved_alternatives?.find(a => a.id === placement?.alternative_id);
    const moved = placement?.period_id !== activity.original_period_id;
    const originalNumber = periodById.get(activity.original_period_id)?.number;
    const nextPeriod = placement?.period_id && periodById.get(placement.period_id);
    const isChanged = changed.has(activity.id);
    const originalRoom = input.rooms.find(r => r.id === activity.original_room_id);
    const restricted = !after && originalRoom?.kind === 'outdoor' && input.restrictions?.some(r =>
      r.kind === 'outdoor_prohibited' && r.administrator_confirmed &&
      r.section_ids.includes(activity.section_id) && r.period_ids.includes(activity.original_period_id));
    const indoor = after && !!placement?.alternative_id && !placement.deferred &&
      input.rooms.some(r => r.id === placement.room_id && r.kind !== 'outdoor');
    const originalDay = periodById.get(activity.original_period_id)?.day;
    const crossDay = nextPeriod && nextPeriod.day !== originalDay;
    const moveLabel = !nextPeriod ? 'Deferred' : after ?
      `Moved from ${crossDay && originalDay ? `${dayNames[originalDay] || originalDay} ` : ''}Period ${originalNumber}` :
      `Moved to ${crossDay ? `${dayNames[nextPeriod.day] || nextPeriod.day} ` : ''}Period ${nextPeriod.number}`;
    const stateLabel = activity.fixed ? 'Fixed lesson' : isChanged ? moved ? moveLabel : placement?.alternative_id ? 'Alternative activity' : 'Room changed' : null;
    return <div className={`today-lesson ${isChanged ? 'changed' : 'preserved'}`} data-activity={activity.id}>
      <strong>{displayLabel(alternative ? alternative.label : activity.label)}</strong>
      <span>{roomName(after ? placement?.room_id : activity.original_room_id)}</span>
      {(restricted || indoor || stateLabel) && <span className="today-lesson-state">{restricted && <span className="today-restricted">Outdoor · restricted</span>}{indoor && <span className="today-indoor">Indoor</span>}{activity.fixed && <LockKeyhole size={16} />}{stateLabel}</span>}
    </div>;
  }
  const deferred = activities.filter(a => placements.get(a.id)?.deferred && periodById.get(a.original_period_id)?.day === selectedDay);
  return <div className="today-timetable">
    <div className="today-timetable-controls"><label>Class<select aria-label="Today timetable class" value={selectedSection} onChange={e => setSection(e.target.value)}>{input.sections.map(s => <option key={s.id} value={s.id}>{className(s.id)}</option>)}</select></label>
      <label>Day<select aria-label="Today timetable day" value={selectedDay} onChange={e => setDay(e.target.value)}>{affectedDays.map(d => <option key={d} value={d}>{dayNames[d] || d}</option>)}</select></label></div>
    {swaps.length > 0 && <p className="today-swap-summary">Reciprocal swap: {swaps.join('; ')}</p>}
    <div className="today-schedule" role="table" aria-label="Original and repaired timetable"><div className="today-schedule-head" role="row"><strong role="columnheader">Period</strong><strong role="columnheader">Original</strong><strong role="columnheader">{comparisonLabel}</strong></div>
      {periods.map(period => <div className="today-schedule-row" role="row" key={period.id}><div className="today-period" role="rowheader">Period {period.number}</div><div role="cell"><span className="today-mobile-label">Original · Period {period.number}</span>{lesson(period.id, false)}</div><div role="cell"><span className="today-mobile-label">{comparisonLabel} · Period {period.number}</span>{lesson(period.id, true)}</div></div>)}
    </div>
    {deferred.length > 0 && <p>{proposed ? 'Proposed deferrals' : 'Approved deferrals'}: {deferred.map(a => activityName(a.label)).join(', ')}. Activities remain accounted for; they are not completed.</p>}
  </div>;
}
