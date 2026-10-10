"""Synthetic publication failures must block check-in without exposing values."""
import sys

import pytest

from scripts import publication_audit as audit
from scripts.fixtures import make_pdf, HANDBOOK


@pytest.mark.parametrize('path,data,rule', [
    ('backend/data/item.txt', b'invented', 'protected-artifact'),
    ('local.faiss', b'invented', 'protected-artifact'),
    ('examples/private.pdf', b'invented', 'non-synthetic-pdf'),
    ('unknown.bin', b'\x00', 'unreviewed-binary'),
    ('text.txt', b'ghp_' + b'A' * 36, 'provider-token'),
    ('text.txt', b'-----BEGIN ' + b'PRIVATE KEY-----', 'private-key'),
    ('text.txt', b'https://user:synthetic@' + b'example.test', 'credential-url'),
    ('text.txt', b'person@' + b'example.test', 'email-address'),
    ('text.txt', b'C:/' + b'Users/Synthetic/private', 'personal-path'),
    ('text.txt', b'password="' + b'A' * 24 + b'"', 'literal-secret'),
])
def test_rejects_sensitive_candidates(path, data, rule):
    assert rule in audit.scan(path, data)


def test_reproducible_pdf_and_reviewed_image(tmp_path, monkeypatch):
    assert audit.scan('examples/cedar-handbook.pdf', make_pdf(HANDBOOK)) == []
    path = next(iter(audit.IMAGES))
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_bytes(b'\x00synthetic image')
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    assert audit.scan(path, target.read_bytes()) == []
    assert audit.scan(path, b'changed') == ['unreviewed-binary']


@pytest.mark.parametrize('mode', ['--staged', '--history', None])
def test_scan_modes_redact_and_deduplicate(mode, tmp_path, monkeypatch, capsys):
    secret = b'ghp_' + b'A' * 36
    (tmp_path / 'synthetic.txt').write_bytes(secret)
    calls = []

    def fake_git(*args):
        calls.append(args)
        if args[0] == 'rev-list':
            return b'first\nsecond\n'
        if args[0] == 'ls-tree':
            return b'100644 blob object\tsynthetic.txt\x00'
        if args[0] == 'ls-files':
            return b'100644 object 0\tsynthetic.txt\x00'
        return secret

    monkeypatch.setattr(audit, 'git', fake_git)
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['publication_audit'] + ([mode] if mode else []))
    assert audit.main() is True
    output = capsys.readouterr().out
    assert secret.decode() not in output
    assert '1 file versions; 1 findings' in output
    assert any(c[0] == 'cat-file' for c in calls) is (mode is not None)


def test_git_reads_only(monkeypatch):
    captured = []
    monkeypatch.setattr(audit.subprocess, 'check_output', lambda args, **kw: captured.append(args) or b'ok')
    assert audit.git('ls-files') == b'ok'
    assert captured == [['git', 'ls-files']]
