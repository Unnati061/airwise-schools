import { useEffect, useState, type FormEvent } from 'react';
import { BookOpen, CalendarDays, ClipboardList, Home, Inbox, LogOut, School, ShieldCheck } from 'lucide-react';
import { api, sessionUser, signIn, signOut, subscribe, type Actor, type Schema } from './client';
import { ActionNotice, ErrorNotice, Loading, ResourceState, useAction, useResource } from './ui';
import Today from './Today';
import Evidence from './Evidence';
import Plan from './Plan';
import TeacherInbox from './TeacherInbox';
import Review from './Review';

export type AdminData = { confirmed: Schema<'ConfirmedInput'>; current: Schema<'CurrentPlan'>; history: Schema<'PlanVersionSummary'>[] };
export type View = 'today' | 'evidence' | 'plan' | 'inbox' | 'review';
const navigation = [{ id: 'today', label: 'Today', icon: Home }, { id: 'evidence', label: 'Evidence & restrictions', icon: BookOpen }, { id: 'plan', label: 'Plan comparison', icon: CalendarDays }, { id: 'inbox', label: 'Teacher inbox', icon: Inbox }, { id: 'review', label: 'Review', icon: ClipboardList }] as const;
function hashView(): View { const value = location.hash.slice(1); return navigation.some(v => v.id === value) ? value as View : 'today'; }
export function navigate(view: View) { location.hash = view; }

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const action = useAction();
  function submit(event: FormEvent) {
    event.preventDefault();
    void action.run(() => signIn(username.trim(), password), () => {}, 'Signed in.');
    setPassword('');
  }
  return <main className="login"><div className="login-brand"><School size={32} /><h1>AirWise Schools</h1></div><p className="demo-label">Demo school · sample school data</p><form onSubmit={submit}><h2>School sign-in</h2><label>Username<input autoComplete="username" required value={username} onChange={e => setUsername(e.target.value)} /></label><label>Password<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label><button className="primary" disabled={action.busy}><ShieldCheck size={17} />{action.busy ? 'Signing in...' : 'Sign in'}</button><ActionNotice action={action} /></form><p className="muted">Secure school access · Cognito</p></main>;
}

function Administrator({ actor, view }: { actor: Actor; view: View }) {
  const [mode, setMode] = useState<'LIVE' | 'REPLAY'>(() => sessionStorage.getItem('airwise.mode') === 'REPLAY' ? 'REPLAY' : 'LIVE');
  const data = useResource(async () => {
    const [confirmed, current, history] = await Promise.all([api<Schema<'ConfirmedInput'>>('/inputs'), api<Schema<'CurrentPlan'>>('/current-plan'), api<Schema<'PlanVersionSummary'>[]>('/approved-plans')]);
    return { confirmed, current, history };
  }, [], true);
  const forecast = useResource(() => api<Schema<'EvidenceView'>>(`/evidence/forecast?mode=${mode}`), [mode]);
  function changeMode(value: 'LIVE' | 'REPLAY') { sessionStorage.setItem('airwise.mode', value); setMode(value); }
  return <>
    {view !== 'today' && <div className="context-bar"><span className={`plan-state ${data.value?.current.needs_review ? 'needs-review' : ''}`}>{data.value?.current.needs_review ? 'Approved plan needs review' : data.value?.current.plan_version ? 'Approved plan on record' : 'No approved plan'}</span></div>}
    <ResourceState resource={data} />
    {view === 'today' && <Today actor={actor} data={data.value} forecast={forecast} mode={mode} changeMode={changeMode} />}
    {view === 'evidence' && data.value && <Evidence actor={actor} data={data.value} reload={data.reload} forecast={forecast} mode={mode} changeMode={changeMode} />}
    {view === 'plan' && data.value && <Plan actor={actor} data={data.value} reload={data.reload} refreshing={data.loading} />}
    {view === 'review' && data.value && <Review data={data.value} reload={data.reload} />}
    {view === 'inbox' && <div className="notice warning">Teacher assignments require a teacher sign-in. Administrator execution review is available in Review.</div>}
  </>;
}

function Workspace({ actor, username }: { actor: Actor; username: string }) {
  const [view, setView] = useState<View>(() => actor.role === 'teacher' ? 'inbox' : hashView());
  useEffect(() => { const changed = () => setView(hashView()); window.addEventListener('hashchange', changed); return () => window.removeEventListener('hashchange', changed); }, []);
  const visible = actor.role === 'administrator' ? navigation.filter(n => n.id !== 'inbox') : navigation.filter(n => n.id === 'inbox');
  const allowed = actor.role === 'administrator' || view === 'inbox';
  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href={actor.role === 'teacher' ? '#inbox' : '#today'}><School size={25} /><span>AirWise <strong>Schools</strong></span></a><div className="school-label">Greater Noida<span>Six sections · School operations</span></div><nav aria-label="Main navigation">{visible.map(({ id, label, icon: Icon }) => <a key={id} href={`#${id}`} aria-current={view === id ? 'page' : undefined}><Icon size={18} /><span>{label}</span></a>)}</nav><div className="sidebar-footer"><ShieldCheck size={16} /><span>Authenticated school access</span></div></aside>
    <div className="workspace">
      <header className="topbar"><span className="demo-label">Demo school · sample school data</span><div className="identity"><span><strong>{actor.role === 'teacher' ? 'School teacher' : 'School administrator'}</strong><small>Greater Noida</small></span><button className="sign-out" title="Sign out" onClick={signOut}><LogOut size={18} />Sign out</button></div></header>
      <main className="content">{!allowed ? <div className="notice danger" role="alert">Administrator access required. <a href="#inbox">Open your teacher inbox</a></div> : actor.role === 'teacher' ? <TeacherInbox actor={actor} /> : <Administrator actor={actor} view={view} />}</main>
      <footer className="app-footer"><span>School time · Asia/Kolkata</span><details><summary>Scope and limitations</summary><p>Single-period activities, one affected day. Regional forecasts are not campus measurements. No verified active closure order, measured exposure reduction or health benefit. Indoor placement does not establish indoor air quality.</p></details></footer>
    </div>
  </div>;
}

function VerifiedSession({ username }: { username: string }) {
  const identity = useResource(() => api<Actor>('/me'), [username]);
  return <>{identity.loading && <div className="session-screen"><Loading label="Verifying school identity..." /><button className="secondary" onClick={signOut}>Sign out</button></div>}{identity.error && <div className="session-screen"><ErrorNotice error={identity.error} /><button className="secondary" onClick={identity.reload}>Retry identity verification</button><button className="secondary" onClick={signOut}>Sign out</button></div>}{identity.value && <Workspace key={identity.value.sub} actor={identity.value} username={username} />}</>;
}

export default function App() {
  const [username, setUsername] = useState(sessionUser);
  useEffect(() => subscribe(() => setUsername(sessionUser())), []);
  return username ? <VerifiedSession key={username} username={username} /> : <Login />;
}
