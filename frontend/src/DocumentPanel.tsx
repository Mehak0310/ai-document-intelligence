import type { DocumentInfo } from './types';

export function DocumentPanel({ documents, selected, onSelect, onArchive, onReset, busy }: {
  documents: DocumentInfo[]; selected: string[]; onSelect: (id: string) => void;
  onArchive: (id: string) => void; onReset: () => void; busy: boolean;
}) {
  return <section aria-labelledby="documents-heading" className="document-panel">
    <div className="section-heading"><h2 id="documents-heading">Your documents</h2><span className="count">{documents.length}</span></div>
    <p className="hint">Select documents to narrow your question. None selected searches all active documents.</p>
    {!documents.length && <p className="empty-documents">No documents yet. Upload a text-based PDF to begin.</p>}
    <ul className="document-list">{documents.map(d => <li key={d.id}>
      <label className="document-choice"><input type="checkbox" checked={selected.includes(d.id)} disabled={busy} onChange={() => onSelect(d.id)} /><span><strong>{d.file_name}</strong><small>{d.num_chunks} text chunks</small></span></label>
      <button className="text-button danger" disabled={busy} aria-label={`Archive ${d.file_name}`} onClick={() => onArchive(d.id)}>Archive</button>
    </li>)}</ul>
    {!!documents.length && <button className="secondary" disabled={busy} onClick={onReset}>Archive all documents</button>}
    <p className="fine-print">Archiving removes documents from search and retains their bytes for recovery.</p>
  </section>;
}
