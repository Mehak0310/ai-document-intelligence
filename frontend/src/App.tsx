import { useEffect, useRef, useState } from 'react';
import { AnswerCard } from './AnswerCard';
import { DocumentPanel } from './DocumentPanel';
import { createRequest, errorMessage, downloadSource, request } from './api';
import type { Answer, DocumentInfo, Message, Style } from './types';

export default function App() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [style, setStyle] = useState<Style>('simple');
  const [file, setFile] = useState<File | null>(null);
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('Connecting to your local backend…');
  const [busy, setBusy] = useState(false);
  const [dark, setDark] = useState(localStorage.getItem('theme') === 'dark');
  const active = useRef<ReturnType<typeof createRequest> | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const sequence = useRef(0);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  async function refresh(signal: AbortSignal) {
    const data = await request<{ documents: DocumentInfo[] }>('/documents', token, { signal });
    setDocuments(data.documents);
    setSelected(ids => ids.filter(id => data.documents.some(d => d.id === id)));
    return data.documents.length;
  }

  useEffect(() => {
    const job = createRequest();
    active.current = job;
    setBusy(true);
    refresh(job.controller.signal).then(count => setStatus(count ? 'Ready to explore your documents.' : 'Backend ready. Upload a PDF to get started.'))
      .catch(error => setStatus(errorMessage(error))).finally(() => { job.finish(); active.current = null; setBusy(false); });
    return () => { job.controller.abort(); job.finish(); };
  }, []);

  async function run(operation: (signal: AbortSignal) => Promise<void>) {
    if (active.current) return;
    const job = createRequest();
    active.current = job;
    setBusy(true);
    try { await operation(job.controller.signal); }
    catch (error) { setStatus(errorMessage(error)); }
    finally { job.finish(); active.current = null; setBusy(false); }
  }

  async function upload() {
    if (!file || active.current) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) { setStatus('Choose a PDF file.'); return; }
    await run(async signal => {
      setStatus('Uploading and indexing your PDF…');
      const body = new FormData(); body.append('file', file);
      const data = await request<DocumentInfo & { duplicate: boolean }>('/upload', token, { method: 'POST', body, signal });
      await refresh(signal);
      setStatus(data.duplicate ? 'This PDF is already indexed; no duplicate was added.' : `Indexed ${data.file_name} · ${data.num_chunks} chunks.`);
      setFile(null); if (fileInput.current) fileInput.current.value = '';
    });
  }

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    if (active.current || !question.trim() || !documents.length) return;
    const id = ++sequence.current;
    const q = question.trim();
    setMessages(previous => [...previous, { id, question: q }]); setQuestion('');
    await run(async signal => {
      setStatus('Finding evidence and preparing an answer…');
      try {
        const result = await request<Answer>('/query', token, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q, prompt_type: style, document_ids: selected }), signal });
        setMessages(previous => previous.map(m => m.id === id ? { ...m, result } : m));
        setStatus(result.insufficient_evidence ? 'The documents do not provide enough evidence.' : 'Answer ready. Review its source evidence.');
      } catch (error) {
        setMessages(previous => previous.map(m => m.id === id ? { ...m, error: errorMessage(error) } : m));
        throw error;
      }
    });
  }

  function archive(id: string) {
    if (!window.confirm('Archive this document? It will leave search; its bytes will be retained.')) return;
    void run(async signal => { await request(`/documents/${id}`, token, { method: 'DELETE', signal }); await refresh(signal); setStatus('Document archived.'); });
  }

  function reset() {
    if (!window.confirm('Archive all active documents? Their bytes will be retained.')) return;
    void run(async signal => { await request('/documents/reset', token, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm: 'ARCHIVE ALL' }), signal }); await refresh(signal); setStatus('All documents archived.'); });
  }

  return <div className="app-shell">
    <header className="app-header"><a className="brand" href="#main"><span className="brand-mark" aria-hidden="true">DI</span><span>Document Intelligence<small>Evidence-led answers, on your machine</small></span></a><button className="secondary" aria-label="Toggle dark mode" aria-pressed={dark} onClick={() => setDark(value => !value)}>{dark ? 'Light mode' : 'Dark mode'}</button></header>
    <main id="main" className="workspace">
      <aside className="sidebar" aria-label="Document workspace">
        <section className="upload-panel"><span className="eyebrow">LOCAL WORKSPACE</span><h1>Turn documents into answers.</h1><p className="hint">Upload a PDF, ask a question, and inspect the evidence behind each response.</p>
          <label htmlFor="pdf-file">Text-based PDF</label><input ref={fileInput} id="pdf-file" type="file" accept=".pdf,application/pdf" disabled={busy} onChange={e => setFile(e.target.files?.[0] || null)} />
          <button className="primary full-width" disabled={busy || !file} onClick={() => void upload()}>Upload PDF</button>
          <p className="fine-print">Up to 25 MB by default. Scanned and encrypted PDFs are unsupported.</p>
        </section>
        <DocumentPanel documents={documents} selected={selected} busy={busy} onSelect={id => setSelected(ids => ids.includes(id) ? ids.filter(x => x !== id) : [...ids, id])} onArchive={archive} onReset={reset} />
        <details className="connection"><summary>Connection settings</summary><label htmlFor="token">Optional API token</label><input id="token" type="password" autoComplete="off" value={token} disabled={busy} onChange={e => setToken(e.target.value)} /><button className="secondary" disabled={busy} onClick={() => void run(async signal => { await refresh(signal); setStatus('Connected.'); })}>Reconnect</button><p className="fine-print">Token stays in memory. Bind the backend to localhost.</p></details>
      </aside>
      <section className="conversation" aria-labelledby="conversation-heading"><div className="conversation-header"><div><span className="eyebrow">ASK YOUR DOCUMENTS</span><h2 id="conversation-heading">Find clarity in the details.</h2></div><span className="local-badge">Local inference</span></div>
        <div className="status-row"><p role="status" aria-live="polite">{status}</p>{busy && <button className="text-button" onClick={() => active.current?.controller.abort()}>Cancel request</button>}</div>
        <div className="messages" role="log" aria-label="Question and answer history" aria-live="polite" aria-busy={busy}>
          {!messages.length && <div className="welcome"><span className="welcome-icon" aria-hidden="true">↗</span><h3>Your next insight starts with a question.</h3><p>Try the synthetic handbook in <code>examples/</code>, then ask: “How many days of leave are available?”</p><p className="fine-print">Each question is independent. Earlier messages are not sent to the model.</p></div>}
          {messages.map(message => <div className="exchange" key={message.id}><p className="question"><span className="eyebrow">YOU ASKED</span>{message.question}</p>{message.result && <AnswerCard result={message.result} disabled={busy} onSource={path => void run(signal => downloadSource(path, token, signal))} />}{message.error && <p className="error" role="alert">{message.error}</p>}{!message.result && !message.error && <p className="thinking">Retrieving evidence…</p>}</div>)}
        </div>
        <form className="composer" onSubmit={event => void ask(event)}><label htmlFor="question">Your question</label><div className="question-controls"><input id="question" maxLength={2000} value={question} disabled={busy} placeholder="What would you like to know?" onChange={e => setQuestion(e.target.value)} /><button className="primary" type="submit" disabled={busy || !question.trim() || !documents.length}>Ask question</button></div><div className="composer-footer"><label htmlFor="style">Response style</label><select id="style" value={style} disabled={busy} onChange={e => setStyle(e.target.value as Style)}><option value="simple">Simple</option><option value="bullet">Bullet</option><option value="detailed">Detailed</option><option value="analytical">Analytical</option></select><span>{selected.length ? `${selected.length} selected` : 'All active documents'}</span></div></form>
      </section>
    </main><footer className="app-footer">Generated answers can be wrong. Verify important claims against the original document.</footer>
  </div>;
}
