"""Bounded XMI 2.1 adapter for the canonical UML subset, without fetching resources."""

from io import BytesIO
from uuid import NAMESPACE_URL, UUID, uuid5

from lxml import etree
from pydantic import ValidationError

from app.domain.uml.models import CanonicalUmlModel, DomainModel, UmlClass
from app.domain.uml.validation import validate_uml_model
from app.interoperability.xmi.exporter import UML_NAMESPACE, XMI_NAMESPACE

MAX_XMI_BYTES = 2 * 1024 * 1024
MAX_XML_NODES = 50_000
MAX_XML_DEPTH = 64
XMI_NAMESPACES = {XMI_NAMESPACE, "http://www.omg.org/XMI"}
UML_NAMESPACES = {UML_NAMESPACE, "http://schema.omg.org/spec/UML/2.1"}


class XmiImportError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class XmiImportResult(DomainModel):
    name: str
    model: CanonicalUmlModel
    warnings: list[str]


def _local(node: etree._Element) -> str:
    return etree.QName(node).localname if isinstance(node.tag, str) else ""


def _xmi(node: etree._Element, name: str) -> str | None:
    values = [node.get(f"{{{namespace}}}{name}") for namespace in XMI_NAMESPACES]
    values = [value for value in values if value is not None]
    if len(values) > 1:
        raise XmiImportError("XMI_AMBIGUOUS_ATTRIBUTE", "Ambiguous XMI attribute")
    return values[0] if values else None


def _kind(node: etree._Element) -> str:
    value = _xmi(node, "type")
    if value:
        prefix, separator, name = value.partition(":")
        if not separator or node.nsmap.get(prefix) not in UML_NAMESPACES:
            raise XmiImportError("XMI_UNSUPPORTED_TYPE", "Unrecognized UML type namespace")
        return name
    return _local(node)


def _identity(node: etree._Element) -> str:
    value = _xmi(node, "id")
    if not value:
        raise XmiImportError("XMI_MISSING_ID", "A UML element has no XMI identifier")
    return value


def _uuid(value: str) -> UUID:
    try:
        return UUID(value[3:]) if value.startswith("id_") else UUID(value)
    except ValueError:
        return uuid5(NAMESPACE_URL, f"xmi:{value}")


def _children(node: etree._Element, tag: str) -> list[etree._Element]:
    return [child for child in node if _local(child) == tag]


def _parse(data: bytes) -> tuple[etree._Element, list[etree._Element]]:
    if not data or len(data) > MAX_XMI_BYTES:
        raise XmiImportError("XMI_SIZE_LIMIT", "XMI must contain at most 2 MiB")
    try:
        stream = etree.iterparse(
            BytesIO(data),
            events=("start", "end"),
            resolve_entities=False,
            load_dtd=False,
            no_network=True,
            huge_tree=False,
            remove_comments=True,
        )
        depth = count = 0
        for event, _ in stream:
            if event == "start":
                count += 1
                depth += 1
                if count > MAX_XML_NODES or depth > MAX_XML_DEPTH:
                    raise XmiImportError("XMI_STRUCTURE_LIMIT", "XMI structure exceeds limits")
            else:
                depth -= 1
        root = stream.root
    except etree.XMLSyntaxError as error:
        raise XmiImportError("XMI_INVALID_XML", "Invalid XML document") from error
    if root.getroottree().docinfo.doctype:
        raise XmiImportError("XMI_DTD_FORBIDDEN", "DTD and entities are not supported")
    if etree.QName(root).namespace not in XMI_NAMESPACES or _local(root) != "XMI":
        raise XmiImportError("XMI_INVALID_ROOT", "Expected an XMI 2.1 document")
    if _xmi(root, "version") != "2.1":
        raise XmiImportError("XMI_UNSUPPORTED_VERSION", "Only XMI 2.1 is supported")
    nodes = [
        node
        for node in root.iter()
        if isinstance(node.tag, str)
        and not any(_local(parent) == "Extension" for parent in node.iterancestors())
        and _local(node) != "Extension"
    ]
    ids = [_xmi(node, "id") for node in nodes if _xmi(node, "id") is not None]
    if len(ids) != len(set(ids)):
        raise XmiImportError("XMI_DUPLICATE_ID", "Duplicate XMI identifier")
    return root, nodes


