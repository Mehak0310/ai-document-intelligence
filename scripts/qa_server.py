"""Explicit browser QA backend: synthetic corpus, deterministic test doubles only."""
from pathlib import Path
from backend.config import Settings
from backend.main import create_app
from backend.rag_pipeline import DocumentService
from tests.fakes import FakeEmbeddings, FakeGenerator

settings = Settings(data_dir=Path(__file__).resolve().parents[1] / '.local' / 'browser-qa-test-doubles', model='qa-test-double', embedding_model='qa-test-double')
app = create_app(settings, DocumentService(settings, FakeEmbeddings(), FakeGenerator()))
