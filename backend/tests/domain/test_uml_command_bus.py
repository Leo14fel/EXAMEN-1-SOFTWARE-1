import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import TypeAdapter

from app.domain.uml.command_bus import UmlCommandBus
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
from app.domain.uml.executor import execute_uml_command
from app.domain.uml.models import (
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlComposition,
    UmlMultiplicity,
    UmlVisibility,
)


def make_document(
    *elements: object, nodes: dict[UUID, DiagramNodeLayout] | None = None
) -> ProjectDocument:
    timestamp = datetime(2026, 9, 14, tzinfo=UTC)
    return ProjectDocument(
        ownerId=uuid4(),
        createdAt=timestamp,
        updatedAt=timestamp,
        umlModel=CanonicalUmlModel(elements=elements),
        diagramLayout=DiagramLayout(nodes={} if nodes is None else nodes),
    )


def make_class(name: str, element_id: UUID | None = None) -> UmlClass:
    return UmlClass(id=element_id or uuid4(), name=name, visibility=UmlVisibility.PUBLIC)


def make_association(
    source_id: UUID, target_id: UUID, element_id: UUID | None = None
) -> UmlAssociation:
    multiplicity = UmlMultiplicity(lower=0, upper="*")
    return UmlAssociation(
        id=element_id or uuid4(),
        sourceId=source_id,
        targetId=target_id,
        sourceMultiplicity=multiplicity,
        targetMultiplicity=multiplicity,
    )


def make_rich_document() -> tuple[ProjectDocument, UmlClass]:
    customer = make_class("Customer")
    document = make_document(
        customer,
        nodes={customer.id: DiagramNodeLayout(x=1, y=2, width=100, height=50)},
    )
    document.metadata["nested"] = {"values": ["original"]}
    return document, customer


def test_add_class_and_relationship() -> None:
    customer = make_class("Customer")
    order = make_class("Order")
    bus = UmlCommandBus(make_document())

    bus.execute(AddUmlElementCommand(element=customer))
    bus.execute(AddUmlElementCommand(element=order))
    bus.execute(AddUmlElementCommand(element=make_association(customer.id, order.id)))

    assert [element.kind for element in bus.document.uml_model.elements] == [
        "class",
        "class",
        "association",
    ]


def test_update_class_and_relationship() -> None:
    customer = make_class("Customer")
    order = make_class("Order")
    association = make_association(customer.id, order.id)
    bus = UmlCommandBus(make_document(customer, order, association))
    renamed_customer = make_class("Client", customer.id)
    replacement_association = make_association(customer.id, order.id, association.id)

    bus.execute(UpdateUmlElementCommand(elementId=customer.id, element=renamed_customer))
    bus.execute(
        UpdateUmlElementCommand(elementId=association.id, element=replacement_association)
    )

    assert bus.document.uml_model.elements[0] == renamed_customer
    assert bus.document.uml_model.elements[2] == replacement_association


def test_remove_relationship_and_unreferenced_class() -> None:
    customer = make_class("Customer")
    order = make_class("Order")
    association = make_association(customer.id, order.id)
    bus = UmlCommandBus(make_document(customer, order, association))

    bus.execute(RemoveUmlElementCommand(elementId=association.id))
    bus.execute(RemoveUmlElementCommand(elementId=order.id))

    assert bus.document.uml_model.elements == [customer]


def test_remove_class_removes_its_node_layout() -> None:
    customer = make_class("Customer")
    layout = DiagramNodeLayout(x=1, y=2, width=100, height=50)
    bus = UmlCommandBus(make_document(customer, nodes={customer.id: layout}))

    bus.execute(RemoveUmlElementCommand(elementId=customer.id))

    assert bus.document.uml_model.elements == []
    assert bus.document.diagram_layout.nodes == {}


def test_set_replace_and_remove_layout() -> None:
    customer = make_class("Customer")
    first = DiagramNodeLayout(x=1, y=2, width=100, height=50)
    replacement = DiagramNodeLayout(x=3, y=4, width=120, height=60)
    bus = UmlCommandBus(make_document(customer))

    bus.execute(SetNodeLayoutCommand(elementId=customer.id, layout=first))
    bus.execute(SetNodeLayoutCommand(elementId=customer.id, layout=replacement))
    assert bus.document.diagram_layout.nodes[customer.id] == replacement
    bus.execute(RemoveNodeLayoutCommand(elementId=customer.id))

    assert bus.document.diagram_layout.nodes == {}


