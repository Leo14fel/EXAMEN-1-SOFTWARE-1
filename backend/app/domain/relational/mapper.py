import hashlib
import re
import unicodedata
from uuid import UUID

from app.domain.relational.models import (
    AttributeProfile,
    ClassProfile,
    Column,
    ForeignKey,
    GenerationProfile,
    Index,
    MappingDiagnostic,
    MappingResult,
    RelationalModel,
    RelationalRelation,
    Table,
)
from app.domain.uml.models import CanonicalUmlModel, UmlClass, UmlComposition, UmlGeneralization
from app.domain.uml.validation import validate_uml_model

SCALAR_TYPES = {
    "String": "text",
    "Text": "text",
    "string": "text",
    "Integer": "integer",
    "int": "integer",
    "Long": "bigint",
    "long": "bigint",
    "Decimal": "numeric",
    "BigDecimal": "numeric",
    "Boolean": "boolean",
    "boolean": "boolean",
    "bool": "boolean",
    "Date": "date",
    "DateTime": "timestamp with time zone",
    "Instant": "timestamp with time zone",
    "UUID": "uuid",
    "Double": "double precision",
    "Float": "double precision",
}
MAX_CLASSES = 2000
MAX_ATTRIBUTES = 20_000
MAX_RELATIONS = 10_000


class MappingIssue(ValueError):
    def __init__(self, code: str, message: str, source_id: UUID | None = None):
        self.diagnostic = MappingDiagnostic(
            severity="error", code=code, message=message, sourceId=source_id
        )
        super().__init__(message)


def identifier(prefix: str, label: str, identity: UUID) -> str:
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", label)
    ascii_text = unicodedata.normalize("NFKD", snake).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_") or "item"
    suffix = hashlib.sha256(str(identity).encode()).hexdigest()[:12]
    return f"{prefix}_{slug[: 63 - len(prefix) - 14]}_{suffix}"


def _unique(names: list[str], code: str, source_id: UUID | None = None) -> None:
    if len(names) != len(set(names)):
        raise MappingIssue(
            code, "Hay nombres de almacenamiento duplicados; revisa el perfil.", source_id
        )


def map_relational(
    model: CanonicalUmlModel, profile: GenerationProfile | None = None
) -> MappingResult:
    try:
        validation = validate_uml_model(model)
    except RecursionError:
        return MappingResult(
            model=None,
            diagnostics=[
                MappingDiagnostic(
                    severity="error",
                    code="INHERITANCE_DEPTH",
                    message="La herencia es demasiado profunda.",
                )
            ],
        )
    if not validation.is_valid:
        return MappingResult(
            model=None,
            diagnostics=[
                MappingDiagnostic(
                    severity="error",
                    code=item.code.value,
                    message=item.message,
                    sourceId=item.element_id,
                )
                for item in validation.diagnostics
                if item.severity.value == "error"
            ],
        )
    diagnostics: list[MappingDiagnostic] = []
    try:
        return MappingResult(
            model=_map(model, profile or GenerationProfile(), diagnostics), diagnostics=diagnostics
        )
    except MappingIssue as error:
        return MappingResult(model=None, diagnostics=[*diagnostics, error.diagnostic])


