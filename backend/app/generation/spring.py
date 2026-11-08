"""Render a Java CRUD backend without filesystem access or code execution."""

import hashlib
import json
import re

from jinja2 import Environment, PackageLoader, StrictUndefined
from pydantic import Field, field_validator

from app.domain.relational.models import GenerationProfile, RelationalModel, Table
from app.domain.uml.models import DomainModel

JAVA_KEYWORDS = frozenset(
    "abstract assert boolean break byte case catch char class const continue default do "
    "double else enum extends final finally float for goto if implements import instanceof "
    "int interface long native new package private protected public return short static "
    "strictfp super switch synchronized this throw throws transient try void volatile while "
    "true false null _ var yield record sealed permits module open opens requires exports "
    "provides uses transitive with to when".split()
)
JAVA_TYPES = {
    "uuid": "java.util.UUID",
    "text": "String",
    "integer": "Integer",
    "bigint": "Long",
    "numeric": "java.math.BigDecimal",
    "boolean": "Boolean",
    "date": "java.time.LocalDate",
    "timestamp with time zone": "java.time.OffsetDateTime",
    "double precision": "Double",
}


class SpringOptions(DomainModel):
    package_name: str = Field(default="com.example.generated", alias="packageName", max_length=180)
    artifact_name: str = Field(
        default="generated-backend", alias="artifactName", pattern=r"^[a-z][a-z0-9-]{0,63}$"
    )

    @field_validator("package_name")
    @classmethod
    def valid_package(cls, value: str) -> str:
        if any(
            not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", part) or part in JAVA_KEYWORDS
            for part in value.split(".")
        ) or value.split(".")[0] in {"java", "javax", "jakarta"}:
            raise ValueError("Use a qualified Java package with safe, nonreserved segments")
        if "." not in value:
            raise ValueError("A qualified Java package is required")
        return value


class UnsupportedGeneration(ValueError):
    """The requested model cannot be generated completely by this increment."""


def _java_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _sql_string(value: str) -> str:
    if "\x00" in value:
        raise UnsupportedGeneration("PostgreSQL text cannot contain NUL")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise UnsupportedGeneration("Text must be valid UTF-8") from exc
    return "'" + value.replace("'", "''") + "'"


def _symbol(prefix: str, sql_name: str) -> str:
    # SQL overrides may differ only in underscore runs: preserve distinct Java names.
    digest = hashlib.sha256(sql_name.encode()).hexdigest()[:10]
    words = "".join(part.capitalize() for part in sql_name.split("_") if part)
    # Spring Data treats underscores as property-path separators, even for Sort.
    return f"{prefix}{words[:48]}X{digest}"


def _table_context(table: Table, profile: GenerationProfile) -> dict:
    columns = []
    for column in sorted(table.columns, key=lambda item: item.name):
        if column.allowed_values is not None and (
            column.sql_type != "text" or not column.allowed_values
        ):
            raise UnsupportedGeneration("Enum constraints require nonempty text values")
        if column.generated and (column.sql_type != "uuid" or column.name not in table.primary_key):
            raise UnsupportedGeneration("Only a UUID primary key can be generated")
        field = _symbol("value", column.name)
        attribute = profile.attributes.get(column.source_attribute_id)
        if attribute and attribute.searchable and column.sql_type != "text":
            raise UnsupportedGeneration("Only text attributes can be searchable")
        columns.append(
            {
                "name": column.name,
                "field": field,
                "accessor": field[0].upper() + field[1:],
                "java_type": JAVA_TYPES[column.sql_type],
                "sql_type": column.sql_type,
                "nullable": column.nullable,
                "is_id": column.name in table.primary_key,
                "generated": column.generated,
                "allowed_values": column.allowed_values,
                "searchable": bool(attribute and attribute.searchable),
                "sortable": bool(attribute and attribute.sortable)
                or column.name in table.primary_key,
            }
        )
    identity = next(item for item in columns if item["is_id"])
    class_profile = profile.classes.get(table.source_class_id)
    return {
        "name": table.name,
        "class_name": _symbol("Entity", table.name),
        "columns": columns,
        "id_type": identity["java_type"],
        "identity": identity,
        "write_columns": [item for item in columns if not item["generated"]],
        "read_only": bool(class_profile and class_profile.read_only),
        "foreign_keys": sorted(table.foreign_keys, key=lambda item: item.name),
        "outgoing": [],
        "incoming": [],
        "primary_key": table.primary_key,
        "unique_constraints": sorted(table.unique_constraints),
        "indexes": sorted(table.indexes, key=lambda item: item.name),
    }


