import hashlib
import json

from scripts.fixtures import write_examples
from scripts.verify_private_integrity import verify


def test_fixture_generation_and_integrity_guard_use_only_synthetic_files(tmp_path, capsys):
    examples = tmp_path/'examples'
    write_examples(examples)
    assert len(list(examples.glob('*.pdf'))) == 3
    assert all(p.read_bytes().startswith(b'%PDF-') for p in examples.glob('*.pdf'))
    synthetic = tmp_path/'invented.txt'
    synthetic.write_text('Synthetic private-artifact stand-in.')
    backup = tmp_path/'.local/backups/pre-upgrade'
    backup.mkdir(parents=True)
    manifest = {'invented.txt': hashlib.sha256(synthetic.read_bytes()).hexdigest()}
    (backup/'private-integrity.json').write_text(json.dumps(manifest))
    assert verify(tmp_path)
    synthetic.write_text('Synthetic changed bytes.')
    assert not verify(tmp_path)
    assert 'invented.txt' not in capsys.readouterr().out