def _map(
    model: CanonicalUmlModel, profile: GenerationProfile, diagnostics: list[MappingDiagnostic]
) -> RelationalModel:
    classes = sorted(
        (item for item in model.elements if isinstance(item, UmlClass)), key=lambda c: str(c.id)
    )
    all_attributes = {attribute.id for cls in classes for attribute in cls.attributes}
    if (
        len(classes) > MAX_CLASSES
        or len(all_attributes) > MAX_ATTRIBUTES
        or len(model.elements) - len(classes) > MAX_RELATIONS
    ):
        raise MappingIssue("MODEL_LIMIT", "El modelo supera el límite de conversión relacional.")
    if (
        set(profile.classes) - {cls.id for cls in classes}
        or set(profile.attributes) - all_attributes
    ):
        raise MappingIssue(
            "PROFILE_REFERENCE_UNKNOWN", "El perfil referencia clases o atributos inexistentes."
        )
    if set(profile.enum_types) & ({cls.name for cls in classes} | set(SCALAR_TYPES)):
        raise MappingIssue(
            "ENUM_NAME_COLLISION", "Un enum coincide con un tipo de clase o primitivo."
        )
    parents: dict[UUID, UmlGeneralization] = {}
    for item in model.elements:
        if isinstance(item, UmlGeneralization):
            if item.source_id in parents:
                raise MappingIssue(
                    "MULTIPLE_INHERITANCE", "JOINED requiere un solo padre.", item.source_id
                )
            parents[item.source_id] = item
    pending = {cls.id: cls for cls in classes}
    ordered = []
    while pending:
        ready = sorted(
            (
                identity
                for identity in pending
                if identity not in parents or parents[identity].target_id not in pending
            ),
            key=str,
        )
        if not ready:
            raise MappingIssue("GENERALIZATION_CYCLE", "La herencia contiene un ciclo.")
        ordered.extend(pending.pop(identity) for identity in ready)
    classes = ordered
    classes_by_name = {cls.name: cls.id for cls in classes}
    tables: list[Table] = []
    by_id: dict[UUID, Table] = {}
    relations = []
    references = []
    for cls in classes:
        options = profile.classes.get(cls.id, ClassProfile())
        key_id = options.primary_key_attribute_id
        parent = parents.get(cls.id)
        if parent is not None and key_id is not None:
            raise MappingIssue(
                "INHERITED_PRIMARY_KEY", "La clase hija hereda la PK del padre.", cls.id
            )
        if key_id is not None and key_id not in {a.id for a in cls.attributes}:
            raise MappingIssue(
                "PRIMARY_KEY_ATTRIBUTE_UNKNOWN",
                "El identificador no pertenece a esta clase.",
                cls.id,
            )
        columns = (
            [] if key_id else [Column(name="id", sqlType="uuid", nullable=False, generated="uuid")]
        )
        if parent is not None:
            parent_key = _key_column(by_id[parent.target_id])
            columns = [
                Column(
                    name="id",
                    sqlType=parent_key.sql_type,
                    nullable=False,
                    sourceAttributeId=parent_key.source_attribute_id,
                )
            ]
        primary_key = ["id"] if key_id is None else []
        unique_constraints = []
        indexes = []
        for attribute in sorted(cls.attributes, key=lambda a: str(a.id)):
            metadata = profile.attributes.get(attribute.id, AttributeProfile())
            enum_values = profile.enum_types.get(attribute.type)
            sql_type = "text" if enum_values is not None else SCALAR_TYPES.get(attribute.type)
            is_reference = attribute.type in classes_by_name
            if is_reference:
                sql_type = "uuid"  # Resolve after all target PKs are available.
            if sql_type is None:
                raise MappingIssue(
                    "TYPE_UNSUPPORTED", f"Tipo no soportado: {attribute.type}", attribute.id
                )
            is_key = attribute.id == key_id
            if is_key and (
                sql_type not in {"uuid", "text", "integer", "bigint"} or enum_values or is_reference
            ):
                raise MappingIssue(
                    "PRIMARY_KEY_TYPE_UNSUPPORTED",
                    "Tipo de identificador no soportado.",
                    attribute.id,
                )
            name = metadata.column_name or identifier("c", attribute.name, attribute.id)
            if is_reference:
                references.append((cls.id, attribute.id, classes_by_name[attribute.type], name))
            columns.append(
                Column(
                    name=name,
                    sqlType=sql_type,
                    nullable=not (metadata.required or is_key),
                    sourceAttributeId=attribute.id,
                    enumName=attribute.type if enum_values else None,
                    allowedValues=list(enum_values) if enum_values else None,
                )
            )
            if is_key:
                primary_key = [name]
            elif metadata.unique:
                unique_constraints.append([name])
            elif metadata.indexed:
                indexes.append(
                    Index(name=identifier("ix", attribute.name, attribute.id), columns=[name])
                )
        _unique([c.name for c in columns], "COLUMN_NAME_COLLISION", cls.id)
        if cls.operations:
            diagnostics.append(
                MappingDiagnostic(
                    severity="warning",
                    code="METHODS_NOT_PERSISTED",
                    message="Los métodos no se convierten en columnas ni lógica de negocio.",
                    sourceId=cls.id,
                )
            )
        if (
            key_id is None
            and parent is None
            and any(a.name.lower() == "id" for a in cls.attributes)
        ):
            diagnostics.append(
                MappingDiagnostic(
                    severity="warning",
                    code="GENERATED_PRIMARY_KEY",
                    message="PK UUID técnica; configura el atributo id para usarlo como clave.",
                    sourceId=cls.id,
                )
            )
        table = Table(
            name=options.table_name or identifier("t", cls.name, cls.id),
            sourceClassId=cls.id,
            columns=columns,
            primaryKey=primary_key,
            uniqueConstraints=sorted(unique_constraints),
            indexes=indexes,
        )
        tables.append(table)
        by_id[cls.id] = table
        if parent is not None:
            target = by_id[parent.target_id]
            _add_fk(table, table.primary_key, target, parent.id, "CASCADE")
            relations.append(
                RelationalRelation(
                    sourceId=parent.id,
                    kind="generalization",
                    sourceTable=table.name,
                    targetTable=target.name,
                    cardinality="inheritance",
                    storageTable=table.name,
                    columns=table.primary_key,
                )
            )
    _unique([table.name for table in tables], "TABLE_NAME_COLLISION")
    for source_id, attribute_id, target_id, name in sorted(
        references, key=lambda item: str(item[1])
    ):
        table, target = by_id[source_id], by_id[target_id]
        column = next(column for column in table.columns if column.name == name)
        column.sql_type = _key_column(target).sql_type
        _add_fk(table, [name], target, attribute_id)
        relations.append(
            RelationalRelation(
                sourceId=attribute_id,
                kind="attributeReference",
                sourceTable=table.name,
                targetTable=target.name,
                cardinality="manyToOne",
                storageTable=table.name,
                columns=[name],
            )
        )
    _map_associations(model, tables, by_id, relations, diagnostics)
    _unique([table.name for table in tables], "TABLE_NAME_COLLISION")
    for table in tables:
        _unique([c.name for c in table.columns], "COLUMN_NAME_COLLISION", table.source_class_id)
        table.foreign_keys.sort(key=lambda fk: fk.name)
        table.indexes.sort(key=lambda index: index.name)
        table.unique_constraints.sort()
    return RelationalModel(
        tables=sorted(tables, key=lambda t: t.name),
        relations=sorted(relations, key=lambda r: str(r.source_id)),
    )


