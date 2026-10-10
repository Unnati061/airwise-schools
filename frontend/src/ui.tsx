import { useEffect, useRef, useState, type DependencyList, type ReactNode } from 'react';
import { AlertCircle, CheckCircle2, RefreshCw, X } from 'lucide-react';
import { ApiError, type Schema } from './client';

export function stamp(value?: string | null) {
  if (!value) return 'Not supplied';
  return new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' }).format(new Date(value));
}
export function short(value?: string | null) { return value ? value.slice(0, 8) : 'None'; }
export function dateInSchool(value: string) { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value)); }
export function words(value: string) { return value.toLowerCase().replaceAll('_', ' ').replace(/^./, c => c.toUpperCase()); }
export function Mode({ mode }: { mode: 'LIVE' | 'REPLAY' | 'MANUAL' | 'UNKNOWN' }) { return <span className={`badge mode-${mode.toLowerCase()}`}>{mode === 'REPLAY' ? 'SYNTHETIC REPLAY' : mode === 'LIVE' ? 'LIVE regional forecast' : mode === 'UNKNOWN' ? 'Evidence provenance not loaded' : 'Manually confirmed'}</span>; }
export function Version({ value }: { value: string }) { return <details className="version-detail"><summary>Version details</summary><code className="version">{value}</code></details>; }

export function useResource<T>(load: () => Promise<T>, deps: DependencyList, keepPrevious = false) {
  const [value, setValue] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError(null); if (!keepPrevious) setValue(null);
    load().then(result => { if (active) setValue(result); }).catch(error => { if (active) setError(error); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [...deps, revision]);
  return { value, loading, error, reload: () => setRevision(r => r + 1) };
}

export function useAction() {
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [notice, setNotice] = useState('');
  const [retry, setRetry] = useState<(() => void) | null>(null);
  async function run<T>(operation: () => Promise<T>, success: (result: T) => void, message: string, safeRetry = false) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(null); setNotice(''); setRetry(null);
    try { const result = await operation(); success(result); setNotice(message); }
    catch (error) {
      setError(error instanceof Error ? error : new Error('Request failed.'));
      if (safeRetry && error instanceof ApiError && [0, 500, 502, 503, 504].includes(error.status)) {
        setRetry(() => () => { void run(operation, success, message, true); });
      }
    }
    finally { lock.current = false; setBusy(false); }
  }
  return { busy, error, notice, run, retry };
}

export function ErrorNotice({ error }: { error: Error | null }) {
  if (!error) return null;
  const status = error instanceof ApiError ? error.status : 0;
  return <div role="alert" className="notice danger"><AlertCircle size={18} /><div><strong>{status === 403 ? 'Access denied' : status === 409 ? 'Version or evidence conflict' : status === 429 ? 'Daily analysis allowance reached' : 'Request could not be completed'}</strong><p>{error.message}</p>{status === 409 && <p>Refresh the current inputs and status. A newer revision requires a new draft and approval.</p>}</div></div>;
}
export function ActionNotice({ action }: { action: ReturnType<typeof useAction> }) { return <><ErrorNotice error={action.error} />{action.retry && <button className="secondary" disabled={action.busy} onClick={action.retry}><RefreshCw size={16} />Retry the same request</button>}{action.notice && <div role="status" className="notice success"><CheckCircle2 size={18} />{action.notice}</div>}{action.busy && <p role="status">Request in progress...</p>}</>; }
export function Loading({ label = 'Loading school records...' }: { label?: string }) { return <p role="status" className="loading">{label}</p>; }
export function ResourceState({ resource }: { resource: { loading: boolean; error: Error | null; reload: () => void } }) { return <>{resource.loading && <Loading />}{resource.error && <><ErrorNotice error={resource.error} /><button className="secondary" disabled={resource.loading} onClick={resource.reload}><RefreshCw size={16} />Retry loading</button></>}</>; }
export function Heading({ title, children }: { title: string; children?: ReactNode }) { return <div className="page-heading"><h1>{title}</h1><div className="toolbar">{children}</div></div>; }
export function Refresh({ onClick, disabled = false, label = 'Refresh records' }: { onClick: () => void; disabled?: boolean; label?: string }) { return <button className="icon-button" title={label} aria-label={label} disabled={disabled} onClick={onClick}><RefreshCw size={18} /></button>; }
export function Empty({ children }: { children: ReactNode }) { return <div className="empty">{children}</div>; }
export function Metrics({ counts }: { counts: Schema<'Counts'> | null | undefined }) { if (!counts) return null; return <dl className="metrics">{[['Changed periods', counts.changed_periods], ['Substitutions', counts.substitutions], ['Deferrals', counts.deferrals], ['Room moves', counts.room_moves]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>; }
export function Dialog({ title, close, children, busy }: { title: string; close: () => void; children: ReactNode; busy?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); return () => ref.current?.close(); }, []);
  return <dialog ref={ref} onCancel={event => { event.preventDefault(); if (!busy) close(); }}><div className="dialog-heading"><h2>{title}</h2><button className="icon-button" title="Close" aria-label="Close" disabled={busy} onClick={close}><X size={18} /></button></div>{children}</dialog>;
}
