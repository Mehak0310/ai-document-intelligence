# API contract

Start FastAPI on localhost port 8000. Interactive docs: `/docs`; schema: `/openapi.json`.
Set `Authorization: Bearer <local token>` when `ADI_API_TOKEN` is configured. Do not put tokens
in URLs. `/health` and API documentation are public local metadata endpoints.

| Route | Request | Response |
|---|---|---|
| `GET /health` | None | Status, active-index availability, storage kind; explicitly does not check Ollama |
| `GET /documents` | Optional configured token | Active documents: ID, filename, chunk count, creation time |
| `POST /upload` | Multipart field `file` | Document metadata, `duplicate`, `index_available` |
| `POST /query` | JSON below | Answer, cited IDs, evidence, source names, model, chunk count, elapsed seconds, abstention flag |
| `DELETE /documents/{id}` | Content-hash document ID | Logical archive; bytes retained; repeat/missing ID returns 404 |
| `POST /documents/reset` | `{"confirm":"ARCHIVE ALL"}` | Count archived; bytes retained |
| `GET /documents/{id}/source` | Active document ID | Exact original PDF bytes; 404 after archive |

```json
{
  "q": "How many days of annual leave are available?",
  "prompt_type": "simple",
  "document_ids": [],
  "model": "llama3"
}
```

`q` is trimmed and must contain 1–2000 characters. Styles: simple, bullet, detailed, analytical.
`model` is optional. `document_ids` is optional, at most 100 SHA-256 IDs; duplicates are collapsed.
Empty selection searches all active documents. Archived or unknown selected IDs return 404.
An empty corpus or insufficient evidence returns 200 with a consistent abstention and no cited IDs.

Evidence contains `id` (request-local S1/S2…), `document_id`, `chunk_id`, `file_name`, one-based
`page`, exact `excerpt`, cosine `score`, and a relative source URL with a page fragment. Only cited
IDs appear in `citations`; retrieved but uncited evidence is displayed separately. `sources` lists
cited filenames. UI source downloads retrieve the full PDF, not an extracted page.

Errors are `{ "detail": "safe message" }`: 401 token, 403 origin, 404 document, 409 embedding
configuration mismatch, 413 size/chunk limit, 415 extension, 422 invalid request/PDF, 429 capacity,
502 invalid model JSON, 503 unavailable generation/embedding/storage, 504 generation timeout.
429 includes `Retry-After: 2`. Client cancellation stops waiting, not necessarily server work.
