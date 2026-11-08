from uuid import uuid4

import pytest

from app.domain.uml.models import (
    CanonicalUmlModel,
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
from app.interoperability.xmi import importer
from app.interoperability.xmi.exporter import export_project_document
from app.interoperability.xmi.importer import XmiImportError, import_xmi


def rich_document():
    a = UmlClass(
        name="Cliente",
        visibility="public",
        attributes=[
            UmlAttribute(name="nombre", type="String", visibility="private"),
            UmlAttribute(name="pedido", type="Pedido", visibility="public"),
        ],
        operations=[
            UmlOperation(
                name="buscar",
                visibility="public",
                parameters=[UmlParameter(name="pedido", type="Pedido")],
                returnType="Cliente",
            )
        ],
    )
    b = UmlClass(name="Pedido", visibility="package")
    return ProjectDocument(
        ownerId=uuid4(),
        metadata={"name": "Modelo de prueba"},
        umlModel=CanonicalUmlModel(
            elements=[
                a,
                b,
                UmlComposition(
                    sourceId=a.id,
                    targetId=b.id,
                    sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
                    targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
                ),
                UmlAssociation(
                    sourceId=b.id,
                    targetId=b.id,
                    sourceMultiplicity=UmlMultiplicity(lower=0, upper=1),
                    targetMultiplicity=UmlMultiplicity(lower=1, upper=3),
                ),
                UmlAggregation(
                    sourceId=a.id,
                    targetId=b.id,
                    sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
                    targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
                ),
                UmlGeneralization(sourceId=b.id, targetId=a.id),
            ]
        ),
    )


def xml(body):
    return (
        """<?xml version="1.0"?><xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
    xmlns:uml="http://www.omg.org/spec/UML/20161101" xmi:version="2.1">
    <uml:Model xmi:id="model" name="Modelo">"""
        + body
        + "</uml:Model></xmi:XMI>"
    ).encode()


def test_round_trip_preserves_supported_semantics_ids_and_type_references():
    document = rich_document()
    exported = export_project_document(document)
    imported = import_xmi(exported)
    assert imported.model == document.uml_model
    assert imported.name == "Modelo de prueba"
    assert imported.warnings == []
    again = ProjectDocument(
        ownerId=uuid4(), metadata={"name": imported.name}, umlModel=imported.model
    )
    assert import_xmi(export_project_document(again)).model == document.uml_model


def test_external_ids_packages_unqualified_features_and_nested_generalization():
    data = xml("""<packagedElement xmi:type="uml:Package" xmi:id="p">
      <packagedElement xmi:type="uml:Class" xmi:id="EAID_A" name="A">
        <generalization xmi:id="g" general="EAID_B" />
      </packagedElement>
      <packagedElement xmi:type="uml:Class" xmi:id="EAID_B" name="B" />
    </packagedElement>""")
    first = import_xmi(data)
    assert first.model == import_xmi(data).model
    assert len(first.warnings) == 1
    a, b, g = first.model.elements
    assert g.source_id == a.id and g.target_id == b.id
    assert a.id != b.id


@pytest.mark.parametrize(
    "body, code",
    [
        ('<packagedElement xmi:type="uml:Interface" xmi:id="i" />', "XMI_UNSUPPORTED_ELEMENT"),
        (
            '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A"/><packagedEl'
            'ement xmi:type="uml:Class" xmi:id="a" name="B"/>',
            "XMI_DUPLICATE_ID",
        ),
        (
            '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A"><ownedAttrib'
            'ute xmi:id="attr" name="x" type="missing"/>'
            "</packagedElement>",
            "XMI_UNKNOWN_TYPE",
        ),
        (
            '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A"><generalizat'
            'ion xmi:id="g" general="a"/>'
            "</packagedElement>",
            "XMI_SEMANTIC_ERROR",
        ),
        (
            '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A"/><packagedEl'
            'ement xmi:type="uml:Class" xmi:id="b" name="A"/>',
            "XMI_SEMANTIC_ERROR",
        ),
        (
            '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A" isAbstract="true"/>',
            "XMI_UNSUPPORTED_FEATURE",
        ),
    ],
)
def test_invalid_or_unsupported_semantics_are_rejected(body, code):
    with pytest.raises(XmiImportError) as error:
        import_xmi(xml(body))
    assert error.value.code == code


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_dtd_external_entities_never_become_uml_content(encoding):
    payload = xml('<packagedElement xmi:type="uml:Class" xmi:id="a" name="A"/>').decode()
    payload = payload.replace(
        '<?xml version="1.0"?>',
        f'<?xml version="1.0" encoding="{encoding}"?><!DOCTYPE xmi:XMI [<!ENTITY xxe SYSTEM "file:///not-to-read">]>',
    )
    with pytest.raises(XmiImportError) as error:
        import_xmi(payload.encode(encoding))
    assert error.value.code == "XMI_DTD_FORBIDDEN"


def test_size_depth_node_limit_version_and_malformed_xml(monkeypatch):
    for data in (b"not xml", xml("").replace(b'2.1"', b'2.5"'), b""):
        with pytest.raises(XmiImportError):
            import_xmi(data)
    with monkeypatch.context() as patch:
        patch.setattr(importer, "MAX_XMI_BYTES", 10)
        with pytest.raises(XmiImportError, match="2 MiB"):
            import_xmi(xml(""))
    with monkeypatch.context() as patch:
        patch.setattr(importer, "MAX_XML_DEPTH", 3)
        with pytest.raises(XmiImportError) as error:
            import_xmi(xml("<a><b><c/></b></a>"))
        assert error.value.code == "XMI_STRUCTURE_LIMIT"
    monkeypatch.setattr(importer, "MAX_XML_NODES", 2)
    with pytest.raises(XmiImportError) as error:
        import_xmi(xml("<a/>"))
    assert error.value.code == "XMI_STRUCTURE_LIMIT"


def test_vendor_extensions_are_reported_without_importing_layout_or_duplicate_ids():
    data = xml('<packagedElement xmi:type="uml:Class" xmi:id="a" name="A"/>')
    data = data.replace(
        b"</xmi:XMI>", b'<xmi:Extension><node xmi:id="a" x="20" y="40" /></xmi:Extension></xmi:XMI>'
    )
    result = import_xmi(data)
    assert len(result.model.elements) == 1 and result.warnings
    assert "diagramLayout" not in result.model.model_dump()


@pytest.mark.parametrize("feature", ['upper="*"', 'isReadOnly="true"', 'isDerived="1"'])
def test_does_not_silently_drop_attribute_features(feature):
    body = (
        '<packagedElement xmi:type="uml:PrimitiveType" xmi:id="s" name="String"/>'
        '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A">'
        f'<ownedAttribute xmi:id="x" name="x" type="s" {feature}/>'
        "</packagedElement>"
    )
    with pytest.raises(XmiImportError) as error:
        import_xmi(xml(body))
    assert error.value.code == "XMI_UNSUPPORTED_FEATURE"


def test_extra_metadata_and_unknown_xml_are_reported_as_warnings():
    result = import_xmi(
        xml(
            '<packagedElement xmi:type="uml:Class" xmi:id="a" name="A" vendorFlag="yes">'
            "<ownedComment/></packagedElement>"
        )
    )
    assert len(result.warnings) == 2
    assert result.model.elements[0].name == "A"
