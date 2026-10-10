import os
import pytest
from backend.config import Settings
from backend.rag_pipeline import DocumentService
from scripts.fixtures import HANDBOOK, make_pdf


@pytest.mark.local_e2e
@pytest.mark.skipif(os.getenv('RUN_LOCAL_E2E') != '1', reason='Opt in with RUN_LOCAL_E2E=1; requires cached embeddings and Ollama.')
def test_real_local_rag(tmp_path):
    service = DocumentService(Settings(data_dir=tmp_path))
    document = service.ingest('synthetic-handbook.pdf', make_pdf(HANDBOOK))
    result = service.query('How many days of annual leave do Cedar employees receive?', document_ids=[document['id']])
    assert not result['insufficient_evidence'] and '20' in result['answer']
    assert result['citations'] and result['evidence'][0]['page'] == 1
    assert service.query('What is the salary of the president of Mars?')['insufficient_evidence']
