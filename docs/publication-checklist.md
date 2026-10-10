# GitHub publication checklist

Owner authorization was provided for a private repository check-in. No public release or pull request is authorized.

- [x] Stage only source, manifests, tests, scripts,
  `.github/`, documentation and the three named synthetic examples.
- [x] Exclude `.local/`, `backend/data/`, root `data/`, every SQLite/index/pickle file, environments,
  dependencies, caches, logs, secret files, and all other PDFs/DOCX. `.gitignore` is not a backup
  policy and does not remove files that were already tracked elsewhere.
- [x] Inspect actual staged files before any commit. Do not blindly add the entire working directory.
- [x] Review screenshots and evaluation reports: only synthetic text should appear.
- [x] Run a secret scanner and a dependency advisory check against the sanitized tree.
- [x] Verify the project environment can install pinned dependencies and run deterministic CI locally.
- [ ] Confirm licensing rights and choose a license before publication. No license was assigned
  automatically to the owner's existing code.
- [x] Confirm the integrity check still reports all original artifacts unchanged.
- [x] Read security limitations; do not advertise production readiness, general accuracy, measured
  speed improvements, users, commercial usage or a fabricated project duration.
- [x] Use only resume claims supported in `docs/resume-evidence.md`.
- [x] Obtain explicit owner approval before repository creation, GitHub push, public hosting or PR.

CI is configured and will run after the first private push. Python advisory tooling was not installed during this check-in; the existing resolved advisory report remains part of the reviewed tree.

