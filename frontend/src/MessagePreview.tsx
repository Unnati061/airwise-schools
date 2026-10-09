import { useState } from 'react';
import { Copy, Download } from 'lucide-react';
import type { Schema } from './client';
import { ActionNotice, Mode, useAction, Version } from './ui';

export default function MessagePreview({ preview }: { preview: Schema<'MessagePreview'> }) {
  const [reviewed, setReviewed] = useState(false);
  const action = useAction();
  function download(language: string, text: string) {
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url;
    link.download = `airwise-preview-${preview.plan_version}-${language}.txt`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section><h2>Administrator message previews</h2><div className="notice warning"><strong>Preview only — not sent</strong><p>Verify dates, assignments and both language versions. No message delivery is available.</p></div><p><Mode mode={preview.mode} /> · <Version value={preview.plan_version} /></p>{preview.needs_review && <p role="alert">This approved version needs review. It has not been replaced by a new approval.</p>}<div className="message-columns">{[['English', preview.english, 'en'], ['Hindi', preview.hindi, 'hi']].map(([language, text, code]) => <div key={code}><label>{language} preview<textarea lang={code} readOnly rows={12} value={text} /></label><div className="toolbar"><button className="secondary" disabled={!reviewed || action.busy} onClick={() => void action.run(() => navigator.clipboard.writeText(text), () => {}, `${language} preview copied; not sent.`)}><Copy size={16} />Copy {language}</button><button className="secondary" disabled={!reviewed} onClick={() => download(code, text)}><Download size={16} />Download {language}</button></div></div>)}</div><label className="check-label"><input type="checkbox" checked={reviewed} onChange={e => setReviewed(e.target.checked)} />I reviewed the dates, assignments and both language versions.</label><ActionNotice action={action} /></section>;
}
