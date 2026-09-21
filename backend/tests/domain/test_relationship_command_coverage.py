from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import (
    AddUmlElementCommand,
    RemoveUmlElementCommand,
    UmlCommandErrorCode,
    UmlCommandExecutionError,
    UpdateUmlElementCommand,
)
from app.domain.uml.models import (
    CanonicalUmlElement,
    CanonicalUmlModel,
    ProjectDocument,
    UmlAggregation,
    UmlAssociation,
    UmlClass,
    UmlComposition,
    UmlGeneralization,
    UmlMultiplicity,
    UmlVisibility,
)


def make_document(*elements: CanonicalUmlElement) -> ProjectDocument:
    timestamp = datetime(2026, 9, 21, tzinfo=UTC)
    return ProjectDocument(
        ownerId=uuid4(),
        createdAt=timestamp,
        updatedAt=timestamp,
        umlModel=CanonicalUmlModel(elements=elements),
    )


def make_class(name: str) -> UmlClass:
    return UmlClass(name=name, visibility=UmlVisibility.PUBLIC)


def make_relationship(
    kind: str,
    source_id: UUID,
    target_id: UUID,
    element_id: UUID | None = None,
    source_multiplicity: UmlMultiplicity | None = None,
    target_multiplicity: UmlMultiplicity | None = None,
) -> UmlAssociation | UmlAggregation | UmlComposition | UmlGeneralization:
    if kind == "generalization":
        return UmlGeneralization(id=element_id or uuid4(), sourceId=source_id, targetId=target_id)

    relationship_type = {
        "association": UmlAssociation,
        "aggregation": UmlAggregation,
        "composition": UmlComposition,
    }[kind]
    return relationship_type(
        id=element_id or uuid4(),
        sourceId=source_id,
        targetId=target_id,
        sourceMultiplicity=source_multiplicity or UmlMultiplicity(lower=0, upper=1),
        targetMultiplicity=target_multiplicity or UmlMultiplicity(lower=1, upper="*"),
    )


@pytest.mark.parametrize("kind", ["association", "aggregation", "composition"])
def test_binary_relationship_crud_undo_redo_and_multiplicity_updates(kind: str) -> None:
    first = make_class("First")
    second = make_class("Second")
    third = make_class("Third")
    relationship = make_relationship(kind, first.id, second.id)
    replacement = make_relationship(
        kind,
        third.id,
        first.id,
        relationship.id,
        UmlMultiplicity(lower=1, upper=1),
        UmlMultiplicity(lower=0, upper="*"),
    )
    bus = UmlCommandBus(make_document(first, second, third))

    bus.execute(AddUmlElementCommand(element=relationship))
    bus.execute(UpdateUmlElementCommand(elementId=relationship.id, element=replacement))
    bus.execute(RemoveUmlElementCommand(elementId=relationship.id))

    bus.undo()
    assert bus.document.uml_model.elements[-1] == replacement
    bus.undo()
    assert bus.document.uml_model.elements[-1] == relationship
    bus.redo()
    assert bus.document.uml_model.elements[-1] == replacement
    bus.redo()
    assert all(element.id != relationship.id for element in bus.document.uml_model.elements)

    assert replacement.source_id == third.id
    assert replacement.target_id == first.id
    assert replacement.source_multiplicity == UmlMultiplicity(lower=1, upper=1)
    assert replacement.target_multiplicity == UmlMultiplicity(lower=0, upper="*")


@pytest.mark.parametrize("kind", ["association", "aggregation", "composition"])
def test_binary_self_relationships_are_admissible(kind: str) -> None:
    classifier = make_class("Recursive")
    relationship = make_relationship(kind, classifier.id, classifier.id)
    bus = UmlCommandBus(make_document(classifier))

    bus.execute(AddUmlElementCommand(element=relationship))
    assert bus.document.uml_model.elements[-1] == relationship
    bus.undo()
    assert bus.document.uml_model.elements == [classifier]
    bus.redo()
    assert bus.document.uml_model.elements[-1] == relationship


