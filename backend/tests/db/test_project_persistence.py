from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy.dialects import postgresql

from app.db.projects import (
    ProjectRecord,
    list_projects,
    project_document_from_record,
    project_record_from_document,
    update_project_if_revision,
)
from app.domain.uml.models import (
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlAggregation,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlComposition,
    UmlGeneralization,
    UmlMultiplicity,
    UmlOperation,
    UmlParameter,
)

PROJECT_ID = UUID("11111111-1111-1111-1111-111111111111")
OWNER_ID = UUID("22222222-2222-2222-2222-222222222222")
CUSTOMER_ID = UUID("33333333-3333-3333-3333-333333333333")
ORDER_ID = UUID("44444444-4444-4444-4444-444444444444")
ATTRIBUTE_ID = UUID("55555555-5555-5555-5555-555555555555")
OPERATION_ID = UUID("66666666-6666-6666-6666-666666666666")
PARAMETER_ID = UUID("77777777-7777-7777-7777-777777777777")
RELATIONSHIP_ID = UUID("88888888-8888-8888-8888-888888888888")
CREATED_AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
UPDATED_AT = datetime(2026, 9, 20, 12, 1, tzinfo=UTC)


def make_document() -> ProjectDocument:
    customer = UmlClass(
        id=CUSTOMER_ID,
        name="Customer",
        visibility="public",
        attributes=[
            UmlAttribute(
                id=ATTRIBUTE_ID,
                name="email",
                type="String",
                visibility="private",
            )
        ],
        operations=[
            UmlOperation(
                id=OPERATION_ID,
                name="placeOrder",
                visibility="public",
                parameters=[UmlParameter(id=PARAMETER_ID, name="quantity", type="Integer")],
                returnType="Boolean",
            )
        ],
    )
    order = UmlClass(id=ORDER_ID, name="Order", visibility="public")
    association = UmlAssociation(
        id=RELATIONSHIP_ID,
        sourceId=CUSTOMER_ID,
        targetId=ORDER_ID,
        sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
        targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
    )
    aggregation = UmlAggregation(
        sourceId=ORDER_ID,
        targetId=CUSTOMER_ID,
        sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
        targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
    )
    composition = UmlComposition(
        sourceId=CUSTOMER_ID,
        targetId=ORDER_ID,
        sourceMultiplicity=UmlMultiplicity(lower=0, upper=1),
        targetMultiplicity=UmlMultiplicity(lower=1, upper="*"),
    )
    generalization = UmlGeneralization(sourceId=ORDER_ID, targetId=CUSTOMER_ID)
    return ProjectDocument(
        id=PROJECT_ID,
        ownerId=OWNER_ID,
        metadata={"name": "Sales", "nested": {"active": True}},
        revision=4,
        createdAt=CREATED_AT,
        updatedAt=UPDATED_AT,
        umlModel=CanonicalUmlModel(
            elements=[customer, order, association, aggregation, composition, generalization]
        ),
        diagramLayout=DiagramLayout(
            nodes={
                CUSTOMER_ID: DiagramNodeLayout(x=10, y=20, width=220, height=160),
                ORDER_ID: DiagramNodeLayout(x=320, y=20, width=220, height=160),
            }
        ),
    )


def test_project_document_round_trips_through_project_record() -> None:
    document = make_document()

    restored = project_document_from_record(project_record_from_document(document))

    assert restored == document
    assert restored.uml_model.elements[0].id == CUSTOMER_ID
    assert restored.diagram_layout.nodes[CUSTOMER_ID].x == 10
    assert [element.kind for element in restored.uml_model.elements[2:]] == [
        "association",
        "aggregation",
        "composition",
        "generalization",
    ]
    assert restored.uml_model.elements[2].source_multiplicity == UmlMultiplicity(lower=1, upper=1)
    assert restored.uml_model.elements[4].target_multiplicity == UmlMultiplicity(lower=1, upper="*")


def test_list_projects_orders_by_updated_at_descending() -> None:
    class ScalarResult:
        def all(self) -> list[ProjectRecord]:
            return []

    class FakeSession:
        statement: object | None = None

        def scalars(self, statement: object) -> ScalarResult:
            self.statement = statement
            return ScalarResult()

    session = FakeSession()

    assert list_projects(session) == []  # type: ignore[arg-type]
    assert session.statement is not None
    compiled = str(session.statement.compile(dialect=postgresql.dialect()))  # type: ignore[union-attr]
    assert "ORDER BY projects.updated_at DESC" in compiled


def test_update_project_uses_id_and_revision_compare_and_swap() -> None:
    class FakeSession:
        statement: object | None = None

        def execute(self, statement: object) -> SimpleNamespace:
            self.statement = statement
            return SimpleNamespace(rowcount=1)

    session = FakeSession()
    document = make_document()

    assert update_project_if_revision(session, document, 3) is True  # type: ignore[arg-type]
    assert session.statement is not None
    compiled = str(session.statement.compile(dialect=postgresql.dialect()))  # type: ignore[union-attr]
    assert "WHERE projects.id = %(id_1)s::UUID AND projects.revision = %(revision_1)s" in compiled
