"""Compare original private artifacts against the ignored pre-upgrade manifest.
Print counts only; never print private paths, hashes, metadata or document contents.
"""
import hashlib
import json
from pathlib import Path


def verify(root=Path(__file__).resolve().parents[1]):
    manifest = json.loads((root/'.local/backups/pre-upgrade/private-integrity.json').read_text())
    unchanged = sum((root/name).is_file() and hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name, digest in manifest.items())
    print(f'Original private artifacts unchanged: {unchanged}/{len(manifest)}')
    return unchanged == len(manifest)


if __name__=='__main__':
    raise SystemExit(0 if verify() else 1)
