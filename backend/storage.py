"""Transactional SQLite authority. PDF bytes retained; delete/reset only archive.
No persisted FAISS binary or pickle is ever loaded. Connections are per operation.
"""
import sqlite3
from contextlib import contextmanager
from .errors import AppError


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "documents.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, pdf BLOB NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1, model TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
                    page INTEGER NOT NULL, text TEXT NOT NULL, vector BLOB NOT NULL
                );
                CREATE INDEX IF NOT EXISTS chunk_document ON chunks(document_id);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def existing(self, document_id):
        with self.connect() as db:
            row = db.execute("SELECT id,name,active FROM documents WHERE id=?", (document_id,)).fetchone()
            return dict(row) if row else None

    def add(self, document_id, name, contents, chunks, vectors, model):
        if len(chunks) != len(vectors):
            raise ValueError("Chunk and vector count mismatch.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT active FROM documents WHERE id=?", (document_id,)).fetchone()
            if existing:
                db.execute("UPDATE documents SET active=1 WHERE id=?", (document_id,))
                return True
            db.execute("INSERT INTO documents(id,name,pdf,model) VALUES(?,?,?,?)", (document_id, name, contents, model))
            db.executemany("INSERT INTO chunks(id,document_id,page,text,vector) VALUES(?,?,?,?,?)", [(c["id"], document_id, c["page"], c["text"], v.astype("float32").tobytes()) for c, v in zip(chunks, vectors)])
        return False

    def list_documents(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT d.id,d.name AS file_name,d.created_at,COUNT(c.id) AS num_chunks FROM documents d JOIN chunks c ON c.document_id=d.id WHERE d.active=1 GROUP BY d.id ORDER BY d.created_at,d.id")]

    def archive(self, document_id):
        with self.connect() as db:
            if not db.execute("UPDATE documents SET active=0 WHERE id=? AND active=1", (document_id,)).rowcount:
                raise AppError("Document not found.", 404)

    def reset(self):
        with self.connect() as db:
            return db.execute("UPDATE documents SET active=0 WHERE active=1").rowcount

    def chunks(self, document_ids, model):
        with self.connect() as db:
            active = {row["id"]: row["model"] for row in db.execute("SELECT id,model FROM documents WHERE active=1")}
            if document_ids and not set(document_ids).issubset(active):
                raise AppError("A selected document is not available.", 404)
            ids = document_ids or list(active)
            if any(active[i] != model for i in ids):
                raise AppError("Embedding model changed. Use a new data directory and re-upload documents.", 409)
            rows = db.execute("SELECT c.*,d.name FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.active=1 ORDER BY c.id")
            return [dict(row) for row in rows if row["document_id"] in ids]

    def source(self, document_id):
        with self.connect() as db:
            row = db.execute("SELECT pdf FROM documents WHERE id=? AND active=1", (document_id,)).fetchone()
            if not row:
                raise AppError("Document not found.", 404)
            return bytes(row["pdf"])

    def integrity(self):
        with self.connect() as db:
            return db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
