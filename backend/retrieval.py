import faiss
import numpy as np
from .embeddings import normalize
from .errors import AppError


def retrieve(store, embeddings, query, document_ids, settings):
    rows = store.chunks(document_ids, settings.embedding_model)
    if not rows:
        return []
    try:
        matrix = normalize(np.stack([np.frombuffer(row["vector"], dtype="float32") for row in rows]))
        vector = normalize([embeddings.embed_query(query)])
        if matrix.shape[1] != vector.shape[1]:
            raise ValueError("Embedding dimensions differ.")
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        scores, positions = index.search(vector, min(settings.top_k, len(rows)))
    except Exception as exc:
        raise AppError("Retrieval is unavailable. Check embedding configuration and storage.", 503) from exc
    evidence = []
    for score, position in zip(scores[0], positions[0]):
        if float(score) < settings.min_score:
            continue
        row = rows[int(position)]
        evidence.append({"id": f"S{len(evidence) + 1}", "document_id": row["document_id"], "chunk_id": row["id"], "file_name": row["name"], "page": row["page"], "excerpt": row["text"], "score": round(float(score), 4), "url": f"/documents/{row['document_id']}/source#page={row['page']}"})
    return evidence
