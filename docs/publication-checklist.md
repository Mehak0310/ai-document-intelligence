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

The existing private remote and matching `main` history were verified through GitHub before this check-in. Its preceding workflow run completed successfully. Fresh scans found zero known advisories in all 79 locked Python packages and the full frontend dependency tree. The publication guard scans staged blobs and reachable history; reviewed screenshots and reproducible synthetic PDFs supplement this heuristic scan.

Original private artifacts remain unchanged (15/15 hashes). Earlier commits contain the owner's author email in Git metadata; existing history is preserved, and new commits use the verified account's GitHub noreply address. Licensing must be reviewed before any public release.

