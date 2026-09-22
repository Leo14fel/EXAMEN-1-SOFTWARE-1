import asyncio
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket

from app.domain.uml.models import ProjectDocument


class ProjectConnectionManager:
    """Tracks WebSocket subscribers independently for each project."""

    def __init__(self) -> None:
        self._connections: dict[UUID, dict[UUID, set[WebSocket]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._lock = asyncio.Lock()

    async def connect(self, project_id: UUID, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[project_id][user_id].add(websocket)

    async def disconnect(self, project_id: UUID, user_id: UUID, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(project_id, {}).get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections[project_id].pop(user_id, None)
            if not self._connections.get(project_id):
                self._connections.pop(project_id, None)

    async def disconnect_user(self, project_id: UUID, user_id: UUID) -> None:
        async with self._lock:
            sockets = list(self._connections.get(project_id, {}).pop(user_id, set()))
            if not self._connections.get(project_id):
                self._connections.pop(project_id, None)
        await asyncio.gather(
            *(socket.close(code=1008) for socket in sockets), return_exceptions=True
        )

    async def broadcast_project_updated(self, project_id: UUID, document: ProjectDocument) -> None:
        async with self._lock:
            sockets = [
                socket
                for user_sockets in self._connections.get(project_id, {}).values()
                for socket in user_sockets
            ]
            payload = {
                "type": "project.updated",
                "document": document.model_dump(mode="json", by_alias=True),
            }
            results = await asyncio.gather(
                *(socket.send_json(payload) for socket in sockets), return_exceptions=True
            )
            for socket, result in zip(sockets, results, strict=True):
                if not isinstance(result, Exception):
                    continue
                for user_id, user_sockets in list(self._connections.get(project_id, {}).items()):
                    if socket in user_sockets:
                        user_sockets.discard(socket)
                        if not user_sockets:
                            self._connections[project_id].pop(user_id, None)
                        break
            if not self._connections.get(project_id):
                self._connections.pop(project_id, None)


project_connections = ProjectConnectionManager()