@pytest.mark.parametrize(
    ("command", "code"),
    [
        (
            lambda customer, association: AddUmlElementCommand(element=customer),
            UmlCommandErrorCode.ELEMENT_ALREADY_EXISTS,
        ),
        (
            lambda customer, association: UpdateUmlElementCommand(
                elementId=uuid4(), element=make_class("Other")
            ),
            UmlCommandErrorCode.ELEMENT_NOT_FOUND,
        ),
        (
            lambda customer, association: UpdateUmlElementCommand(
                elementId=customer.id, element=make_class("Other")
            ),
            UmlCommandErrorCode.ELEMENT_ID_MISMATCH,
        ),
        (
            lambda customer, association: UpdateUmlElementCommand(
                elementId=customer.id,
                element=make_association(customer.id, customer.id, customer.id),
            ),
            UmlCommandErrorCode.ELEMENT_KIND_MISMATCH,
        ),
        (
            lambda customer, association: RemoveUmlElementCommand(elementId=uuid4()),
            UmlCommandErrorCode.ELEMENT_NOT_FOUND,
        ),
        (
            lambda customer, association: SetNodeLayoutCommand(
                elementId=association.id,
                layout=DiagramNodeLayout(x=0, y=0, width=1, height=1),
            ),
            UmlCommandErrorCode.NODE_LAYOUT_TARGET_NOT_CLASS,
        ),
        (
            lambda customer, association: RemoveNodeLayoutCommand(elementId=customer.id),
            UmlCommandErrorCode.NODE_LAYOUT_NOT_FOUND,
        ),
    ],
)
def test_command_errors_are_typed(command: object, code: UmlCommandErrorCode) -> None:
    customer = make_class("Customer")
    association = make_association(customer.id, customer.id)
    bus = UmlCommandBus(make_document(customer, association))

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(command(customer, association))  # type: ignore[operator]

    assert error.value.code is code


def test_remove_referenced_class_is_atomic() -> None:
    customer = make_class("Customer")
    order = make_class("Order")
    association = make_association(customer.id, order.id)
    bus = UmlCommandBus(make_document(customer, order, association))
    before = bus.document.model_copy(deep=True)

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(RemoveUmlElementCommand(elementId=order.id))

    assert error.value.code is UmlCommandErrorCode.INVALID_RESULTING_DOCUMENT
    assert bus.document == before
    assert bus.document.revision == 0
    assert not bus.can_undo
    assert not bus.can_redo


def test_semantic_diagnostics_do_not_block_structural_commands() -> None:
    bus = UmlCommandBus(make_document())

    bus.execute(AddUmlElementCommand(element=make_class("Customer")))
    bus.execute(AddUmlElementCommand(element=make_class("Customer")))

    assert len(bus.document.uml_model.elements) == 2


def test_execute_does_not_mutate_the_original_document() -> None:
    initial = make_document()
    initial_copy = initial.model_copy(deep=True)
    bus = UmlCommandBus(initial)

    bus.execute(AddUmlElementCommand(element=make_class("Customer")))

    assert initial == initial_copy
    assert bus.document != initial


def test_document_property_does_not_expose_bus_state() -> None:
    document, customer = make_rich_document()
    bus = UmlCommandBus(document)

    external = bus.document
    external.metadata["nested"]["values"].append("external")
    external.uml_model.elements[0].name = "ExternalCustomer"
    external.diagram_layout.nodes[customer.id].x = 999

    current = bus.document
    assert current.metadata["nested"] == {"values": ["original"]}
    assert current.uml_model.elements[0].name == "Customer"
    assert current.diagram_layout.nodes[customer.id].x == 1


def test_execute_result_does_not_expose_bus_state() -> None:
    document, customer = make_rich_document()
    bus = UmlCommandBus(document)

    result = bus.execute(AddUmlElementCommand(element=make_class("Order")))
    result.metadata["nested"]["values"].append("external")
    result.uml_model.elements[0].name = "ExternalCustomer"
    result.diagram_layout.nodes[customer.id].x = 999

    current = bus.document
    assert current.metadata["nested"] == {"values": ["original"]}
    assert current.uml_model.elements[0].name == "Customer"
    assert current.diagram_layout.nodes[customer.id].x == 1


