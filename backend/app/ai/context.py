"""Only this project's public UML and bounded attributed events leave the server."""

import json
from uuid import UUID

from app.ai.gemini import MAX_INPUT_BYTES, ProviderError
from app.domain.uml.models import ProjectDocument


def build_context(document: ProjectDocument, actor_id: UUID, text: str, events: list[dict]) -> dict:
    if not text.strip() or len(text) > 2000:
        raise ValueError("Request must contain 1..2000 characters")
    # Never send arbitrary project metadata, layout, credentials or memberships.
    safe_events = []
    for event in events[-20:]:
        safe_events.append(
            {
                key: event[key]
                for key in (
                    "id",
                    "sequence",
                    "kind",
                    "actorId",
                    "actorName",
                    "createdAt",
                    "text",
                    "action",
                    "projectRevision",
                    "requestId",
                    "baseRevision",
                    "status",
                    "requestedBy",
                    "canApply",
                )
                if key in event
            }
        )
    result = {
        "projectId": str(document.id),
        "revision": document.revision,
        "requesterId": str(actor_id),
        "request": text.strip(),
        "umlModel": document.uml_model.model_dump(mode="json", by_alias=True),
        "recentSharedEvents": safe_events,
        "historyTruncated": len(events) > 20,
    }
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ProviderError("AI_CONTEXT_TOO_LARGE")
    return result
