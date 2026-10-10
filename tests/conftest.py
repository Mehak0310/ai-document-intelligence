import os
import tempfile
from pathlib import Path
import pytest

# Set before backend.main is imported: even its default app uses a temporary store.
_import_store = tempfile.TemporaryDirectory(prefix='adi-import-')
os.environ['ADI_DATA_DIR'] = _import_store.name

from backend.config import Settings
from backend.rag_pipeline import DocumentService
from scripts.fixtures import HANDBOOK, make_pdf
from tests.fakes import FakeEmbeddings, FakeGenerator


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path, min_score=0.3)


@pytest.fixture
def service(settings):
    return DocumentService(settings, FakeEmbeddings(), FakeGenerator())


@pytest.fixture
def pdf():
    return make_pdf(HANDBOOK)
