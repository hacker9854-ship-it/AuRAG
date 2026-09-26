"""Predictive notification polling and Server-Sent Events endpoints."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.app.core.neo4j import get_session
from backend.app.services.events import (
    list_predictive_events,
    mark_notification_read,
    notification_payload,
)

router = APIRouter()


def format_sse_event(event: dict) -> str:
    return (
        f"id: {event['id']}\n"
        "event: predictive_warning\n"
        f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )


@router.get("/notifications")
def notifications(
    since: str | None = None,
    limit: int = 50,
    session=Depends(get_session),
) -> dict:
    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_limit", "detail": "limit must be 1-200."},
        )
    try:
        events = list_predictive_events(session, since=since, limit=limit)
        return {"items": [notification_payload(event) for event in events]}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "notifications_failed", "detail": str(exc)},
        ) from exc


@router.post("/notifications/{event_id}/read")
def mark_read(event_id: str, session=Depends(get_session)) -> dict:
    try:
        if not mark_notification_read(session, event_id):
            raise HTTPException(
                status_code=404,
                detail={"error": "notification_not_found", "detail": event_id},
            )
        return {"id": event_id, "status": "read"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "notification_update_failed", "detail": str(exc)},
        ) from exc


@router.get("/events/predictive")
async def predictive_events(request: Request, last_event_id: str | None = None):
    header_cursor = request.headers.get("last-event-id")
    initial_cursor = header_cursor or last_event_id

    async def stream():
        cursor = initial_cursor
        while not await request.is_disconnected():
            try:
                from retrieval.index_chunks import get_database, get_driver

                with get_driver().session(database=get_database()) as session:
                    events = list_predictive_events(session, since=cursor, limit=100)
                if events:
                    for event in events:
                        payload = notification_payload(event)
                        cursor = event["id"]
                        yield format_sse_event(payload)
                else:
                    yield ": keep-alive\n\n"
            except Exception as exc:
                yield (
                    "event: stream_error\n"
                    f"data: {json.dumps({'detail': str(exc)}, separators=(',', ':'))}\n\n"
                )
            await asyncio.sleep(2)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

