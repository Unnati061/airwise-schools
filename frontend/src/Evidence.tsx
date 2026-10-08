import { useEffect, useState, type FormEvent } from 'react';
import { ArrowRight, Check, FileText, Sparkles } from 'lucide-react';
import { api, type Actor, type Schema } from './client';
import type { AdminData } from './App';
import { ActionNotice, Empty, Heading, Mode, ResourceState, stamp, useAction, useResource, Version } from './ui';
import { ModeSwitch, Provenance, type ForecastResource } from './Today';

export default function Evidence({ actor, data, reload, forecast, mode, changeMode }: { actor: Actor; data: AdminData; reload: () => void; forecast: ForecastResource; mode: 'LIVE' | 'REPLAY'; changeMode: (mode: 'LIVE' | 'REPLAY') => void }) {
  const policies = useResource(() => api<Schema<'PolicyExcerpt'>[]>('/policy-excerpts'), []);
  const [selectedPolicies, setSelectedPolicies] = useState<string[]>(['ncdc-2025-school-5ii']);
  const [notice, setNotice] = useState('');
  const [noticeDigest, setNoticeDigest] = useState('');
  useEffect(() => {
    let current = true;
    setNoticeDigest('');
    crypto.subtle.digest('SHA-256', new TextEncoder().encode(notice)).then(bytes => {
      if (current) setNoticeDigest([...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, '0')).join(''));
    });
    return () => { current = false; };
  }, [notice]);
  const [analysis, setAnalysis] = useState<Schema<'AnalysisResult'> | null>(null);
  const [proposalIds, setProposalIds] = useState<string[]>([]);
  const [periodIds, setPeriodIds] = useState<string[]>([]);
  const [date, setDate] = useState('');
  const [noticeReviewed, setNoticeReviewed] = useState(false);
  const [ambiguitiesReviewed, setAmbiguitiesReviewed] = useState(false);
  const [confirmedAnalysis, setConfirmedAnalysis] = useState('');
  const analyzeAction = useAction(), confirmAction = useAction();
  const storageKey = `airwise.analysis.${actor.sub}`;
  const saved = useResource(async () => {
    const id = sessionStorage.getItem(storageKey) || data.confirmed.evidence_binding?.analysis_id;
    return id ? api<Schema<'AnalysisResult'>>(`/notice-analyses/${id}`) : null;
  }, []);
  const active = analysis || saved.value;
  const bound = useResource(() => active ? api<Schema<'EvidenceView'>>(`/evidence/${active.evidence_id}`) : Promise.resolve(null), [active?.evidence_id]);
  const snapshot = forecast.value?.snapshot;
  const restrictions = data.confirmed.input.restrictions ?? [];
  const alreadyConfirmed = active && (confirmedAnalysis === active.id || data.confirmed.evidence_binding?.analysis_id === active.id);
  const compatible = active && snapshot && active.evidence_id === snapshot.id && active.mode === mode && active.input_revision === data.confirmed.revision && active.notice_sha256 === noticeDigest && [...active.policy_ids].sort().join('|') === [...selectedPolicies].sort().join('|');
  const usable = forecast.value && (forecast.value.freshness === 'REPLAY' || (forecast.value.freshness === 'FRESH' && Date.now() - Date.parse(forecast.value.snapshot.retrieved_at) <= 3600000));
  function toggle(values: string[], value: string, set: (v: string[]) => void) { set(values.includes(value) ? values.filter(v => v !== value) : [...values, value]); }
  function syntheticNotice() { setNotice('SYNTHETIC UNVERIFIED SCHOOL NOTICE: On 2026-10-12, restrict outdoor PE for section 6A in Monday period 2; use its explicitly approved indoor classroom alternative. Administrator review is required. This is not a legal closure or GRAP activation order.'); }
  function analyze(event: FormEvent) {
    event.preventDefault();
    if (!snapshot || !usable || !selectedPolicies.length || analyzeAction.busy || confirmAction.busy) return;
    const body: Schema<'AnalysisRequest'> = { notice, evidence_id: snapshot.id, mode, policy_ids: selectedPolicies };
    void analyzeAction.run(() => api<Schema<'AnalysisResult'>>('/notice-analyses', 'POST', body), result => {
      setAnalysis(result); setProposalIds([]); setPeriodIds([]); setDate(result.interpretation?.affected_dates[0]?.start || '');
      setNoticeReviewed(false); setAmbiguitiesReviewed(false); sessionStorage.setItem(storageKey, result.id);
    }, 'Interpretation recorded. Restrictions have not been confirmed.');
  }
  function confirm(event: FormEvent) {
    event.preventDefault();
    if (!active || !compatible || !usable || alreadyConfirmed || active.status !== 'SUCCESS' || !proposalIds.length || !periodIds.length || !date || !noticeReviewed || !ambiguitiesReviewed || confirmAction.busy) return;
    const body: Schema<'ReviewConfirmation'> = { expected_revision: active.input_revision, proposal_ids: proposalIds, calendar_date: date, period_ids: periodIds, notice_reviewed: noticeReviewed, ambiguities_reviewed: ambiguitiesReviewed };
    void confirmAction.run(() => api<Schema<'ConfirmedInput'>>(`/notice-analyses/${active.id}/confirm`, 'POST', body), () => { setConfirmedAnalysis(active.id); reload(); }, 'Restrictions confirmed. The existing approved plan is retained until a new plan is approved.');
  }
  return <><Heading title="Evidence & restrictions"><ModeSwitch mode={mode} changeMode={changeMode} /></Heading><p className="lead">Official guidance and an unverified notice, reviewed before timetable changes.</p><ResourceState resource={forecast} />{snapshot && <div className="evidence-context"><Mode mode={snapshot.mode} /><span>{snapshot.mode === 'REPLAY' ? 'Fixture timestamp' : 'Retrieved'} {stamp(snapshot.retrieved_at)}</span><span>{snapshot.mode === 'REPLAY' ? 'No model cycle: synthetic fixture' : `Model issue time: ${snapshot.model_issue_time ? stamp(snapshot.model_issue_time) : 'not supplied'}`}</span><small>Selected snapshot <Version value={snapshot.id} /></small></div>}
    <div className="notice warning">Official advisories are not active closure orders. No current legal GRAP stage or closure is verified.</div>
    <div className="evidence-columns"><section><h2>Policy evidence</h2><ResourceState resource={policies} />{policies.value?.map(policy => <article className="policy" key={policy.id}><label className="check-label"><input type="checkbox" checked={selectedPolicies.includes(policy.id)} onChange={() => toggle(selectedPolicies, policy.id, setSelectedPolicies)} /><strong>{policy.title}</strong></label><div className="policy-meta"><span className="badge">{policy.classification === 'ADVISORY' ? 'Official advisory' : 'Internal school policy'}</span><span>{policy.document_date}</span></div><blockquote>{policy.excerpt}</blockquote><p>{policy.reference}</p><p className="muted">{policy.jurisdiction}</p>{policy.source_url.startsWith('https://') && <a href={policy.source_url} target="_blank" rel="noreferrer">Official source document</a>}<details><summary>Citation and document integrity</summary><p>Citation <code>{policy.id}</code></p><p>Verified {stamp(policy.verified_at)}</p><p>{policy.limitation}</p><p>Document SHA-256 <code className="hash">{policy.document_sha256}</code></p><p>Excerpt SHA-256 <code className="hash">{policy.excerpt_sha256}</code></p></details></article>)}</section>
    <section><div className="section-heading"><h2>Notice interpretation</h2><button className="secondary" type="button" onClick={syntheticNotice}><FileText size={16} />Use synthetic notice</button></div><form onSubmit={analyze}><label>Pasted notice <span className="badge">Unverified document</span><textarea maxLength={3000} rows={6} required value={notice} onChange={e => setNotice(e.target.value)} /></label><div className="form-footer"><span className="muted">{notice.length}/3,000 characters · Nova Lite · Daily allowance applies</span><button className="primary" disabled={!snapshot || !usable || !selectedPolicies.length || analyzeAction.busy || confirmAction.busy}><Sparkles size={16} />Interpret notice</button></div></form><ActionNotice action={analyzeAction} /><ResourceState resource={saved} />
    {!active && <Empty>No interpretation selected. No restrictions have been inferred automatically.</Empty>}
    {active && <div className="interpretation"><div className="section-heading"><h3>Proposed interpretation</h3><span className="badge">{active.status}</span></div><p><Mode mode={active.mode} /> · Unverified notice · Administrator review required</p><p className="muted">{active.model} · {active.region} · Input revision <code>{active.input_revision}</code></p><ResourceState resource={bound} />{bound.value && <details><summary>Evidence bound to this interpretation</summary><Provenance evidence={bound.value} /></details>}
      <div className="notice warning"><strong>Review issues and ambiguities</strong><ul>{active.review_reasons.map((reason, i) => <li key={i}>{reason}</li>)}</ul></div>
      {active.interpretation && <><h3>Affected date wording</h3>{active.interpretation.affected_dates.length ? <ul>{active.interpretation.affected_dates.map((d, i) => <li key={i}>{d.raw_text} · {d.start ?? 'Unresolved start'} to {d.end ?? 'Unresolved end'}</li>)}</ul> : <p>No affected date established.</p>}
      <form onSubmit={confirm}><fieldset disabled={confirmAction.busy || !!alreadyConfirmed}><legend>Proposed restrictions</legend>{active.interpretation.proposed_restrictions.map(proposal => {
        const supported = proposal.kind === 'outdoor_prohibited' && proposal.citation_ids.length > 0 && proposal.activity_ids.length > 0;
        return <div className="proposal" key={proposal.id}><label className="check-label"><input type="checkbox" disabled={!supported} checked={proposalIds.includes(proposal.id)} onChange={() => toggle(proposalIds, proposal.id, setProposalIds)} /><strong>{supported ? 'Outdoor spaces unavailable' : 'Unsupported instruction — cannot confirm'}</strong></label><p>Activities: {proposal.activity_ids.join(', ') || 'Not established'}</p><p>Citations: {proposal.citation_ids.join(', ') || 'No supporting citation'}</p></div>;
      })}</fieldset><label>Reviewed calendar date<input type="date" required value={date} onChange={e => setDate(e.target.value)} /></label><fieldset disabled={confirmAction.busy || !!alreadyConfirmed}><legend>Confirmed period scope ({data.confirmed.input.affected_day})</legend><div className="period-checks">{data.confirmed.input.periods.filter(p => p.day === data.confirmed.input.affected_day).map(p => <label className="check-label" key={p.id}><input type="checkbox" checked={periodIds.includes(p.id)} onChange={() => toggle(periodIds, p.id, setPeriodIds)} />Period {p.number}</label>)}</div></fieldset><label className="check-label"><input type="checkbox" checked={noticeReviewed} onChange={e => setNoticeReviewed(e.target.checked)} />Notice source and authenticity reviewed</label><label className="check-label"><input type="checkbox" checked={ambiguitiesReviewed} onChange={e => setAmbiguitiesReviewed(e.target.checked)} />Dates, period scope and ambiguities reviewed</label>
      {!compatible && !alreadyConfirmed && <div className="notice warning">This interpretation must match the pasted notice, selected citations, evidence and current input revision. After a page refresh, paste the original notice again; its text is not saved in the browser.</div>}
      <button className="primary" disabled={!compatible || !usable || !!alreadyConfirmed || active.status !== 'SUCCESS' || !proposalIds.length || !periodIds.length || !date || !noticeReviewed || !ambiguitiesReviewed || confirmAction.busy}><Check size={17} />{alreadyConfirmed ? 'Restrictions confirmed' : 'Confirm reviewed restrictions'}</button></form></>}
      <ActionNotice action={confirmAction} />
    </div>}</section></div>
    <section>
      <h2>Confirmed restrictions</h2><p>Input revision <Version value={data.confirmed.revision} /></p>
      {data.confirmed.evidence_binding && <p><Mode mode={data.confirmed.evidence_binding.mode} /> · Reviewed date {data.confirmed.evidence_binding.calendar_date}</p>}
      {restrictions.length ? <div className="table-scroll"><table><thead><tr><th>Restriction</th><th>Sections</th><th>Periods</th><th>Confirmation</th></tr></thead><tbody>{restrictions.map(r => <tr key={r.id}><td>Outdoor spaces unavailable</td><td>{r.section_ids.join(', ')}</td><td>{r.period_ids.join(', ')}</td><td>Administrator confirmed</td></tr>)}</tbody></table></div> : <Empty>No confirmed outdoor restrictions.</Empty>}
      <a className="next-link" href="#plan">Compare and generate a plan <ArrowRight size={17} /></a>
    </section>
  </>;
}