def generate_spring_sources(
    model: RelationalModel,
    options: SpringOptions | None = None,
    profile: GenerationProfile | None = None,
) -> dict[str, str]:
    """Return relative POSIX paths and UTF-8 source; no partial output on errors."""
    # Revalidate even mutable Pydantic instances before interpolating identifiers.
    model = RelationalModel.model_validate(model.model_dump(by_alias=True))
    options = SpringOptions.model_validate((options or SpringOptions()).model_dump(by_alias=True))
    profile = GenerationProfile.model_validate(
        (profile or GenerationProfile()).model_dump(by_alias=True)
    )
    if any(len(table.columns) > 200 for table in model.tables):
        raise UnsupportedGeneration("At most 200 columns per table are supported by Java DTOs")
    if any(len(table.primary_key) != 1 or table.source_relationship_id for table in model.tables):
        raise UnsupportedGeneration(
            "Composite identities and many-to-many join tables are unsupported"
        )
    if any(
        r.requires_runtime_validation or r.cardinality == "inheritance" for r in model.relations
    ):
        raise UnsupportedGeneration(
            "Relationships requiring runtime rules or inheritance are unsupported"
        )
    if profile.classes.keys() - {t.source_class_id for t in model.tables} or (
        profile.attributes.keys() - {c.source_attribute_id for t in model.tables for c in t.columns}
    ):
        raise UnsupportedGeneration("Generation profile references unknown source elements")
    tables = [
        _table_context(table, profile) for table in sorted(model.tables, key=lambda item: item.name)
    ]
    by_name = {table["name"]: table for table in tables}
    for table in tables:
        for key in table["foreign_keys"]:
            target = by_name[key.target_table]
            if len(key.columns) != 1 or key.target_columns != target["primary_key"]:
                raise UnsupportedGeneration(
                    "Only single-column references to primary keys are supported"
                )
            column = next(c for c in table["columns"] if c["name"] == key.columns[0])
            dependency = target["class_name"]
            reference = {
                "key": key.name,
                "column": column,
                "table": target,
                "service": "service" if target is table else "related" + dependency,
            }
            table["outgoing"].append(reference)
            target["incoming"].append(
                {
                    "key": key.name,
                    "column": column,
                    "table": table,
                    "service": "service" if target is table else "related" + table["class_name"],
                }
            )
    for table in tables:
        dependencies = {
            r["table"]["class_name"]: r["table"]
            for r in [*table["outgoing"], *table["incoming"]]
            if r["table"] is not table
        }
        table["dependencies"] = [dependencies[name] for name in sorted(dependencies)]
        if len(table["dependencies"]) > 200:
            raise UnsupportedGeneration(
                "At most 200 related entity types per controller are supported"
            )
    # SQL names were validated above. Reject schema-wide index collisions as well.
    schema_names = [table["name"] for table in tables] + [
        index.name for table in tables for index in table["indexes"]
    ]
    if len(schema_names) != len(set(schema_names)):
        raise UnsupportedGeneration("Tables and indexes must have distinct schema-wide names")
    environment = Environment(
        loader=PackageLoader("app.generation", "templates"),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    environment.filters["java_string"] = _java_string
    environment.filters["sql_string"] = _sql_string
    context = {"options": options, "tables": tables}
    outputs = {
        "settings.gradle": "settings.gradle.j2",
        "build.gradle": "build.gradle.j2",
        "src/main/resources/application.properties": "application.properties.j2",
        "schema.sql": "schema.sql.j2",
        "README.md": "README.md.j2",
        ".gitignore": "gitignore.j2",
    }
    java_root = "src/main/java/" + options.package_name.replace(".", "/")
    outputs[f"{java_root}/GeneratedApplication.java"] = "application.java.j2"
    outputs[f"{java_root}/validation/AllowedValues.java"] = "allowed-values.java.j2"
    outputs[f"{java_root}/validation/AllowedValuesValidator.java"] = "enum-validator.java.j2"
    outputs[f"{java_root}/application/QuerySupport.java"] = "query.java.j2"
    outputs[f"{java_root}/errors/ApiErrors.java"] = "errors.java.j2"
    files = {
        path: environment.get_template(template).render(**context)
        for path, template in outputs.items()
    }
    for table in tables:
        for suffix, folder, template in (
            ("", "domain", "entity.java.j2"),
            ("Repository", "persistence", "repository.java.j2"),
            ("View", "api", "view.java.j2"),
            ("Input", "api", "input.java.j2"),
            ("Service", "application", "service.java.j2"),
            ("Controller", "api", "controller.java.j2"),
        ):
            path = f"{java_root}/{folder}/{table['class_name']}{suffix}.java"
            files[path] = environment.get_template(template).render(**context, table=table)
    return dict(sorted(files.items()))