def import_xmi(data: bytes) -> XmiImportResult:
    root, nodes = _parse(data)
    try:
        return _convert(root, nodes)
    except (ValidationError, ValueError, KeyError) as error:
        if isinstance(error, XmiImportError):
            raise
        raise XmiImportError("XMI_INVALID_MODEL", "XMI does not form a valid UML model") from error


def _convert(root: etree._Element, nodes: list[etree._Element]) -> XmiImportResult:
    for node in nodes:
        if etree.QName(node).namespace not in {*XMI_NAMESPACES, *UML_NAMESPACES, None}:
            raise XmiImportError("XMI_UNSUPPORTED_NAMESPACE", "Unsupported content namespace")
        if any(
            node.get(key) in {"true", "1"}
            for key in (
                "isAbstract",
                "isStatic",
                "isReadOnly",
                "isDerived",
            )
        ):
            raise XmiImportError("XMI_UNSUPPORTED_FEATURE", "Unsupported UML modifiers")
    models = [node for node in nodes if _local(node) == "Model"]
    if len(models) != 1:
        raise XmiImportError("XMI_MODEL_COUNT", "Exactly one UML Model is required")
    warnings = []
    known_tags = {
        "XMI",
        "Model",
        "packagedElement",
        "Class",
        "Package",
        "PrimitiveType",
        "DataType",
        "Association",
        "Generalization",
        "generalization",
        "ownedAttribute",
        "ownedOperation",
        "ownedParameter",
        "ownedEnd",
        "type",
        "lowerValue",
        "upperValue",
    }
    known_attributes = {
        "name",
        "visibility",
        "type",
        "direction",
        "memberEnd",
        "specific",
        "general",
        "lower",
        "upper",
        "aggregation",
        "association",
        "value",
        "version",
        "id",
        "idref",
        "isAbstract",
        "isStatic",
        "isReadOnly",
        "isDerived",
    }
    if any(_local(node) not in known_tags for node in nodes):
        warnings.append("Contenido XML adicional no representado en el subconjunto UML actual.")
    if any(
        etree.QName(key).localname not in known_attributes for node in nodes for key in node.attrib
    ):
        warnings.append("Propiedades adicionales del archivo no representadas en el modelo actual.")
    if any(_local(node) == "Extension" for node in root.iter()):
        warnings.append("Extensiones del proveedor y posiciones de diagramas no importadas.")
    packaged = [node for node in nodes if _local(node) == "packagedElement"]
    allowed = {"Class", "PrimitiveType", "DataType", "Association", "Generalization", "Package"}
    for node in packaged:
        if _kind(node) not in allowed:
            raise XmiImportError("XMI_UNSUPPORTED_ELEMENT", "Unsupported packaged UML element")
        if _kind(node) in {"PrimitiveType", "DataType"} and any(
            _local(child) in {"ownedAttribute", "ownedOperation"} for child in node
        ):
            raise XmiImportError("XMI_UNSUPPORTED_ELEMENT", "Structured data types are unsupported")
    if any(_kind(node) == "Package" for node in packaged):
        warnings.append("Los paquetes se aplanaron; su estructura no pertenece al modelo actual.")
    types = {
        _identity(node): node.get("name", "")
        for node in nodes
        if _kind(node) in {"Class", "PrimitiveType", "DataType"}
    }
    class_nodes = [node for node in nodes if _kind(node) == "Class"]
    class_ids = {_identity(node) for node in class_nodes}
    end_nodes = {
        _identity(node): node
        for node in nodes
        if _local(node) == "ownedEnd"
        or (_local(node) == "ownedAttribute" and node.get("association"))
    }

    def type_name(node: etree._Element) -> str:
        reference = node.get("type")
        if not reference:
            nested = _children(node, "type")
            reference = _xmi(nested[0], "idref") if len(nested) == 1 else None
        if not reference or reference.removeprefix("#") not in types:
            raise XmiImportError("XMI_UNKNOWN_TYPE", "Type reference is missing or unresolved")
        return types[reference.removeprefix("#")]

    def member(node: etree._Element) -> dict:
        return {"id": _uuid(_identity(node)), "name": node.get("name", ""), "type": type_name(node)}

    classes = []
    for node in class_nodes:
        if any(
            _local(child) in {"nestedClassifier", "ownedBehavior", "ownedReception"}
            for child in node
        ):
            raise XmiImportError("XMI_UNSUPPORTED_ELEMENT", "Unsupported classifier content")
        for attribute in _children(node, "ownedAttribute"):
            if _identity(attribute) not in end_nodes and (
                attribute.get("lower", "1") != "1"
                or attribute.get("upper", "1") != "1"
                or any(
                    child.get("value", "1") != "1"
                    for child in attribute
                    if _local(child) in {"lowerValue", "upperValue"}
                )
            ):
                raise XmiImportError(
                    "XMI_UNSUPPORTED_FEATURE",
                    "Attribute multiplicity is not represented by the model",
                )
        attributes = [
            {**member(child), "visibility": child.get("visibility", "public")}
            for child in _children(node, "ownedAttribute")
            if _identity(child) not in end_nodes
        ]
        operations = []
        for child in _children(node, "ownedOperation"):
            parameters = _children(child, "ownedParameter")
            if any(
                parameter.get("direction", "in") not in {"in", "return"} for parameter in parameters
            ):
                raise XmiImportError(
                    "XMI_PARAMETER_DIRECTION", "Only input and return are supported"
                )
            returns = [
                parameter for parameter in parameters if parameter.get("direction") == "return"
            ]
            if len(returns) > 1:
                raise XmiImportError("XMI_MULTIPLE_RETURNS", "An operation has multiple returns")
            operations.append(
                {
                    "id": _uuid(_identity(child)),
                    "name": child.get("name", ""),
                    "visibility": child.get("visibility", "public"),
                    "parameters": [
                        member(parameter)
                        for parameter in parameters
                        if parameter.get("direction", "in") == "in"
                    ],
                    "returnType": type_name(returns[0]) if returns else None,
                }
            )
        classes.append(
            UmlClass(
                id=_uuid(_identity(node)),
                name=node.get("name", ""),
                visibility=node.get("visibility", "public"),
                attributes=attributes,
                operations=operations,
            )
        )
    elements = list(classes)

    def class_ref(reference: str | None) -> UUID:
        if not reference or reference not in class_ids:
            raise XmiImportError("XMI_UNKNOWN_CLASS", "Relationship references an unknown class")
        return _uuid(reference)

    def multiplicity(end: etree._Element) -> dict:
        bounds = {}
        for key in ("lower", "upper"):
            child = _children(end, f"{key}Value")
            value = end.get(key, child[0].get("value", "1") if child else "1")
            bounds[key] = "*" if key == "upper" and value in {"*", "-1"} else int(value)
        return bounds

    for node in nodes:
        if _kind(node) == "Association":
            references = node.get("memberEnd", "").split()
            ends = (
                [end_nodes[reference] for reference in references]
                if references
                else _children(node, "ownedEnd")
            )
            if len(ends) != 2 or ends[0] is ends[1]:
                raise XmiImportError(
                    "XMI_ASSOCIATION_ARITY", "Only binary associations are supported"
                )
            aggregated = [end for end in ends if end.get("aggregation", "none") != "none"]
            if len(aggregated) > 1 or any(
                end.get("aggregation", "none") not in {"none", "shared", "composite"}
                for end in ends
            ):
                raise XmiImportError("XMI_AGGREGATION", "Unsupported aggregation ends")
            if aggregated and ends[0] is aggregated[0]:
                ends.reverse()
            kind = {"none": "association", "shared": "aggregation", "composite": "composition"}[
                ends[1].get("aggregation", "none")
            ]
            elements.append(
                {
                    "id": _uuid(_identity(node)),
                    "kind": kind,
                    "sourceId": class_ref(ends[0].get("type")),
                    "targetId": class_ref(ends[1].get("type")),
                    "sourceMultiplicity": multiplicity(ends[0]),
                    "targetMultiplicity": multiplicity(ends[1]),
                }
            )
        elif _kind(node) == "Generalization" or _local(node) == "generalization":
            parent = node.getparent()
            specific = node.get("specific") or (
                _xmi(parent, "id") if parent in class_nodes else None
            )
            elements.append(
                {
                    "id": _uuid(_identity(node)),
                    "kind": "generalization",
                    "sourceId": class_ref(specific),
                    "targetId": class_ref(node.get("general")),
                }
            )
    model = CanonicalUmlModel(elements=elements)
    validation = validate_uml_model(model)
    if not validation.is_valid:
        raise XmiImportError("XMI_SEMANTIC_ERROR", "UML validation rejected the imported model")
    return XmiImportResult(
        name=models[0].get("name", "").strip() or "Proyecto importado",
        model=model,
        warnings=warnings,
    )
