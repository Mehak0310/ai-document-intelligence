import asyncio
from dataclasses import replace
from threading import Event
from unittest.mock import Mock

import httpx

from backend.main import create_app


def test_cancelled_request_keeps_capacity_until_worker_exits(service, settings, monkeypatch):
    started, release, ended = Event(), Event(), Event()
    def blocked(*args):
        started.set()
        try:
            assert release.wait(5)
            raise RuntimeError('synthetic-sensitive-marker')
        finally:
            ended.set()
    monkeypatch.setattr(service, 'query', blocked)
    app = create_app(replace(settings, max_concurrent=1), service)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://testserver') as client:
            task = asyncio.create_task(client.post('/query', json={'q': 'leave'}))
            assert await asyncio.to_thread(started.wait, 5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            assert (await client.get('/documents')).status_code == 429
            release.set()
            assert await asyncio.to_thread(ended.wait, 5)
            assert (await client.get('/documents')).status_code == 200
    asyncio.run(scenario())
