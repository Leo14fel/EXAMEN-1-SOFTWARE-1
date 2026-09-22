from uuid import UUID

import pytest

from app.domain.uml.models import ProjectDocument
from app.realtime.projects import ProjectConnectionManager


class FakeWebSocket:
    def __init__(self, fail_send: bool = False) -> None:
        self.accepted = False
        self.closed: list[int] = []
        self.messages: list[dict[str, object]] = []
        self.fail_send = fail_send

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int) -> None:
        self.closed.append(code)

    async def send_json(self, payload: dict[str, object]) -> None:
        if self.fail_send:
            raise RuntimeError('connection closed')
        self.messages.append(payload)


@pytest.mark.asyncio
async def test_broadcasts_authoritative_document_to_all_project_members() -> None:
    manager = ProjectConnectionManager()
    project_id = UUID('11111111-1111-1111-1111-111111111111')
    owner_id = UUID('22222222-2222-2222-2222-222222222222')
    viewer_id = UUID('33333333-3333-3333-3333-333333333333')
    owner_socket = FakeWebSocket()
    viewer_socket = FakeWebSocket()
    document = ProjectDocument(id=project_id, ownerId=owner_id, revision=4)

    await manager.connect(project_id, owner_id, owner_socket)  # type: ignore[arg-type]
    await manager.connect(project_id, viewer_id, viewer_socket)  # type: ignore[arg-type]
    await manager.broadcast_project_updated(project_id, document)

    assert owner_socket.accepted and viewer_socket.accepted
    assert owner_socket.messages[0]['type'] == 'project.updated'
    assert viewer_socket.messages[0]['document']['revision'] == 4  # type: ignore[index]


@pytest.mark.asyncio
async def test_revoking_access_disconnects_all_user_project_sockets() -> None:
    manager = ProjectConnectionManager()
    project_id = UUID('11111111-1111-1111-1111-111111111111')
    user_id = UUID('22222222-2222-2222-2222-222222222222')
    first, second = FakeWebSocket(), FakeWebSocket()

    await manager.connect(project_id, user_id, first)  # type: ignore[arg-type]
    await manager.connect(project_id, user_id, second)  # type: ignore[arg-type]
    await manager.disconnect_user(project_id, user_id)

    assert first.closed == second.closed == [1008]
