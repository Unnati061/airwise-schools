import { useState } from 'react';
import { ArrowRight, LockKeyhole } from 'lucide-react';
import type { Schema } from './client';
import { activityName, className, roomName } from './names';

const dayNames: Record<string, string> = { Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday' };

export default function TodayTimetable({ plan, proposed }: { plan: Schema<'DraftPlan'>; proposed: boolean }) {
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
  function lesson(periodId: string, after: boolean) {
    const activity = activities.find(a => (after ? placements.get(a.id)?.period_id : a.original_period_id) === periodId);
    if (!activity) return <div className="today-lesson vacant">No activity assigned</div>;
    const placement = placements.get(activity.id);
    const alternative = after && activity.approved_alternatives?.find(a => a.id === placement?.alternative_id);
    const moved = placement?.period_id !== activity.original_period_id;
    const originalNumber = periodById.get(activity.original_period_id)?.number;
    const nextPeriod = placement?.period_id && periodById.get(placement.period_id);
    const isChanged = changed.has(activity.id);
    return <div className={`today-lesson ${isChanged ? 'changed' : 'preserved'}`} data-activity={activity.id}>
      <strong>{activityName(alternative ? alternative.label : activity.label)}</strong>
      <span>Room: {roomName(after ? placement?.room_id : activity.original_room_id)}</span>
      <span className="today-lesson-state">{activity.fixed ? <><LockKeyhole size={14} />Fixed · preserved</> : isChanged ? moved ? <>{nextPeriod ? <>Period {originalNumber} <ArrowRight size={14} />{nextPeriod.day !== periodById.get(activity.original_period_id)?.day && `${dayNames[nextPeriod.day] || nextPeriod.day} `}Period {nextPeriod.number}</> : 'Deferred'}</> : 'Activity / room changed' : 'Preserved'}</span>
    </div>;
  }
  const deferred = activities.filter(a => placements.get(a.id)?.deferred && periodById.get(a.original_period_id)?.day === selectedDay);
  return <div className="today-timetable">
    <div className="today-timetable-controls"><label>Class<select aria-label="Today timetable class" value={selectedSection} onChange={e => setSection(e.target.value)}>{input.sections.map(s => <option key={s.id} value={s.id}>{className(s.id)}</option>)}</select></label>
      <label>Day<select aria-label="Today timetable day" value={selectedDay} onChange={e => setDay(e.target.value)}>{affectedDays.map(d => <option key={d} value={d}>{dayNames[d] || d}</option>)}</select></label><span>Changed lessons are labelled; unchanged lessons show the full swap.</span></div>
    <div className="today-schedule" role="table" aria-label="Original and repaired timetable"><div className="today-schedule-head" role="row"><strong role="columnheader">Period</strong><strong role="columnheader">Original</strong><strong role="columnheader">{proposed ? 'Proposed · not approved' : 'Approved'}</strong></div>
      {periods.map(period => <div className="today-schedule-row" role="row" key={period.id}><div className="today-period" role="rowheader">Period {period.number}</div><div role="cell"><span className="today-mobile-label">Original · Period {period.number}</span>{lesson(period.id, false)}</div><div role="cell"><span className="today-mobile-label">{proposed ? 'Proposed' : 'Approved'} · Period {period.number}</span>{lesson(period.id, true)}</div></div>)}
    </div>
    {deferred.length > 0 && <p>{proposed ? 'Proposed deferrals' : 'Approved deferrals'}: {deferred.map(a => activityName(a.label)).join(', ')}. Activities remain accounted for; they are not completed.</p>}
  </div>;
}
