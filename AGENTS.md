# Project agent instructions

Work incrementally and protect local document data.

- Read the relevant specification and changed files before editing.
- Implement the smallest coherent change, then run focused tests.
- Run the full backend, frontend, production-build, and Playwright suites when the change can affect their behavior.
- Use Playwright Test for repeatable browser regression. Use interactive browser exploration only to investigate a failure.
- Browser tests, evaluations, examples, screenshots, and committed reports must use synthetic documents only.
- Never inspect private document contents, stage, copy, summarize, or publish files under `backend/data/`, `data/`, or `.local/`. The integrity verifier may hash original artifacts and read its ignored manifest; verification tools may read their own ignored reports and dependencies. Print only aggregate integrity results. Never commit databases, vector indexes, logs, caches, environments, `.env` files, credentials, or private documents.
- Before every commit, inspect `git status --short`, `git diff --cached --name-only`, and `git check-ignore` for protected paths. Run `python -m scripts.publication_audit --staged` and `python -m scripts.publication_audit --history`. These checks redact values and fail on suspicious content; review any finding before committing.
- Never force-push, rewrite remote history, create a pull request, or make the repository public without explicit user authorization.
- Record milestone results in `artifacts/milestone-summary.json`. Keep it compact and omit secrets, personal filesystem paths, resume/document contents, and raw logs.
- Use existing dependencies; do not install or upgrade them unless the task requires it. Run independent checks concurrently where safe. Avoid repeated full scans and unnecessary sub-agents.
- Record unexecuted checks as unexecuted, never passed. `commit_sha` records the verified implementation checkpoint; a subsequent report-only commit may contain this summary. Verify the final pushed tip separately with GitHub before reporting success.

The milestone summary schema is:

```json
{
  "milestone": "identifier",
  "status": "passed|failed|partial",
  "changed_files": [],
  "tests": {},
  "coverage": {},
  "browser_qa": {},
  "evaluation_metrics": {},
  "security_findings": [],
  "outstanding_issues": [],
  "commit_sha": null
}
```
