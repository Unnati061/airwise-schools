import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Wind, RefreshCw } from 'lucide-react';
import type { components } from './api';
import './style.css';

type School = components['schemas']['School'];

function App() {
  const [school, setSchool] = useState<School | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let disposed = false;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    setState('loading');
    Promise.all(['/health', '/school'].map(async path => {
      const response = await fetch(`/api${path}`, { signal: controller.signal });
      if (!response.ok) throw new Error('API unavailable');
      return response.json();
    })).then(([health, fixture]) => {
      if (disposed) return;
      if (health.status !== 'ok') throw new Error('API unhealthy');
      setSchool(fixture); setState('ready');
    }).catch(() => { if (!disposed) setState('error'); })
      .finally(() => window.clearTimeout(timeout));
    return () => { disposed = true; controller.abort(); window.clearTimeout(timeout); };
  }, [revision]);
  return <>
    <header><Wind size={26} /><strong>AirWise Schools</strong><span className="tag">SYNTHETIC</span></header>
    <main>
      <div className="heading"><h1>{school?.name ?? 'School overview'}</h1><button title="Refresh school" aria-label="Refresh school" disabled={state === 'loading'} onClick={() => setRevision(r => r + 1)}><RefreshCw size={18} /></button></div>
      <p role="status" className={state === 'error' ? 'error' : ''}>{state === 'loading' ? 'Connecting...' : state === 'error' ? 'Backend unavailable. Retry when the connection returns.' : 'Backend connected'}</p>
      <h2>Sections</h2>
      {school && <table><thead><tr><th>Section</th><th>Students</th></tr></thead><tbody>{school.sections.map(section => <tr key={section.id}><td>{section.label}</td><td>{section.size}</td></tr>)}</tbody></table>}
      <footer>Synthetic school data · No live air-quality evidence</footer>
    </main>
  </>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