def _key_column(table: Table) -> Column:
    return next(column for column in table.columns if column.name == table.primary_key[0])


def _add_fk(
    table: Table, columns: list[str], target: Table, source_id: UUID, on_delete: str = "RESTRICT"
) -> None:
    table.foreign_keys.append(
        ForeignKey(
            name=identifier("fk", "_".join(columns), source_id),
            columns=columns,
            targetTable=target.name,
            targetColumns=target.primary_key,
            onDelete=on_delete,
            sourceId=source_id,
        )
    )
    covered = [
        table.primary_key,
        *table.unique_constraints,
        *[index.columns for index in table.indexes],
    ]
    if not any(group[: len(columns)] == columns for group in covered):
        table.indexes.append(
            Index(name=identifier("ix", "_".join(columns), source_id), columns=columns)
        )


def _map_associations(
    model: CanonicalUmlModel,
    tables: list[Table],
    by_id: dict[UUID, Table],
    relations: list[RelationalRelation],
    diagnostics: list[MappingDiagnostic],
) -> None:
    compositions: set[UUID] = set()
    for item in sorted(model.elements, key=lambda item: str(item.id)):
        if isinstance(item, (UmlClass, UmlGeneralization)):
            continue
        source, target = by_id[item.source_id], by_id[item.target_id]
        src, dst = item.source_multiplicity, item.target_multiplicity
        if src.upper == 0 or dst.upper == 0:
            raise MappingIssue(
                "ZERO_MULTIPLICITY", "El máximo cero requiere otra estrategia.", item.id
            )
        src_many, dst_many = src.upper != 1, dst.upper != 1
        composition = isinstance(item, UmlComposition)
        if composition:
            if src_many or item.target_id in compositions:
                raise MappingIssue(
                    "COMPOSITION_OWNERSHIP", "La composición requiere un tipo de owner.", item.id
                )
            compositions.add(item.target_id)
        if src_many and dst_many:
            table = Table(
                name=identifier("j", f"{source.name}_{target.name}", item.id),
                sourceRelationshipId=item.id,
                columns=[
                    Column(name="source_id", sqlType=_key_column(source).sql_type, nullable=False),
                    Column(name="target_id", sqlType=_key_column(target).sql_type, nullable=False),
                ],
                primaryKey=["source_id", "target_id"],
            )
            _add_fk(table, ["source_id"], source, item.id)
            _add_fk(table, ["target_id"], target, item.id)
            tables.append(table)
            columns, cardinality = table.primary_key, "manyToMany"
            needs_runtime = src.lower > 0 or dst.lower > 0 or src.upper != "*" or dst.upper != "*"
        else:
            table, referenced, bound = (source, target, dst) if src_many else (target, source, src)
            name = identifier("r", referenced.name, item.id)
            table.columns.append(
                Column(
                    name=name, sqlType=_key_column(referenced).sql_type, nullable=bound.lower == 0
                )
            )
            if not src_many and not dst_many:
                table.unique_constraints.append([name])
            _add_fk(table, [name], referenced, item.id, "CASCADE" if composition else "RESTRICT")
            columns = [name]
            cardinality = "manyToOne" if src_many else "oneToMany" if dst_many else "oneToOne"
            other = src if src_many else dst
            needs_runtime = (
                other.lower > 0 or (other.upper != "*" and other.upper != 1) or composition
            )
        relations.append(
            RelationalRelation(
                sourceId=item.id,
                kind=item.kind,
                sourceTable=source.name,
                targetTable=target.name,
                cardinality=cardinality,
                storageTable=table.name,
                columns=columns,
                sourceMultiplicity=src.model_copy(deep=True),
                targetMultiplicity=dst.model_copy(deep=True),
                requiresRuntimeValidation=needs_runtime,
            )
        )
        if needs_runtime:
            diagnostics.append(
                MappingDiagnostic(
                    severity="warning",
                    code="RELATION_RUNTIME_VALIDATION",
                    message="La cardinalidad o composición requiere validaciones entre objetos.",
                    sourceId=item.id,
                )
            )
