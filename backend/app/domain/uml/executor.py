from copy import deepcopy
from uuid import UUID

from pydantic import ValidationError

from app.domain.uml.commands import (
    AddUmlElementCommand,
    RemoveNodeLayoutCommand,
    RemoveUmlElementCommand,
    SetNodeLayoutCommand,
    UmlCommand,
    UmlCommandErrorCode,
    UmlCommandExecutionError,
    UpdateUmlElementCommand,
)
from app.domain.uml.models import (
    CanonicalUmlElement,
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlClass,
)


def execute_uml_command(document: ProjectDocument, command: UmlCommand) -> ProjectDocument:
    if isinstance(command, AddUmlElementCommand):
        if _find_element(document, command.element.id) is not None:
            _raise(UmlCommandErrorCode.ELEMENT_ALREADY_EXISTS, "UML element already exists")
        return _build_document(document, [*document.uml_model.elements, command.element])

    if isinstance(command, UpdateUmlElementCommand):
        existing = _find_element(document, command.element_id)
        if existing is None:
            _raise(UmlCommandErrorCode.ELEMENT_NOT_FOUND, "UML element was not found")
        if command.element.id != command.element_id:
            _raise(
                UmlCommandErrorCode.ELEMENT_ID_MISMATCH,
                "Replacement element id must match elementId",
            )
        if command.element.kind != existing.kind:
            _raise(
                UmlCommandErrorCode.ELEMENT_KIND_MISMATCH,
                "Replacement element kind must match the existing element",
            )
        elements = [
            command.element if element.id == command.element_id else element
            for element in document.uml_model.elements
        ]
        return _build_document(document, elements)

    if isinstance(command, RemoveUmlElementCommand):
        existing = _find_element(document, command.element_id)
        if existing is None:
            _raise(UmlCommandErrorCode.ELEMENT_NOT_FOUND, "UML element was not found")
        elements = [
            element for element in document.uml_model.elements if element.id != command.element_id
        ]
        node_layouts = dict(document.diagram_layout.nodes)
        if isinstance(existing, UmlClass):
            node_layouts.pop(command.element_id, None)
        return _build_document(document, elements, node_layouts)

    if isinstance(command, SetNodeLayoutCommand):
        _require_class(document, command.element_id)
        node_layouts = dict(document.diagram_layout.nodes)
        node_layouts[command.element_id] = command.layout
        return _build_document(document, document.uml_model.elements, node_layouts)

    if isinstance(command, RemoveNodeLayoutCommand):
        _require_class(document, command.element_id)
        if command.element_id not in document.diagram_layout.nodes:
            _raise(UmlCommandErrorCode.NODE_LAYOUT_NOT_FOUND, "Node layout was not found")
        node_layouts = dict(document.diagram_layout.nodes)
        del node_layouts[command.element_id]
        return _build_document(document, document.uml_model.elements, node_layouts)

    raise AssertionError("Unsupported UML command")


def _find_element(document: ProjectDocument, element_id: UUID) -> CanonicalUmlElement | None:
    return next(
        (element for element in document.uml_model.elements if element.id == element_id), None
    )


def _require_class(document: ProjectDocument, element_id: UUID) -> UmlClass:
    element = _find_element(document, element_id)
    if element is None:
        _raise(UmlCommandErrorCode.ELEMENT_NOT_FOUND, "UML element was not found")
    if not isinstance(element, UmlClass):
        _raise(
            UmlCommandErrorCode.NODE_LAYOUT_TARGET_NOT_CLASS,
            "Node layout target must be a UML class",
        )
    return element


def _build_document(
    document: ProjectDocument,
    elements: list[CanonicalUmlElement],
    node_layouts: dict[UUID, DiagramNodeLayout] | None = None,
) -> ProjectDocument:
    try:
        uml_model = CanonicalUmlModel(
            elements=[element.model_copy(deep=True) for element in elements]
        )
        layouts = document.diagram_layout.nodes if node_layouts is None else node_layouts
        diagram_layout = DiagramLayout(
            nodes={
                element_id: layout.model_copy(deep=True)
                for element_id, layout in layouts.items()
            }
        )
        return ProjectDocument(
            id=document.id,
            metadata=deepcopy(document.metadata),
            ownerId=document.owner_id,
            revision=document.revision,
            createdAt=document.created_at,
            updatedAt=document.updated_at,
            umlModel=uml_model,
            diagramLayout=diagram_layout,
        )
    except ValidationError as error:
        raise UmlCommandExecutionError(
            UmlCommandErrorCode.INVALID_RESULTING_DOCUMENT,
            "Command would produce an invalid ProjectDocument",
        ) from error


def _raise(code: UmlCommandErrorCode, message: str) -> None:
    raise UmlCommandExecutionError(code, message)
