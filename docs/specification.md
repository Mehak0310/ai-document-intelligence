# Upgrade specification and acceptance evidence

Scope: a single-user, localhost portfolio application. Preserve the original corpus and index;
never use them in tests, evaluation, screenshots or public artifacts. No paid generation,
repository initialization, publication, push or PR is part of this assignment.

## Requirements

| Requirement | Design | Verification |
|---|---|---|
| Preserve private data | Ignored pre-upgrade snapshot; untouched legacy paths; separate v2 store | `scripts/verify_private_integrity.py` |
| Safe ingestion | PDF header/extension/size checks, encrypted/empty rejection, chunk limit | PDF parser and API tests |
| Idempotence | SHA-256 PDF identity; transactional unique document/chunk IDs | Duplicate and concurrent ingestion tests |
| Recoverable updates | SQLite transactions, WAL, retained PDF bytes and chunk vectors | Rollback, integrity, archive/restore tests |
| Avoid pickle execution | No disk-loaded FAISS/pickle; float32 vectors in SQLite | Native in-memory FAISS code and retrieval tests |
| Responsive backend | Threadpool offload; bounded work admission; finite generation timeout | Capacity, failure and cancellation tests |
| Scoped retrieval | Select corpus before constructing FAISS index | Scope isolation tests and evaluation case |
| Verifiable citations | Stable chunk ID, original page, exact excerpt, source PDF endpoint | Page, excerpt and citation ID checks |
| Consistent abstention | Score gate plus structured model output; reject invalid citation IDs | Empty/unanswerable/malformed-output tests |
| Frontend architecture | React/TypeScript, separate document/evidence components and request helpers | Component tests, strict typecheck and build |
| Safe interaction | Synchronous submission guard, AbortController, timeout, archive confirmation | Component and browser tests |
| Accessibility | Explicit labels, landmarks, live status, responsive layout, visible focus | Browser axe checks plus manual screenshot review |
| Measured quality | Eight synthetic cases; two retrieval configurations; separate doubles/real reports | `scripts/evaluate.py` and results JSON |
| Portfolio evidence | Technical docs, interview guide, screenshots, supported resume claims | Documentation and publication checklist |

## Deliberate boundaries

Archive/reset is logical removal from search, not erasure. Original files and retained records are
never deleted. Re-uploading identical archived bytes reactivates the existing record. To change
embedding model, choose a fresh data directory and re-upload; no automatic legacy migration or
unsafe pickle import is performed. Existing private PDFs can be manually re-uploaded by the owner
outside demonstrations if desired.

No OCR, DOCX, streaming, conversational memory, reranking, LangGraph, MCP or agents are claimed.
Citation ID integrity does not prove semantic entailment. The evaluation is intentionally small.
