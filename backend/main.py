import asyncio
import logging
import secrets
from threading import BoundedSemaphore
from typing import Literal, Optional
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool
from .config import Settings
from .errors import AppError
from .rag_pipeline import DocumentService

logger = logging.getLogger("adi")


class QueryRequest(BaseModel):
    q: str = Field(min_length=1, max_length=2000)
    prompt_type: Literal["bullet", "detailed", "simple", "analytical"] = "simple"
    model: Optional[str] = Field(default=None, max_length=100, pattern=r"^[\w.:/-]+$")
    document_ids: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("q")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Question must contain text.")
        return value.strip()

    @field_validator("document_ids")
    @classmethod
    def identifiers(cls, value):
        if any(len(v) != 64 or any(c not in "0123456789abcdef" for c in v) for v in value):
            raise ValueError("Invalid document identifier.")
        return list(dict.fromkeys(value))


class ResetRequest(BaseModel):
    confirm: Literal["ARCHIVE ALL"]


def create_app(settings=None, service=None):
    settings = settings or Settings.from_env()
    service = service or DocumentService(settings)
    gate = BoundedSemaphore(settings.max_concurrent)
    app = FastAPI(title="AI Document Intelligence", version="2.0.0")
    app.state.service = service
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type", "Authorization"])

    async def access(request: Request, authorization: Optional[str] = Header(default=None)):
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origins:
            raise HTTPException(403, "Origin is not allowed.")
        if settings.api_token and not secrets.compare_digest(authorization or "", f"Bearer {settings.api_token}"):
            raise HTTPException(401, "Valid API token required.")

    async def work(fn, *args):
        if not gate.acquire(blocking=False):
            raise HTTPException(429, "Server is busy. Try again shortly.", headers={"Retry-After": "2"})

        def guarded():
            try:
                return fn(*args)
            except AppError:
                raise
            except Exception as exc:
                logger.error("operation_failed type=%s", type(exc).__name__)
                raise AppError("Operation failed. Check local configuration and storage.", 503) from exc
            finally:
                gate.release()
        task = asyncio.create_task(run_in_threadpool(guarded))
        # Retrieve background errors after client cancellation to avoid traceback logging.
        task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)
        return await asyncio.shield(task)

    @app.exception_handler(AppError)
    async def domain_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({"detail": "Invalid request. Check required fields, lengths and allowed values."}, status_code=422)

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok", "index_available": bool(await work(service.store.list_documents)), "storage": "sqlite", "ollama_checked": False}

    @app.get("/documents", dependencies=[Depends(access)])
    async def documents():
        return {"documents": await work(service.store.list_documents)}

    @app.post("/upload", dependencies=[Depends(access)])
    async def upload(file: UploadFile = File(...)):
        try:
            contents = await file.read(settings.max_upload_bytes + 1)
        finally:
            await file.close()
        return await work(service.ingest, file.filename, contents)

    @app.post("/query", dependencies=[Depends(access)])
    async def query(req: QueryRequest):
        return await work(service.query, req.q, req.prompt_type, req.model, req.document_ids)

    @app.delete("/documents/{document_id}", dependencies=[Depends(access)])
    async def archive(document_id: str):
        await work(service.store.archive, document_id)
        return {"archived": True, "bytes_retained": True}

    @app.post("/documents/reset", dependencies=[Depends(access)])
    async def reset(req: ResetRequest):
        return {"archived": await work(service.store.reset), "bytes_retained": True}

    @app.get("/documents/{document_id}/source", dependencies=[Depends(access)])
    async def source(document_id: str):
        return Response(await work(service.store.source, document_id), media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="source.pdf"'})

    return app


app = create_app()
