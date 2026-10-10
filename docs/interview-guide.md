# Interview explanation guide

Use this guide with `docs/architecture.md`, `docs/evaluation.md` and the actual source open.
Do not claim production usage, broad accuracy, user counts, speed gains or a project duration.

## 1. What RAG is and why it was chosen

Retrieval-augmented generation finds relevant source text and supplies it to a model at answer time.
Here `DocumentService.query` in `backend/rag_pipeline.py` composes retrieval and Ollama generation.
It lets the local model answer questions about newly uploaded PDFs without retraining. Retrieval
can miss the answer and the generator can still invent claims; RAG is not a correctness guarantee.

**Question:** Why use RAG rather than fine-tuning for this application's changing PDF corpus?

## 2. Embeddings and semantic similarity

`backend/embeddings.py` lazily loads MiniLM via LangChain's Hugging Face integration and normalizes
vectors. The query and document chunks occupy the same embedding space. Meaning-related text can
score similarly without exact keyword overlap; unfamiliar domains and numbers can still be difficult.
The actual cached embedding produced 384 dimensions; normalization rejects zero/nonfinite vectors.

**Question:** What breaks if the query embedding model differs from the indexed document model?

## 3. Chunk size and overlap trade-offs

`backend/ingestion.py` uses LangChain recursive splitting within each PDF page. The default 800/100
configuration retains more surrounding context; small chunks can isolate facts but lose qualifiers.
Overlap duplicates context to reduce boundary loss, increasing embedding/storage cost. Splits use
characters, not tokens, so multilingual text has different token budgets. Page boundaries are preserved.
The real 180/30 experiment created seven chunks rather than four and showed no quality improvement.

**Question:** How would you isolate the effect of overlap in a larger controlled evaluation?

## 4. FAISS and alternative vector databases

`backend/retrieval.py` constructs native `IndexFlatIP` from SQLite vectors. It is an exact in-memory
index, simple for this local corpus. No persisted FAISS or pickle is loaded. SQLite provides transactional
metadata and original bytes. A server vector database can add persistent filtered search, replication
and multi-user operational controls, at the cost of another service and a different privacy boundary.

**Question:** At what corpus size or concurrency would rebuilding FAISS per request become unsuitable?

## 5. Retrieval quality and reranking

Normalized inner product is cosine similarity. The code searches only active selected documents,
returns top-k chunks and filters by a configurable score floor. This threshold is not calibrated confidence.
There is no hybrid retrieval, MMR or reranker. Page-hit checks in the synthetic harness are the baseline
before introducing reranking; more relevant labeled questions are needed to justify complexity.

**Question:** How would you distinguish a retrieval failure from a generation failure?

## 6. Prompt construction and hallucination risks

`backend/prompts.py` serializes question and excerpts as untrusted JSON data, selects one of four
response styles and requests structured output. `backend/generation.py` sends the schema to Ollama
with temperature zero. Prompt text is an instruction, not an access-control boundary. The model may
ignore it, quote an injected instruction or state facts that a cited passage does not entail.

**Question:** Why does temperature zero fail to guarantee factual or reproducible answers?

## 7. Grounding and citation verification

Page numbers, deterministic chunk IDs, exact excerpts and source URLs come from stored records,
not model-generated metadata. `DocumentService.query` accepts only known cited IDs or abstains.
`AnswerCard.tsx` distinguishes cited from merely retrieved evidence and offers an authenticated full-PDF
download. This proves reference integrity; it does not check every claim's semantic entailment.

**Question:** How could you detect an answer with a valid S1 citation but an unsupported numerical claim?

## 8. Ollama versus hosted LLM APIs

The direct `requests.post` adapter calls configured `/api/generate` without agents or orchestration
framework generation chains. Default localhost Ollama keeps document prompts on this machine and
avoids per-request paid API calls. CPU inference can be slow and requires model installation. A hosted
provider changes latency, quality, cost and data handling; it would require an explicit operator decision.

**Question:** Which interfaces and tests would you preserve when adding a second generation provider?

## 9. FastAPI concurrency and async behavior

`backend/main.py` keeps async request handling but delegates blocking CPU/network/storage functions
to a threadpool. A semaphore rejects excess work with 429. `asyncio.shield` and a callback keep capacity
accounting correct when a client stops waiting and consume background errors. SQLite locks coordinate
writers across processes; admission limits and embedding instances remain per process.

**Question:** Why is a browser AbortController insufficient to cancel embedding or Ollama work?

## 10. Document privacy and prompt injection

Legacy private files are untouched; `.gitignore` excludes originals, vectors, metadata, backups and
secrets. New persistence does not deserialize pickle. Optional bearer authentication covers corpus
operations, while binding localhost is the deployment boundary. One synthetic document includes
malicious instructions; its actual returned answer avoided the attack terms. More attacks and
operational isolation are required. There are no execution tools for the model to invoke.

**Question:** Why must an embedding index be excluded from publication even after PDFs are removed?

## 11. Evaluation metrics and experiment results

`scripts/evaluate.py` compares two configurations on eight synthetic cases. Both scored 6/6 retrieval
page hits, 6/6 structural citations/support checks, 5/6 strict answer fact matches and 2/2 abstentions.
The succinct injection answer exposed a lexical proxy limitation. The pilot report is retained and
safety rescoring documented. Deterministic doubles verify wiring, not real-model accuracy. Coverage
measures executed statements, not completeness of all behaviors or model quality.

**Question:** Why is this eight-question result insufficient to claim “100% accurate RAG”?

## 12. Scaling to a production service

This code needs more than deployment: user identity and isolation, ingress limits, parser/worker
sandboxing, hard execution budgets, global admission/rate limits, corpus quotas, encrypted backups,
observability without content leaks, versioned model/index lifecycles and representative evaluation.
FAISS rebuilding and per-process model memory are explicit scaling costs. Archive/reset retains bytes,
so a separately authorized physical erasure policy would also be needed. See `docs/security.md`.

**Question:** What would you implement first if several users needed independent private document stores?
