import DOMPurify from 'dompurify';
import { marked } from 'marked';
import type { Answer } from './types';

export function AnswerCard({ result, onSource, disabled }: { result: Answer; onSource: (path: string) => void; disabled: boolean }) {
  const safe = DOMPurify.sanitize(marked.parse(result.answer, { async: false }), {
    ALLOWED_TAGS: ['p', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'code', 'pre', 'br', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'a'],
    ALLOWED_ATTR: ['href', 'title'],
  });
  return <article className="answer-card" aria-label="Document answer">
    <div className="answer-heading"><span className="eyebrow">{result.insufficient_evidence ? 'INSUFFICIENT EVIDENCE' : 'DOCUMENT ANSWER'}</span><span>{result.latency.toFixed(2)}s</span></div>
    <div className="markdown" dangerouslySetInnerHTML={{ __html: safe }} />
    <p className="answer-meta">{result.retrieved_chunks} retrieved chunks · {result.model}</p>
    {result.evidence.length > 0 && <details open><summary>Source evidence ({result.evidence.length})</summary>
      <div className="evidence-list">{result.evidence.map(e => <section key={e.chunk_id} className="evidence">
        <div className="evidence-heading"><strong>[{e.id}] {e.file_name}</strong><span>Page {e.page}{result.citations.includes(e.id) ? ' · cited' : ' · retrieved'}</span></div>
        <blockquote>{e.excerpt}</blockquote>
        <button className="text-button" disabled={disabled} onClick={() => onSource(e.url)}>Download source PDF · page {e.page}</button>
      </section>)}</div>
    </details>}
    <p className="fine-print">Check the supporting excerpts. A valid citation does not guarantee every claim is correct.</p>
  </article>;
}
