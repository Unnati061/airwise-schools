import { useEffect, useState } from 'react';
import { ArrowRight, Database, Radio, Wind } from 'lucide-react';
import type { Actor, Schema } from './client';
import type { AdminData } from './App';
import OperationsOverview from './OperationsOverview';
import ForecastChart from './ForecastChart';
import { dateInSchool, Empty, Heading, Mode, Refresh, ResourceState, stamp } from './ui';

export type ForecastResource = { value: Schema<'EvidenceView'> | null; loading: boolean; error: Error | null; reload: () => void };
export function ModeSwitch({ mode, changeMode }: { mode: 'LIVE' | 'REPLAY'; changeMode: (mode: 'LIVE' | 'REPLAY') => void }) { return <div className="segmented" role="group" aria-label="Evidence mode"><button aria-pressed={mode === 'LIVE'} onClick={() => changeMode('LIVE')}><Radio size={15} />Live</button><button aria-pressed={mode === 'REPLAY'} onClick={() => changeMode('REPLAY')}><Database size={15} />Synthetic replay</button></div>; }

export function Provenance({ evidence }: { evidence: Schema<'EvidenceView'> }) {
  const snapshot = evidence.snapshot;
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const timer = window.setInterval(() => setNow(Date.now()), 60000); return () => window.clearInterval(timer); }, []);
  const minutes = Math.max(0, Math.floor((now - Date.parse(snapshot.retrieved_at)) / 60000));
  const issue = snapshot.mode === 'REPLAY' ? 'Not applicable — synthetic fixture, no model cycle' : snapshot.model_issue_time ? stamp(snapshot.model_issue_time) : 'Not supplied by provider; model-cycle freshness unknown';
  return <section className="provenance">
    <div className="section-heading"><h2>Source record</h2><Mode mode={snapshot.mode} /></div>
    <dl className="details">
      <div><dt>Source</dt><dd>{snapshot.source}{snapshot.mode === 'LIVE' && <> · <a href={snapshot.source_url} target="_blank" rel="noreferrer">Provider request</a></>}</dd></div>
      <div><dt>{snapshot.mode === 'REPLAY' ? 'Fixture timestamp' : 'Retrieved'}</dt><dd><time title={snapshot.retrieved_at}>{stamp(snapshot.retrieved_at)}</time>{snapshot.mode === 'LIVE' && <> · Retrieval age {minutes} min</>}</dd></div>
      <div><dt>Model issue time</dt><dd>{issue}</dd></div>
      <div><dt>Spatial / time resolution</dt><dd>{snapshot.resolution}</dd></div>
      <div><dt>Coordinates</dt><dd>{snapshot.mode === 'REPLAY' ? <>Scenario {snapshot.requested_latitude}, {snapshot.requested_longitude}; no physical model grid</> : <>Requested {snapshot.requested_latitude}, {snapshot.requested_longitude} · Provider grid {snapshot.grid_latitude}, {snapshot.grid_longitude}</>}</dd></div>
      <div><dt>Evidence usability</dt><dd>{evidence.freshness === 'FRESH' ? `Retrieval / future-value checks passed at ${stamp(evidence.checked_at)}; not model freshness` : evidence.freshness === 'REPLAY' ? 'Synthetic replay, not current conditions' : 'Stale or missing forecast values; review cannot be confirmed'}</dd></div>
    </dl>
    <details><summary>Limitations and source hash</summary><ul>{snapshot.limitations.map(l => <li key={l}>{l}</li>)}</ul><p>Source-body SHA-256 <code className="hash">{snapshot.raw_sha256}</code></p></details>
    <div className="notice neutral"><strong>Station observations unavailable</strong><p>{evidence.observation_limitation}</p></div>
  </section>;
}

export default function Today({ forecast, mode, changeMode, data, actor }: { forecast: ForecastResource; mode: 'LIVE' | 'REPLAY'; changeMode: (mode: 'LIVE' | 'REPLAY') => void; data?: AdminData | null; actor: Actor }) {
  const [day, setDay] = useState('');
  const snapshot = forecast.value?.snapshot;
  const future = snapshot?.points.filter(p => snapshot.mode === 'REPLAY' || Date.parse(p.valid_time) >= Date.now()) ?? [];
  const first = future[0]?.valid_time;
  const dates = [...new Set(snapshot?.points.map(p => dateInSchool(p.valid_time)) ?? [])];
  const selectedDay = dates.includes(day) ? day : first ? dateInSchool(first) : dates[0] || '';
  const times = [...new Set(snapshot?.points.filter(p => dateInSchool(p.valid_time) === selectedDay).map(p => p.valid_time) ?? [])];
  const valueAt = (pollutant: string, time?: string) => snapshot?.points.find(p => p.pollutant === pollutant && p.valid_time === time)?.value;
  return <div className="today-view"><Heading title="Today" />{data && <OperationsOverview actor={actor} data={data} forecast={forecast} />}<ResourceState resource={forecast} /><div className="today-forecast-controls"><ModeSwitch mode={mode} changeMode={changeMode} /><Refresh onClick={forecast.reload} disabled={forecast.loading} label="Refresh forecast" /></div>{forecast.value && <div className="forecast-card">
    {snapshot!.mode === 'REPLAY' && <p className="replay-note">Synthetic replay · invented demo values, not current conditions.</p>}
    <div className="forecast-card-heading"><strong>Regional forecast, not campus measurement</strong><Mode mode={snapshot!.mode} /></div><div className="forecast-secondary"><div><div className="forecast-strip">{['PM2.5', 'PM10'].map(pollutant => <div key={pollutant}><span className="metric-label"><Wind size={20} />{pollutant}</span><strong>{valueAt(pollutant, first) ?? 'Unavailable'} <small>ug/m3</small></strong></div>)}</div><p>Valid {first ? stamp(first) : 'No future values'}</p><p>{snapshot!.mode === 'LIVE' ? 'Open-Meteo / CAMS' : 'Synthetic fixture'} · Station observations unavailable.</p></div><ForecastChart points={snapshot!.points.filter(p => dateInSchool(p.valid_time) === selectedDay)} /></div>
    <details className="evidence-details"><summary>Forecast provenance and limitations</summary><Provenance evidence={forecast.value} /></details>
    <details className="evidence-details"><summary>Hourly forecast</summary><div className="section-heading"><h2>Hourly forecast</h2><label className="inline-field">Valid date<select value={selectedDay} onChange={e => setDay(e.target.value)}>{dates.map(d => <option key={d}>{d}</option>)}</select></label></div>{times.length ? <div className="table-scroll"><table><thead><tr><th>Valid time (school time)</th><th>PM2.5 (ug/m3)</th><th>PM10 (ug/m3)</th></tr></thead><tbody>{times.map(time => <tr key={time}><td>{stamp(time)}</td><td>{valueAt('PM2.5', time) ?? 'Unavailable'}</td><td>{valueAt('PM10', time) ?? 'Unavailable'}</td></tr>)}</tbody></table></div> : <Empty>No forecast values are available for this date.</Empty>}</details>
  </div>}{!data && <a className="next-link" href="#evidence">Review evidence and restrictions <ArrowRight size={17} /></a>}</div>;
}
