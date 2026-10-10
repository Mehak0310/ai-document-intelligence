from threading import Lock
import numpy as np


def normalize(vectors):
    array = np.asarray(vectors, dtype="float32")
    if array.ndim != 2 or not array.shape[1] or not np.isfinite(array).all():
        raise ValueError("Invalid embedding shape or values.")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Zero embeddings are not supported.")
    return np.ascontiguousarray(array / norms)


class LocalEmbeddings:
    def __init__(self, model_name):
        self.model_name = model_name
        self._model = None
        self._lock = Lock()

    def _load(self):
        if self._model is None:
            from langchain_huggingface import HuggingFaceEmbeddings
            self._model = HuggingFaceEmbeddings(model_name=self.model_name)
        return self._model

    def embed_documents(self, texts):
        with self._lock:
            return normalize(self._load().embed_documents(texts))

    def embed_query(self, text):
        with self._lock:
            return normalize([self._load().embed_query(text)])[0]
