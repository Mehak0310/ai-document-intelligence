"""Read-only publication guard. Reports paths and rule names, never matched values.

This heuristic guard supplements provenance and visual review; it is not proof
that arbitrary text or images contain no confidential information.
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDFS = {'examples/cedar-handbook.pdf', 'examples/harbor-support.pdf',
        'examples/adversarial-test.pdf'}
IMAGES = {'docs/screenshots/synthetic-desktop.png',
          'docs/screenshots/synthetic-mobile-dark.png'}
RULES = {
    'private-key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'provider-token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16})\b',
    'personal-path': rb'(?:[A-Z]:[\\/]+Users[\\/]+[^\s"\']+|/ho' + rb'me/[^\s/]+/)',
    'email-address': rb'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    'credential-url': rb'https?://[^\s/:]+:[^\s/@]+@[A-Za-z0-9]',
    'literal-secret': rb'(?i)(?:api_key|password|secret|access_token)\s*[:=]\s*["\'][A-Za-z0-9_+/=-]{20,}["\']',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def scan(path, data):
    findings = []
    parts = Path(path).parts
    if (any(p in {'.local', '.venv', 'node_modules', 'data', '__pycache__',
                  'dist', 'test-results', 'playwright-report', '.aws', '.codex'} for p in parts)
            or Path(path).suffix.lower() in {'.db', '.pkl', '.pickle', '.faiss', '.docx', '.log', '.key', '.pem', '.pfx', '.p12'}
            or '.sqlite' in path or (Path(path).name.startswith('.env') and path != '.env.example')):
        findings.append('protected-artifact')
    if path.endswith('.pdf'):
        from scripts.fixtures import make_pdf, HANDBOOK, SUPPORT, INJECTION
        expected = dict(zip(sorted(PDFS), [make_pdf(INJECTION), make_pdf(HANDBOOK), make_pdf(SUPPORT)]))
        if path not in expected or data != expected[path]:
            findings.append('non-synthetic-pdf')
    elif b'\x00' in data or path in IMAGES:
        if path not in IMAGES or data != (ROOT / path).read_bytes():
            findings.append('unreviewed-binary')
    else:
        findings += [name for name, pattern in RULES.items() if re.search(pattern, data)]
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--staged', action='store_true')
    group.add_argument('--history', action='store_true')
    args = parser.parse_args()
    revisions = git('rev-list', '--all').decode().splitlines() if args.history else [None]
    seen, findings = set(), []
    for rev in revisions:
        listing = git('ls-tree', '-rz', rev) if rev else git('ls-files', '--stage', '-z')
        for item in listing.split(b'\x00'):
            if not item:
                continue
            metadata, raw_path = item.split(b'\t', 1)
            path = raw_path.decode('utf-8')
            fields = metadata.decode().split()
            oid = fields[2] if rev else fields[1]
            key = (path, oid)
            if key in seen:
                continue
            seen.add(key)
            data = git('cat-file', 'blob', oid) if (rev or args.staged) else (ROOT / path).read_bytes()
            findings.extend((path, rule) for rule in scan(path, data))
    for path, rule in findings:
        print(f'{path}: {rule} (value redacted)')
    print(f'Publication scan: {len(seen)} file versions; {len(findings)} findings')
    return bool(findings)


if __name__ == '__main__':
    raise SystemExit(main())
