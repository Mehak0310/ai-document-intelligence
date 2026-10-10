# GitHub publication checklist — owner review required

No Git repository was initialized, pushed, published or submitted as a PR in this assignment.

- [ ] Prefer a fresh sanitized staging directory; copy only source, manifests, tests, scripts,
  `.github/`, documentation and the three named synthetic examples.
- [ ] Exclude `.local/`, `backend/data/`, root `data/`, every SQLite/index/pickle file, environments,
  dependencies, caches, logs, secret files, and all other PDFs/DOCX. `.gitignore` is not a backup
  policy and does not remove files that were already tracked elsewhere.
- [ ] Inspect actual staged files before any commit. Do not blindly add the entire working directory.
- [ ] Review screenshots and evaluation reports: only synthetic text should appear.
- [ ] Run a secret scanner and a dependency advisory check against the sanitized tree.
- [ ] Verify a clean environment can install pinned dependencies and run deterministic CI locally.
- [ ] Confirm licensing rights and choose a license before publication. No license was assigned
  automatically to the owner's existing code.
- [ ] Confirm the integrity check still reports all original artifacts unchanged.
- [ ] Read security limitations; do not advertise production readiness, general accuracy, measured
  speed improvements, users, commercial usage or a fabricated project duration.
- [ ] Use only resume claims supported in `docs/resume-evidence.md`.
- [ ] Obtain explicit owner approval before repository creation, GitHub push, public hosting or PR.

CI is provided but has not been executed on GitHub because publication was not authorized.
