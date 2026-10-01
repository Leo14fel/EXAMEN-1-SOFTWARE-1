from datetime import UTC, datetime
from uuid import UUID

from lxml import etree

from app.domain.uml.models import (
    CanonicalUmlModel,
    ProjectDocument,
    UmlAggregation,
    UmlAttribute,
    UmlClass,
    UmlComposition,
    UmlGeneralization,
    UmlMultiplicity,
    UmlOperation,
    UmlParameter,
    UmlVisibility,
)
from app.interoperability.xmi.exporter import UML_NAMESPACE, XMI_NAMESPACE, export_project_document


def test_exports_canonical_model_as_deterministic_xmi_21() -> None:
    customer = UmlClass(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="Customer",
        visibility=UmlVisibility.PUBLIC,
        attributes=[
            UmlAttribute(
                id=UUID("22222222-2222-2222-2222-222222222222"),
                name="name",
                type="String",
                visibility=UmlVisibility.PRIVATE,
            )
        ],
        operations=[
            UmlOperation(
                id=UUID("33333333-3333-3333-3333-333333333333"),
                name="findOrders",
                visibility=UmlVisibility.PUBLIC,
                parameters=[
                    UmlParameter(
                        id=UUID("44444444-4444-4444-4444-444444444444"),
                        name="limit",
                        type="Integer",
                    )
                ],
                returnType="Boolean",
            )
        ],
    )
    order = UmlClass(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        name="Order",
        visibility=UmlVisibility.PUBLIC,
    )
    multiplicity_many = UmlMultiplicity(lower=0, upper="*")
    document = ProjectDocument(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        ownerId=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        metadata={"name": "Sales Model"},
        createdAt=datetime(2026, 9, 22, tzinfo=UTC),
        updatedAt=datetime(2026, 9, 22, tzinfo=UTC),
        umlModel=CanonicalUmlModel(
            elements=[
                customer,
                order,
                UmlAggregation(
                    id=UUID("66666666-6666-6666-6666-666666666666"),
                    sourceId=customer.id,
                    targetId=order.id,
                    sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
                    targetMultiplicity=multiplicity_many,
                ),
                UmlComposition(
                    id=UUID("77777777-7777-7777-7777-777777777777"),
                    sourceId=order.id,
                    targetId=order.id,
                    sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
                    targetMultiplicity=multiplicity_many,
                ),
                UmlGeneralization(
                    id=UUID("88888888-8888-8888-8888-888888888888"),
                    sourceId=order.id,
                    targetId=customer.id,
                ),
            ]
        ),
    )

    exported = export_project_document(document)
    root = etree.fromstring(exported)

    assert root.nsmap == {"xmi": XMI_NAMESPACE, "uml": UML_NAMESPACE}
    assert root.get(f"{{{XMI_NAMESPACE}}}version") == "2.1"
    assert root.xpath("string(uml:Model/@name)", namespaces=root.nsmap) == "Sales Model"
    assert (
        root.xpath(
            "count(.//uml:packagedElement[@xmi:type='uml:PrimitiveType'])", namespaces=root.nsmap
        )
        == 3.0
    )
    assert root.xpath("string(.//uml:ownedAttribute/@type)", namespaces=root.nsmap).startswith(
        "primitive_"
    )
    assert (
        root.xpath(
            "string(.//uml:ownedParameter[@direction='return']/@name)", namespaces=root.nsmap
        )
        == "return"
    )
    assert (
        root.xpath("string(.//uml:ownedEnd[@aggregation='shared']/@upper)", namespaces=root.nsmap)
        == "*"
    )
    assert (
        root.xpath("count(.//uml:ownedEnd[@aggregation='composite'])", namespaces=root.nsmap)
        == 1.0
    )
    assert (
        root.xpath(
            "string(.//uml:packagedElement[@xmi:type='uml:Generalization']/@specific)",
            namespaces=root.nsmap,
        )
        == "id_55555555555555555555555555555555"
    )
    assert export_project_document(document) == exported
    assert b"diagramLayout" not in exported


def test_removes_xml_unsafe_name_characters() -> None:
    document = ProjectDocument(
        metadata={"name": "Valid\x01 name"},
        ownerId=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    )

    root = etree.fromstring(export_project_document(document))

    assert root.xpath("string(uml:Model/@name)", namespaces=root.nsmap) == "Valid name"
