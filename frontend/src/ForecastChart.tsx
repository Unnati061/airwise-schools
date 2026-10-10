import type { Schema } from './client';

export default function ForecastChart({ points }: { points: Schema<'EvidenceView'>['snapshot']['points'] }) {
  const times = [...new Set(points.map(p => p.valid_time))].sort().slice(0, 24);
  const selected = points.filter(p => times.includes(p.valid_time));
  const max = Math.max(1, ...selected.map(p => p.value ?? 0));
  const xy = (time: string, value: number) => `${48 + times.indexOf(time) * 590 / Math.max(1, times.length - 1)},${126 - value / max * 106}`;
  return <div className="hourly-chart"><div className="chart-title"><strong>Hourly regional forecast</strong><span><i className="pm25-key" />PM2.5 <i className="pm10-key" />PM10 · ug/m3</span></div>{times.length ? <svg viewBox="0 0 670 160" role="img" aria-label="First 24 hourly forecast values for PM2.5 and PM10, in micrograms per cubic metre. Values and timestamps are available in the forecast table.">
    {[0, 0.5, 1].map(r => <g key={r}><line x1="48" x2="638" y1={126 - r * 106} y2={126 - r * 106} stroke="#d5dfdf" /><text x="40" y={131 - r * 106} textAnchor="end" fontSize="16" fill="#445660">{Math.round(max * r)}</text></g>)}
    {['PM2.5', 'PM10'].map((p, i) => <polyline key={p} points={selected.filter(v => v.pollutant === p && v.value !== null).map(v => xy(v.valid_time, v.value!)).join(' ')} fill="none" stroke={i ? '#b36a08' : '#087e80'} strokeWidth="3" />)}
    {[0, Math.floor((times.length - 1) / 2), times.length - 1].map((i, j) => <text key={j} x={48 + i * 590 / Math.max(1, times.length - 1)} y="153" textAnchor={j === 0 ? 'start' : j === 2 ? 'end' : 'middle'} fontSize="16" fill="#445660">{new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }).format(new Date(times[i]))}</text>)}
  </svg> : <p>No hourly values available.</p>}</div>;
}