def test_undo_result_does_not_expose_bus_state() -> None:
    document, customer = make_rich_document()
    bus = UmlCommandBus(document)
    bus.execute(AddUmlElementCommand(element=make_class("Order")))

    result = bus.undo()
    result.metadata["nested"]["values"].append("external")
    result.uml_model.elements[0].name = "ExternalCustomer"
    result.diagram_layout.nodes[customer.id].x = 999

    current = bus.document
    assert current.metadata["nested"] == {"values": ["original"]}
    assert current.uml_model.elements[0].name == "Customer"
    assert current.diagram_layout.nodes[customer.id].x == 1


def test_redo_result_does_not_expose_bus_state() -> None:
    document, customer = make_rich_document()
    bus = UmlCommandBus(document)
    bus.execute(AddUmlElementCommand(element=make_class("Order")))
    bus.undo()

    result = bus.redo()
    result.metadata["nested"]["values"].append("external")
    result.uml_model.elements[0].name = "ExternalCustomer"
    result.diagram_layout.nodes[customer.id].x = 999

    current = bus.document
    assert current.metadata["nested"] == {"values": ["original"]}
    assert current.uml_model.elements[0].name == "Customer"
    assert current.diagram_layout.nodes[customer.id].x == 1


def test_command_element_cannot_mutate_bus_after_execution() -> None:
    element = make_class("Customer")
    command = AddUmlElementCommand(element=element)
    bus = UmlCommandBus(make_document())

    bus.execute(command)
    command.element.name = "ExternalCustomer"
    command.element.attributes.append(
        UmlAttribute(name="external", type="str", visibility=UmlVisibility.PUBLIC)
    )

    current_element = bus.document.uml_model.elements[0]
    assert current_element.name == "Customer"
    assert isinstance(current_element, UmlClass)
    assert current_element.attributes == []


def test_command_layout_cannot_mutate_bus_after_execution() -> None:
    document, customer = make_rich_document()
    command = SetNodeLayoutCommand(
        elementId=customer.id,
        layout=DiagramNodeLayout(x=10, y=20, width=200, height=100),
    )
    bus = UmlCommandBus(document)

    bus.execute(command)
    command.layout.x = 999
    command.layout.width = 999

    current_layout = bus.document.diagram_layout.nodes[customer.id]
    assert current_layout.x == 10
    assert current_layout.width == 200


def test_executor_result_cannot_mutate_input_document() -> None:
    document, customer = make_rich_document()
    result = execute_uml_command(document, AddUmlElementCommand(element=make_class("Order")))
    result.metadata["nested"]["values"].append("external")
    result.uml_model.elements[0].name = "ExternalCustomer"
    result.diagram_layout.nodes[customer.id].x = 999

    assert document.metadata["nested"] == {"values": ["original"]}
    assert document.uml_model.elements[0].name == "Customer"
    assert document.diagram_layout.nodes[customer.id].x == 1


def test_execute_undo_and_redo() -> None:
    customer = make_class("Customer")
    bus = UmlCommandBus(make_document())
    bus.execute(AddUmlElementCommand(element=customer))

    assert bus.can_undo
    assert not bus.can_redo
    bus.undo()
    assert bus.document.uml_model.elements == []
    assert not bus.can_undo
    assert bus.can_redo
    bus.redo()
    assert bus.document.uml_model.elements == [customer]
    assert bus.can_undo
    assert not bus.can_redo


def test_multiple_undo_and_redo_restore_content() -> None:
    first = make_class("First")
    second = make_class("Second")
    bus = UmlCommandBus(make_document())
    bus.execute(AddUmlElementCommand(element=first))
    bus.execute(AddUmlElementCommand(element=second))
    bus.undo()
    bus.undo()
    assert bus.document.uml_model.elements == []
    bus.redo()
    bus.redo()

    assert bus.document.uml_model.elements == [first, second]


def test_undo_history_retains_only_the_100_most_recent_states() -> None:
    bus = UmlCommandBus(make_document())
    for index in range(101):
        bus.execute(AddUmlElementCommand(element=make_class(f"Class{index}")))

    undo_count = 0
    while bus.can_undo:
        bus.undo()
        undo_count += 1

    assert undo_count == 100
    assert [element.name for element in bus.document.uml_model.elements] == ["Class0"]
    with pytest.raises(UmlCommandExecutionError) as error:
        bus.undo()
    assert error.value.code is UmlCommandErrorCode.UNDO_NOT_AVAILABLE


