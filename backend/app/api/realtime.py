"""Persisted-state subscriptions; mutations keep the existing HTTP command path."""

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pymongo.errors import PyMongoError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.api.projects import _project_access, _project_bus, _project_lock, _state
from app.core.config import settings
from app.core.security import decode_access_token, invalid_token_error
from app.db.dependencies import StorageSession, get_db_session
from app.db.mongo_store import MongoStore
from app.db.users import get_user_by_id

router = APIRouter(tags=["realtime"])
database_session = Depends(get_db_session)
POLL_SECONDS = 0.5
AUTH_TIMEOUT_SECONDS = 5


def document_delta(before: Any, after: Any, path: list[str | int] | None = None) -> list[dict]:
    """Deterministic structural delta, including list truncation in descending order."""
    path = [] if path is None else path
    if before == after:
        return []
    changes = []
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(before.keys() - after.keys()):
            changes.append({"op": "remove", "path": [*path, key]})
        for key in sorted(after):
            if key not in before:
                changes.append({"op": "set", "path": [*path, key], "value": after[key]})
            else:
                changes.extend(document_delta(before[key], after[key], [*path, key]))
    elif isinstance(before, list) and isinstance(after, list):
        for index in range(min(len(before), len(after))):
            changes.extend(document_delta(before[index], after[index], [*path, index]))
        for index in range(len(before) - 1, len(after) - 1, -1):
            changes.append({"op": "remove", "path": [*path, index]})
        for index in range(len(before), len(after)):
            changes.append({"op": "set", "path": [*path, index], "value": after[index]})
    else:
        changes.append({"op": "set", "path": path, "value": after})
    return changes


def subscription_state(
    session: StorageSession,
    project_id: UUID,
    token: str,
) -> dict:
    # SQL is legacy only. Avoid retaining a transaction/snapshot across subscription polls.
    if not isinstance(session, MongoStore):
        session.rollback()
    user = get_user_by_id(session, decode_access_token(token))
    if user is None:
        raise invalid_token_error()
    with _project_lock(project_id):
        access = _project_access(session, project_id, user)
        state = _state(_project_bus(project_id, access.document)).model_dump(
            mode="json", by_alias=True
        )
    result = {**state, "effectiveRole": access.effective_role.value}
    return result




async def receive_control(socket: WebSocket) -> dict:
    raw = await socket.receive_text()
    if len(raw) > 4096:
        raise ValueError("Control message exceeds limit")
    message = json.loads(raw)
    if not isinstance(message, dict):
        raise ValueError("Control message must be an object")
    return message


@router.websocket("/projects/{project_id}/sync")
async def synchronize_project(
    socket: WebSocket, project_id: UUID, session: StorageSession = database_session
) -> None:
    # CORS middleware does not protect WebSockets. CLI clients may omit Origin.
    if socket.headers.get("origin") not in (None, settings.frontend_origin):
        await socket.close(code=4403)
        return
    await socket.accept()
    try:
        auth = await asyncio.wait_for(receive_control(socket), timeout=AUTH_TIMEOUT_SECONDS)
        token = auth.get("token")
        if auth.get("type") != "authenticate" or not isinstance(token, str):
            await socket.close(code=4401)
            return
        previous = None
        force_snapshot = True
        while True:
            current = await run_in_threadpool(
                subscription_state, session, project_id, token
            )
            document = current["document"]
            if force_snapshot:
                await socket.send_json({"type": "snapshot", **current})
            elif current != previous:
                await socket.send_json(
                    {
                        "type": "patch",
                        "projectId": str(project_id),
                        "baseRevision": previous["document"]["revision"],
                        "revision": document["revision"],
                        "changes": document_delta(previous["document"], document),
                        "canUndo": current["canUndo"],
                        "canRedo": current["canRedo"],
                        "effectiveRole": current["effectiveRole"],
                    }
                )
            previous = current
            force_snapshot = False
            try:
                control = await asyncio.wait_for(receive_control(socket), timeout=POLL_SECONDS)
                if control == {"type": "resync"}:
                    force_snapshot = True
                else:
                    await socket.close(code=4400)
                    return
                await asyncio.sleep(POLL_SECONDS)
            except TimeoutError:
                pass
    except WebSocketDisconnect:
        return
    except HTTPException as error:
        await socket.close(code=4401 if error.status_code == 401 else 4404)
    except (TimeoutError, ValueError, KeyError, TypeError):
        await socket.close(code=4400)
    except (PyMongoError, SQLAlchemyError):
        await socket.close(code=1013, reason="Storage unavailable")
