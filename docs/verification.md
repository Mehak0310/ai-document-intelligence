# Verification report

Checks ran locally on Windows using the isolated Python 3.11.17 project environment and Node 22.16.0.
The original global Anaconda environment was not upgraded. A project-local runtime and `.venv`
were created without PATH/registry changes. Network-approved downloads installed dependencies and
Chromium; no paid API, private document generation, public hosting or pull request was used.

| Check | Actual result |
|---|---|
| Deterministic Python suite | 40 passed; one real-model test skipped by default |
| Active backend statement coverage | 364/364 statements, 100% |
| Backend plus utility-script coverage | 464/483 statements, 96.07%; exceeds 90% gate |
| Clean lightweight Python environment | Deterministic tests passed without Torch or model downloads |
| Frontend component tests | 9 passed |
| TypeScript and production Vite build | Passed |
| Frontend lockfile installation | `npm ci` passed |
| Chromium synthetic workflows | 3 passed |
| Automated accessibility | Zero axe violations in tested mobile light/dark states |
| Responsive styling | Styled page and dark theme asserted; no horizontal overflow at 375px |
| Source download | Browser downloaded original PDF bytes; `%PDF-` signature verified |
| Separate real Ollama end-to-end test | 1 passed on the final Python 3.11 stack |
| Real evaluation | 16 cases across two configurations, zero generation errors; see evaluation report |
| Dependency consistency | `pip check`: no broken requirements |
| Resolved backend/test advisory scan | 79 resolved dependencies; zero known advisories in the final snapshot |
| Frontend advisory scan | Zero known advisories in the audited lockfile tree |
| Original private artifact integrity | 15/15 unchanged against the pre-upgrade manifest |

The real-model end-to-end test passed separately and remains opt-in for future runs.
Raw coverage/advisory outputs are kept in ignored `.local/`; public evaluation reports contain only
synthetic content. The Windows dependency snapshot is `requirements-lock-windows-py311.txt`.
GitHub Actions is configured but has not run remotely; Linux/other browsers are not locally verified.
No license was assigned automatically to the owner's original code.

## What the tests establish

Backend tests parse actual synthetic PDFs, use native FAISS and SQLite, and replace embeddings/Ollama
with explicit doubles. They exercise malformed/encrypted/empty/oversized input, page metadata,
duplicates including concurrent races, rollback, persistence/restore, document-scoped retrieval,
valid/invalid citations, abstention, operational failures, authentication/origin checks, API contracts,
capacity rejection, and cancellation while a worker remains active. Utility tests verify synthetic
fixture generation and integrity checking against an invented artifact, never the original corpus.

Frontend tests verify safe Markdown, document actions, loading/error states, guarded submits,
selection payloads, cancellation/timeouts, themes and token header behavior. Browser workflows cover
upload, query, scope selection, evidence, source downloads, duplicates, archive/reset, unanswerable
questions, failures and cancellation. Screenshot answers come from a backend explicitly labeled
`qa-test-double`; screenshots are UI evidence, not real-model quality or latency measurements.

Coverage counts executed statements, not exhaustive path coverage or model reliability. Utility-script
coverage gaps include standalone CLI guards, the QA launcher (exercised in a separate browser process),
and real/error evaluation branches (some exercised outside the deterministic coverage process).
The coverage scope excludes only three unchanged/unintegrated legacy backend helpers.

## Problems found and corrected during verification

- Playwright/axe initially resolved different core versions; exact compatible versions now align.
- A headless PDF preview test stayed blank. Source interaction now downloads authenticated PDF bytes
  instead of depending on an embedded browser PDF viewer.
- Vite-injected styles were blocked by CSP in development. A development-only policy adjustment fixes
  this; the production policy stays strict. Browser tests now assert actual styled rendering.
- Advisory scans found affected initial frontend and backend pins, then transitive Starlette/pytest
  issues. Patched compatible versions were installed and verified in a fresh Python 3.11 environment.
- The injection case returned a correct terse answer that failed strict lexical completeness. The
  failure is retained; safety and task completeness are measured separately. Original pilot output
  and the pre-patch runtime evaluation are preserved for inspection.

Remaining limitations and public-deployment requirements are in `docs/security.md`. The test results
do not establish production readiness, complete WCAG compliance, general injection resistance, or
general RAG accuracy.

