# Project agent instructions

Work incrementally and protect local document data.

- Read the relevant specification and changed files before editing.
- Implement the smallest coherent change, then run focused tests.
- Run the full backend, frontend, production-build, and Playwright suites when the change can affect their behavior.
- Use Playwright Test for repeatable browser regression. Use interactive browser exploration only to investigate a failure.
- Browser tests, evaluations, examples, screenshots, and committed reports must use synthetic documents only.
- Never read, stage, copy, summarize, or publish files under `backend/data/`, `data/`, or `.local/`. Never commit databases, vector indexes, logs, caches, environments, `.env` files, credentials, or private documents.
- Before every commit, inspect `git status --short`, `git diff --cached --name-only`, and `git check-ignore` for protected paths. Run a value-redacting secret scan against staged files.
- Never force-push, rewrite remote history, create a pull request, or make the repository public without explicit user authorization.
- Record milestone results in `artifacts/milestone-summary.json`. Keep it compact and omit secrets, personal filesystem paths, resume/document contents, and raw logs.

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