def test_redo_and_revision_remain_correct_after_history_limit() -> None:
    bus = UmlCommandBus(make_document())
    for index in range(101):
        bus.execute(AddUmlElementCommand(element=make_class(f"Class{index}")))
    revision_after_execute = bus.document.revision

    while bus.can_undo:
        bus.undo()
    revision_after_undo = bus.document.revision
    while bus.can_redo:
        bus.redo()

    assert len(bus.document.uml_model.elements) == 101
    assert bus.document.revision == 301
    assert revision_after_execute == 101
    assert revision_after_undo == 201
    assert not bus.can_redo


def test_new_command_after_undo_clears_redo() -> None:
    first = make_class("First")
    second = make_class("Second")
    third = make_class("Third")
    bus = UmlCommandBus(make_document())
    bus.execute(AddUmlElementCommand(element=first))
    bus.execute(AddUmlElementCommand(element=second))
    bus.undo()
    assert bus.can_redo

    bus.execute(AddUmlElementCommand(element=third))

    assert not bus.can_redo
    assert bus.document.uml_model.elements == [first, third]


def test_undo_and_redo_without_history_raise_explicit_errors() -> None:
    bus = UmlCommandBus(make_document())

    with pytest.raises(UmlCommandExecutionError) as undo_error:
        bus.undo()
    with pytest.raises(UmlCommandExecutionError) as redo_error:
        bus.redo()

    assert undo_error.value.code is UmlCommandErrorCode.UNDO_NOT_AVAILABLE
    assert redo_error.value.code is UmlCommandErrorCode.REDO_NOT_AVAILABLE


def test_revision_and_updated_at_are_monotonic_and_failures_do_not_change_them() -> None:
    bus = UmlCommandBus(make_document())
    initial_updated_at = bus.document.updated_at
    bus.execute(AddUmlElementCommand(element=make_class("First")))
    first_updated_at = bus.document.updated_at
    bus.execute(AddUmlElementCommand(element=make_class("Second")))
    second_updated_at = bus.document.updated_at
    bus.undo()
    undo_updated_at = bus.document.updated_at
    bus.redo()

    assert bus.document.revision == 4
    assert (
        initial_updated_at
        < first_updated_at
        < second_updated_at
        < undo_updated_at
        < bus.document.updated_at
    )
    before_failure = bus.document.model_copy(deep=True)
    with pytest.raises(UmlCommandExecutionError):
        bus.execute(RemoveUmlElementCommand(elementId=uuid4()))
    assert bus.document == before_failure


@pytest.mark.parametrize(
    "command",
    [
        AddUmlElementCommand(element=make_class("Customer")),
        UpdateUmlElementCommand(
            elementId=UUID("00000000-0000-0000-0000-000000000001"),
            element=make_class("Customer", UUID("00000000-0000-0000-0000-000000000001")),
        ),
        RemoveUmlElementCommand(elementId=UUID("00000000-0000-0000-0000-000000000001")),
        SetNodeLayoutCommand(
            elementId=UUID("00000000-0000-0000-0000-000000000001"),
            layout=DiagramNodeLayout(x=0, y=0, width=1, height=1),
        ),
        RemoveNodeLayoutCommand(elementId=UUID("00000000-0000-0000-0000-000000000001")),
    ],
)
def test_command_json_round_trip_preserves_concrete_subtype(command: UmlCommand) -> None:
    adapter = TypeAdapter(UmlCommand)
    payload = json.loads(adapter.dump_json(command, by_alias=True))

    restored = adapter.validate_json(adapter.dump_json(command, by_alias=True))

    assert payload["commandType"] == command.command_type
    if isinstance(
        command,
        UpdateUmlElementCommand
        | RemoveUmlElementCommand
        | SetNodeLayoutCommand
        | RemoveNodeLayoutCommand,
    ):
        assert payload["elementId"] == str(command.element_id)
    assert type(restored) is type(command)
    assert restored == command


def test_nested_element_round_trip_preserves_relationship_subtype() -> None:
    source = uuid4()
    target = uuid4()
    command = AddUmlElementCommand(
        element=UmlComposition(
            sourceId=source,
            targetId=target,
            sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
            targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
        )
    )
    adapter = TypeAdapter(UmlCommand)

    restored = adapter.validate_json(adapter.dump_json(command))

    assert isinstance(restored, AddUmlElementCommand)
    assert isinstance(restored.element, UmlComposition)


def test_executor_is_pure() -> None:
    document = make_document()
    original = document.model_copy(deep=True)

    result = execute_uml_command(document, AddUmlElementCommand(element=make_class("Customer")))

    assert document == original
    assert result != document
