import { useState } from 'react';
import { ArrowDownUp, ArrowRight, LockKeyhole } from 'lucide-react';
import type { Schema } from './client';
import { activityName, className, roomName } from './names';

export function PlanNumbers({ plan }: { plan: Schema<'DraftPlan'> }) {
  const indoor = plan.placements.filter(p => p.alternative_id && !p.deferred && plan.input_snapshot.rooms.some(r => r.id === p.room_id && r.kind !== 'outdoor')).length;
  return <dl className="plan-numbers">{[['Changed periods', plan.counts?.changed_periods ?? '—'], ['Indoor substitutions', indoor], ['Room moves', plan.counts?.room_moves ?? '—'], ['Activities retained', plan.placements.length]].map(([label, value]) => <div key={label}><dd>{value}</dd><dt>{label}</dt></div>)}</dl>;
}

export default function Timetable({ plan, previous }: { plan: Schema<'DraftPlan'>; previous?: Schema<'DraftPlan'> | null }) {
  const [section, setSection] = useState('6-a');
  const [selected, setSelected] = useState('6-a:Mon-2');
  const day = plan.input_snapshot.affected_day;
  const periods = plan.input_snapshot.periods.filter(p => p.day === day).sort((a, b) => a.number - b.number);
  const activities = plan.input_snapshot.activities.filter(a => a.section_id === section);
  const placed = new Map(plan.placements.map(p => [p.activity_id, p]));
  const prior = previous && new Map(previous.placements.map(p => [p.activity_id, p]));
  const differences = new Set((plan.differences ?? []).map(d => d.activity_id));
  return <div className="timetable-tool"><div className="section-heading"><div><h2>{previous ? 'Previous plan → revised draft' : 'Before → after'}</h2><p>{day === 'Mon' ? 'Monday' : day} · select a lesson to trace its placement</p></div><label className="inline-field">Class<select aria-label="Timetable class" value={section} onChange={e => setSection(e.target.value)}>{plan.input_snapshot.sections.map(s => <option key={s.id} value={s.id}>{className(s.id)}</option>)}</select></label></div>
    <div className="timetable-grid" aria-label="Before and after timetable"><div className="slot-head">{className(section)}</div>{periods.map(p => <div className="slot-head" key={p.id}>Period {p.number}</div>)}
      {['before', 'after'].map(side => <div className="timetable-track" key={side}><div className="track-label">{side === 'before' ? previous ? 'Previous' : 'Original' : 'Revised'}<ArrowDownUp size={20} /></div>{periods.map(period => {
        const activity = activities.find(a => (side === 'before' ? prior?.get(a.id)?.period_id || a.original_period_id : placed.get(a.id)?.period_id) === period.id);
        if (!activity) return <div className="slot empty-slot" key={period.id}>No activity</div>;
        const next = placed.get(activity.id), before = prior?.get(activity.id);
        const oldPeriod = before?.period_id || activity.original_period_id;
        const oldRoom = before?.room_id || activity.original_room_id;
        const isChanged = previous ? JSON.stringify(next) !== JSON.stringify(before) : differences.has(activity.id);
        const alternative = (activity.approved_alternatives ?? []).find(a => a.id === (side === 'after' ? next?.alternative_id : before?.alternative_id));
        return <button key={period.id} className={`slot ${isChanged ? 'slot-changed' : ''} ${selected === activity.id ? 'slot-selected' : ''}`} onClick={() => setSelected(activity.id)} aria-pressed={selected === activity.id} title={`Trace ${className(section)} ${activityName(activity.label)}`}>
          <strong>{activityName(alternative?.label || activity.label)}</strong><span>{roomName(side === 'before' ? oldRoom : next?.room_id)}</span>
          {activity.fixed ? <span className="slot-tag"><LockKeyhole size={14} />Fixed</span> : isChanged ? <span className="slot-tag">{oldPeriod !== next?.period_id ? <>P{oldPeriod?.split('-').at(-1)} <ArrowRight size={14} /> P{next?.period_id?.split('-').at(-1)}</> : 'Room / activity changed'}</span> : <span className="slot-tag">Preserved</span>}
        </button>;
      })}</div>)}
    </div>
    <p className="trace-key"><span className="trace-swatch" />Matching outlines connect the same lesson before and after. Fixed lessons remain fixed.</p>
  </div>;
}
