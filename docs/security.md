# Security boundaries and data protection

## Private data preservation

Before source changes, `.gitignore` was added and an ignored snapshot of the original code and data
was created at `.local/backups/pre-upgrade/`. Its private-integrity manifest records hashes locally;
neither paths nor hashes belong in public reports. Original private data remains at its original
locations. The new store defaults to `backend/data/v2/` and does not read the legacy documents or
FAISS/pickle files. Test stores use temporary directories; browser QA and evaluation use `.local/`.

The corpus contains sensitive personal document categories, including financial, health, travel,
resume and agreement records. No document content was extracted for this upgrade. Integrity checks
hash file bytes only. Original inputs, their indexes, extracted text, vectors, backups, logs, secret
configuration and bytecode are excluded from publication. Only three named generated PDFs are
allowlisted. Every PDF in `examples/` is invented and reproducible from `scripts/fixtures.py`.

The backup is on the same disk: it helps recover accidental edits but is not an off-device backup.
Before further work, the owner should keep an encrypted off-device copy and verify restoreability.
For an app database backup, stop the server before copying the SQLite directory, including WAL/SHM
files; a live backup should use SQLite's backup API. Never load a third-party pickle index.

## Implemented controls

- Bounded uploads, content-header checks, page-preserving parser, no filesystem use of upload names.
- Parameterized SQL, atomic updates, deterministic content identity, non-executable vector storage.
- Optional `ADI_API_TOKEN` on document, upload, query, archive/reset and source endpoints.
- Explicit browser origin checks in addition to CORS; secret comparison uses constant-time comparison.
- Request validation returns generic messages without echoing inputs. Operational failures expose
  safe messages; application logs contain only exception type, not content or exception strings.
- Bounded active work, Ollama timeouts, Markdown allowlist sanitization, local CSP, no remote images,
  `nosniff`, `no-store`, `no-referrer`, and frame denial for API responses.
- Archive and reset are controlled logical removals; no deletion of user files or retained PDF bytes.

## Remaining risks

- Without a configured token, any process able to reach localhost can query the active corpus.
  A single token does not provide per-user identity, tenant isolation or audit trails.
- Local storage and backup are plaintext; OS permissions and disk encryption are the boundary.
  Archive is not privacy erasure. Secure physical purge is intentionally outside this assignment.
- CORS/origin checks do not protect against non-browser clients. Bind to `127.0.0.1`, not `0.0.0.0`.
  Reverse-proxy TLS, host validation, authentication, quotas, per-user rate limits and isolation are
  required before considering public deployment. Health/OpenAPI reveal limited service metadata.
- The application limit is checked after multipart handling. A malicious upload can still consume
  spool space before the check; a proxy/body limit and parser/worker isolation are required publicly.
- PDF parsing and embedding have no hard process time/memory limits. A chunk cap is not a full
  resource-exhaustion defense. SQLite capacity and corpus size are not quota-limited.
- Prompt boundaries and one tested injection fixture do not prove resistance to adversarial inputs.
  Valid citations can accompany unsupported statements; inspect excerpts and evaluate broader data.
- Ollama URL is operator-controlled; a remote configured URL would send evidence to that service.
  No hosted API or paid API was used. Initial uncached embeddings require a Hugging Face download.
- The semaphore and embedding model instance are per worker. More workers multiply capacity and
  model memory; SQLite coordinates writes but does not implement a global rate limiter.
- Dependency auditing is a snapshot, not a guarantee. Update pins deliberately and rerun all checks.
  Browser accessibility automation does not establish complete WCAG compliance.

Final scans reported zero known advisories in the resolved Python environment and frontend lockfile
tree. This required a compatible Python 3.11 environment and patched library pins; do not launch the
upgraded application using the unchanged original Python 3.9 dependency environment. See the verified
Windows lock snapshot and `docs/verification.md`. Patched package requirements can be inspected in
[LangChain's package metadata](https://pypi.org/project/langchain-core/1.6.9/) and
[Sentence Transformers package metadata](https://pypi.org/project/sentence-transformers/5.6.0/).

## Recovery

Re-uploading identical archived bytes reactivates their record. There is no unauthenticated archive
restore endpoint. A new data directory and re-upload rebuild a damaged or model-incompatible corpus.
Never overwrite or delete the original private files or legacy index as an automatic migration step.
