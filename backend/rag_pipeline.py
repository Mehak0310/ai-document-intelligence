"""Application service composing ingestion, persistence, retrieval and generation."""
import hashlib
import time
from .embeddings import LocalEmbeddings, normalize
from .errors import AppError
from .generation import OllamaGenerator
from .ingestion import parse_chunks, validate_pdf
from .prompts import ABSTENTION, get_prompt
from .retrieval import retrieve
from .storage import Store


class DocumentService:
    def __init__(self, settings, embeddings=None, generator=None, store=None):
        self.settings = settings
        self.embeddings = embeddings if embeddings is not None else LocalEmbeddings(settings.embedding_model)
        self.generator = generator if generator is not None else OllamaGenerator(settings)
        self.store = store if store is not None else Store(settings.data_dir)

    def ingest(self, filename, contents):
        name = validate_pdf(filename, contents, self.settings.max_upload_bytes)
        document_id = hashlib.sha256(contents).hexdigest()
        existing = self.store.existing(document_id)
        if existing and existing["active"]:
            item = next(d for d in self.store.list_documents() if d["id"] == document_id)
            return {**item, "duplicate": True, "index_available": True}
        chunks = parse_chunks(contents, document_id, self.settings)
        try:
            vectors = normalize(self.embeddings.embed_documents([c["text"] for c in chunks]))
        except Exception as exc:
            raise AppError("Embedding initialization or indexing failed. Check the local embedding model.", 503) from exc
        duplicate = self.store.add(document_id, name, contents, chunks, vectors, self.settings.embedding_model)
        item = next(d for d in self.store.list_documents() if d["id"] == document_id)
        return {**item, "duplicate": duplicate, "index_available": True}

    def query(self, question, prompt_type="simple", model=None, document_ids=None):
        start = time.perf_counter()
        evidence = retrieve(self.store, self.embeddings, question, document_ids, self.settings)
        model_name = model or self.settings.model
        result = {"answer": ABSTENTION, "sources": [], "citations": [], "evidence": evidence, "insufficient_evidence": True, "retrieved_chunks": len(evidence), "model": model_name}
        if evidence:
            generated = self.generator.generate(get_prompt(prompt_type, question, evidence), model_name)
            ids, answer = generated.get("citations"), generated.get("answer")
            allowed = {e["id"] for e in evidence}
            valid = isinstance(ids, list) and bool(ids) and all(isinstance(i, str) and i in allowed for i in ids)
            if generated.get("insufficient_evidence") is False and valid and isinstance(answer, str) and answer.strip():
                citations = list(dict.fromkeys(ids))
                result.update(answer=answer.strip() + "\n\n" + " ".join(f"[{i}]" for i in citations), citations=citations, insufficient_evidence=False, sources=sorted({e["file_name"] for e in evidence if e["id"] in citations}))
        result["latency"] = round(time.perf_counter() - start, 3)
        return result