def test_generalization_crud_undo_redo_and_updates() -> None:
    child = make_class("Child")
    parent = make_class("Parent")
    other_child = make_class("OtherChild")
    generalization = make_relationship("generalization", child.id, parent.id)
    replacement = make_relationship(
        "generalization", other_child.id, parent.id, generalization.id
    )
    bus = UmlCommandBus(make_document(child, parent, other_child))

    bus.execute(AddUmlElementCommand(element=generalization))
    bus.execute(UpdateUmlElementCommand(elementId=generalization.id, element=replacement))
    bus.execute(RemoveUmlElementCommand(elementId=generalization.id))

    bus.undo()
    assert bus.document.uml_model.elements[-1] == replacement
    bus.undo()
    assert bus.document.uml_model.elements[-1] == generalization
    bus.redo()
    assert bus.document.uml_model.elements[-1] == replacement
    bus.redo()
    assert all(element.id != generalization.id for element in bus.document.uml_model.elements)


def test_self_generalization_is_rejected_atomically() -> None:
    classifier = make_class("Classifier")
    bus = UmlCommandBus(make_document(classifier))
    before = bus.document

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(
            AddUmlElementCommand(
                element=make_relationship("generalization", classifier.id, classifier.id)
            )
        )

    assert error.value.code is UmlCommandErrorCode.GENERALIZATION_SELF_REFERENCE
    assert bus.document == before
    assert not bus.can_undo
    assert not bus.can_redo


def test_direct_generalization_cycle_is_rejected_without_altering_undo_history() -> None:
    first = make_class("First")
    second = make_class("Second")
    valid = make_relationship("generalization", first.id, second.id)
    bus = UmlCommandBus(make_document(first, second))
    bus.execute(AddUmlElementCommand(element=valid))
    before_rejection = bus.document

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(
            AddUmlElementCommand(element=make_relationship("generalization", second.id, first.id))
        )

    assert error.value.code is UmlCommandErrorCode.GENERALIZATION_CYCLE
    assert bus.document == before_rejection
    assert bus.can_undo
    assert not bus.can_redo
    bus.undo()
    assert bus.document.uml_model.elements == [first, second]


def test_indirect_generalization_cycle_is_rejected_atomically() -> None:
    first = make_class("First")
    second = make_class("Second")
    third = make_class("Third")
    bus = UmlCommandBus(make_document(first, second, third))
    bus.execute(
        AddUmlElementCommand(element=make_relationship("generalization", first.id, second.id))
    )
    bus.execute(
        AddUmlElementCommand(element=make_relationship("generalization", second.id, third.id))
    )
    before = bus.document

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(
            AddUmlElementCommand(element=make_relationship("generalization", third.id, first.id))
        )

    assert error.value.code is UmlCommandErrorCode.GENERALIZATION_CYCLE
    assert bus.document == before
    assert bus.document.revision == 2
    assert not bus.can_redo


def test_generalization_update_that_creates_a_cycle_is_rejected_atomically() -> None:
    first = make_class("First")
    second = make_class("Second")
    third = make_class("Third")
    first_generalization = make_relationship("generalization", first.id, second.id)
    second_generalization = make_relationship("generalization", second.id, third.id)
    bus = UmlCommandBus(
        make_document(first, second, third, first_generalization, second_generalization)
    )
    before = bus.document
    cyclic_replacement = make_relationship(
        "generalization", second.id, first.id, second_generalization.id
    )

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(
            UpdateUmlElementCommand(
                elementId=second_generalization.id, element=cyclic_replacement
            )
        )

    assert error.value.code is UmlCommandErrorCode.GENERALIZATION_CYCLE
    assert bus.document == before
    assert not bus.can_undo
    assert not bus.can_redo


@pytest.mark.parametrize("kind", ["association", "composition", "generalization"])
def test_removing_a_class_referenced_by_a_relationship_is_atomic(kind: str) -> None:
    source = make_class("Source")
    target = make_class("Target")
    relationship = make_relationship(kind, source.id, target.id)
    bus = UmlCommandBus(make_document(source, target, relationship))
    before = bus.document

    with pytest.raises(UmlCommandExecutionError) as error:
        bus.execute(RemoveUmlElementCommand(elementId=source.id))

    assert error.value.code is UmlCommandErrorCode.INVALID_RESULTING_DOCUMENT
    assert bus.document == before
    assert not bus.can_undo
    assert not bus.can_redo
