# Resume evidence — DRAFT claims for review

No production usage, user counts, time savings, general accuracy, commercial adoption or project
duration is supported. The following bullets describe implementation and verifiable local checks.

1. **DRAFT:** Built a React/TypeScript and FastAPI PDF question-answering application using Hugging Face
   embeddings, FAISS similarity retrieval and local Ollama generation, with document-scoped search
   and page-level source evidence.
2. **DRAFT:** Implemented transactional document storage, content-hash deduplication, recoverable
   document archiving, bounded backend concurrency and citation-ID validation without loading pickle indexes.
3. **DRAFT:** Added deterministic backend and frontend tests, synthetic browser QA and a real local
   RAG evaluation comparing two retrieval configurations across eight labeled questions.

| Claim | Evidence |
|---|---|
| React/TypeScript interface | `frontend/src/App.tsx`, `DocumentPanel.tsx`, `AnswerCard.tsx`, strict build |
| FastAPI and local generation | `backend/main.py`, `generation.py`, opt-in real-model test |
| Embeddings and scoped FAISS | `backend/embeddings.py`, `retrieval.py`, scoping tests |
| Exact page evidence | `ingestion.py`, `rag_pipeline.py`, parser/citation tests and browser source download |
| Atomic persistence and duplicates | `storage.py`, concurrent upload and rollback tests |
| Concurrency and cancellation | `main.py`, `tests/test_cancellation.py`, browser cancellation/overlap checks |
| Quality experiments | `eval/dataset.json`, `scripts/evaluate.py`, actual results and documented pilot limitations |

Supported ATS keywords: React, TypeScript, JavaScript, HTML, CSS, responsive design, accessibility,
React Testing Library, Vitest, Playwright, Python, FastAPI, Pydantic, REST APIs, RAG, LangChain,
Hugging Face, Sentence Transformers, embeddings, FAISS, cosine similarity, SQLite, transactions,
Ollama, local LLM inference, prompt engineering, grounding, citations, pytest, test coverage,
evaluation, GitHub Actions configuration, input validation, DOMPurify, request cancellation.

GitHub Actions is configured, not remotely executed. LangGraph, MCP, agents, fine-tuning, reranking,
cloud deployment and production reliability are not implemented claims. The project now supplies
stronger AI application and frontend evidence; production/senior scope still needs broader operational
work and evidence of design ownership in an interview. No framework name substitutes for that evidence.
