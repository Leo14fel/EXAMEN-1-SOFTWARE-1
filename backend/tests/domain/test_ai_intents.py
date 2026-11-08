from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.ai.context import build_context
from app.ai.gemini import ProviderError
from app.ai.intents import IntentResponse, ResolutionError, resolve_intent
from app.domain.uml.models import CanonicalUmlModel, ProjectDocument, UmlClass


def document():
    return ProjectDocument(
        ownerId=uuid4(),
        umlModel=CanonicalUmlModel(
            elements=[
                UmlClass(id=UUID(int=1), name="Cliente", visibility="public"),
                UmlClass(id=UUID(int=2), name="Pedido", visibility="public"),
            ]
        ),
    )


@pytest.mark.parametrize(
    "intent,command_type",
    [
        ({"operation": "createClass", "name": "Producto"}, "addElement"),
        ({"operation": "renameClass", "target": "Cliente", "name": "Comprador"}, "updateElement"),
        ({"operation": "deleteClass", "target": "Pedido"}, "removeElement"),
        (
            {"operation": "addAttribute", "target": "Cliente", "name": "nombre", "type": "String"},
            "updateElement",
        ),
        ({"operation": "addOperation", "target": "Cliente", "name": "saludar"}, "updateElement"),
        (
            {
                "operation": "createAssociation",
                "source": "Cliente",
                "target": "Pedido",
                "sourceLower": 1,
                "sourceUpper": 1,
                "targetLower": 0,
                "targetUpper": "*",
            },
            "addElement",
        ),
    ],
)
def test_closed_intent_uses_existing_executor_without_mutating_document(intent, command_type):
    project = document()
    before = project.model_dump_json()
    command = resolve_intent(project, IntentResponse(intent=intent))
    assert command.command_type == command_type
    assert project.model_dump_json() == before


@pytest.mark.parametrize(
    "intent",
    [
        {"operation": "executeSql", "sql": "DROP TABLE"},
        {"operation": "createClass", "name": "x", "url": "https://evil.test"},
        {"operation": "addAttribute", "target": "Cliente", "name": "n", "type": "Python"},
        {"operation": "createClass", "name": "  "},
        {"operation": "deleteClass", "target": "Cliente", "actorId": "other"},
        {
            "operation": "createAssociation",
            "source": "Cliente",
            "target": "Pedido",
            "sourceLower": True,
            "sourceUpper": 1,
            "targetLower": 0,
            "targetUpper": "*",
        },
    ],
)
def test_unknown_operations_extra_payloads_and_invalid_schema_are_rejected(intent):
    with pytest.raises(ValidationError):
        IntentResponse(intent=intent)


@pytest.mark.parametrize(
    "intent",
    [
        {"operation": "renameClass", "target": "missing", "name": "x"},
        {"operation": "createClass", "name": "cliente"},
        {"operation": "renameClass", "target": "Cliente", "name": "Pedido"},
        {"operation": "clarify", "reason": "¿Qué clase?"},
        {"operation": "unsupported", "reason": "No SQL"},
    ],
)
def test_no_guessing_and_semantic_validation_fail_closed(intent):
    with pytest.raises(ResolutionError):
        resolve_intent(document(), IntentResponse(intent=intent))


def test_ambiguous_reference_cannot_become_command():
    project = document()
    project.uml_model.elements.append(UmlClass(name="cliente", visibility="public"))
    with pytest.raises(ResolutionError, match="ambiguous"):
        resolve_intent(
            project, IntentResponse(intent={"operation": "deleteClass", "target": "Cliente"})
        )


def test_context_is_bounded_attributed_and_excludes_private_metadata_and_layout():
    project = document()
    project.metadata = {"password": "NEVER_SEND"}
    events = [
        {
            "id": str(i),
            "kind": "message",
            "actorId": "peer",
            "text": "Hola",
            "private": "NEVER_SEND",
        }
        for i in range(25)
    ]
    context = build_context(project, project.owner_id, " crea Producto ", events)
    assert context["request"] == "crea Producto" and context["historyTruncated"]
    assert len(context["recentSharedEvents"]) == 20
    assert context["recentSharedEvents"][0]["actorId"] == "peer"
    ai_event = {
        "kind": "aiResult",
        "actorId": "ai:gemini",
        "requestedBy": "peer",
        "requestId": "request",
        "baseRevision": 0,
        "status": "proposed",
        "canApply": False,
        "text": "No se aplicó",
        "private": "NEVER_SEND",
    }
    attributed = build_context(project, project.owner_id, "otra solicitud", [ai_event])
    assert attributed["recentSharedEvents"][0]["requestedBy"] == "peer"
    assert attributed["recentSharedEvents"][0]["canApply"] is False
    assert "NEVER_SEND" not in str(context)
    assert "diagramLayout" not in context and "metadata" not in context


def test_large_context_fails_instead_of_silently_omitting_diagram():
    project = document()
    events = [{"text": "x" * 4000} for _ in range(20)]
    with pytest.raises(ProviderError, match="TOO_LARGE"):
        build_context(project, project.owner_id, "hola", events)
