import re
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.domain.uml.models import DomainModel, UmlMultiplicity

SqlType = Literal[
    "uuid",
    "text",
    "integer",
    "bigint",
    "numeric",
    "boolean",
    "date",
    "timestamp with time zone",
    "double precision",
]
SqlName = str


class ClassProfile(DomainModel):
    table_name: str | None = Field(
        default=None, alias="tableName", pattern=r"^[a-z][a-z0-9_]{0,62}$"
    )
    primary_key_attribute_id: UUID | None = Field(default=None, alias="primaryKeyAttributeId")


class AttributeProfile(DomainModel):
    column_name: str | None = Field(
        default=None, alias="columnName", pattern=r"^[a-z][a-z0-9_]{0,62}$"
    )
    required: bool = False
    unique: bool = False
    indexed: bool = False


class GenerationProfile(DomainModel):
    version: Literal[1] = 1
    classes: dict[UUID, ClassProfile] = Field(default_factory=dict)
    attributes: dict[UUID, AttributeProfile] = Field(default_factory=dict)
    enum_types: dict[str, list[str]] = Field(default_factory=dict, alias="enumTypes")

    @field_validator("enum_types")
    @classmethod
    def valid_enums(cls, values: dict[str, list[str]]) -> dict[str, list[str]]:
        for name, literals in values.items():
            if not name.strip() or name != name.strip() or not 1 <= len(literals) <= 256:
                raise ValueError("Enum must have a name and 1..256 values")
            if len(set(literals)) != len(literals) or any(
                not v.strip() or len(v) > 128 for v in literals
            ):
                raise ValueError("Enum values must be nonblank, unique and at most 128 characters")
        return values


class Column(DomainModel):
    name: SqlName
    sql_type: SqlType = Field(alias="sqlType")
    nullable: bool
    source_attribute_id: UUID | None = Field(default=None, alias="sourceAttributeId")
    generated: Literal["uuid"] | None = None
    enum_name: str | None = Field(default=None, alias="enumName")
    allowed_values: list[str] | None = Field(default=None, alias="allowedValues")


class ForeignKey(DomainModel):
    name: SqlName
    columns: list[SqlName]
    target_table: SqlName = Field(alias="targetTable")
    target_columns: list[SqlName] = Field(alias="targetColumns")
    on_delete: Literal["RESTRICT", "CASCADE"] = Field(default="RESTRICT", alias="onDelete")
    source_id: UUID = Field(alias="sourceId")


class Index(DomainModel):
    name: SqlName
    columns: list[SqlName]


class Table(DomainModel):
    name: SqlName
    source_class_id: UUID | None = Field(default=None, alias="sourceClassId")
    source_relationship_id: UUID | None = Field(default=None, alias="sourceRelationshipId")
    columns: list[Column]
    primary_key: list[SqlName] = Field(alias="primaryKey")
    foreign_keys: list[ForeignKey] = Field(default_factory=list, alias="foreignKeys")
    unique_constraints: list[list[SqlName]] = Field(default_factory=list, alias="uniqueConstraints")
    indexes: list[Index] = Field(default_factory=list)


class RelationalRelation(DomainModel):
    source_id: UUID = Field(alias="sourceId")
    kind: str
    source_table: str = Field(alias="sourceTable")
    target_table: str = Field(alias="targetTable")
    cardinality: Literal["oneToOne", "oneToMany", "manyToOne", "manyToMany", "inheritance"]
    storage_table: str = Field(alias="storageTable")
    columns: list[str]
    source_multiplicity: UmlMultiplicity | None = Field(default=None, alias="sourceMultiplicity")
    target_multiplicity: UmlMultiplicity | None = Field(default=None, alias="targetMultiplicity")
    requires_runtime_validation: bool = Field(default=False, alias="requiresRuntimeValidation")


class RelationalModel(DomainModel):
    version: Literal[1] = 1
    dialect: Literal["postgresql"] = "postgresql"
    inheritance_strategy: Literal["joined"] = Field(default="joined", alias="inheritanceStrategy")
    quoted_identifiers: Literal[True] = Field(default=True, alias="quotedIdentifiers")
    tables: list[Table]
    relations: list[RelationalRelation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_storage_graph(self) -> "RelationalModel":
        tables = {table.name: table for table in self.tables}
        if len(tables) != len(self.tables):
            raise ValueError("Duplicate table name")
        for table in self.tables:
            names = [column.name for column in table.columns]
            if len(set(names)) != len(names) or not table.primary_key:
                raise ValueError("Columns must be unique and a primary key is required")
            columns = {column.name: column for column in table.columns}
            identifiers = [
                table.name,
                *names,
                *[index.name for index in table.indexes],
                *[key.name for key in table.foreign_keys],
            ]
            if any(not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name) for name in identifiers):
                raise ValueError("Invalid SQL identifier")
            for group in [
                table.primary_key,
                *table.unique_constraints,
                *[index.columns for index in table.indexes],
            ]:
                if not group or len(group) != len(set(group)) or set(group) - columns.keys():
                    raise ValueError("Invalid key or index columns")
            if any(columns[name].nullable for name in table.primary_key):
                raise ValueError("Primary key must be nonnull")
            for key in table.foreign_keys:
                target = tables.get(key.target_table)
                if target is None or len(key.columns) != len(key.target_columns) or not key.columns:
                    raise ValueError("Foreign key target is invalid")
                targets = {column.name: column for column in target.columns}
                if set(key.columns) - columns.keys() or set(key.target_columns) - targets.keys():
                    raise ValueError("Foreign key columns are missing")
                if key.target_columns not in [target.primary_key, *target.unique_constraints]:
                    raise ValueError("Foreign key must reference a unique key")
                if any(
                    columns[a].sql_type != targets[b].sql_type
                    for a, b in zip(key.columns, key.target_columns, strict=True)
                ):
                    raise ValueError("Foreign key types must match")
        for relation in self.relations:
            if any(
                name not in tables
                for name in (
                    relation.source_table,
                    relation.target_table,
                    relation.storage_table,
                )
            ):
                raise ValueError("Relation references unknown table")
            if set(relation.columns) - {
                column.name for column in tables[relation.storage_table].columns
            }:
                raise ValueError("Relation storage columns are missing")
        return self


class MappingDiagnostic(DomainModel):
    severity: Literal["error", "warning"]
    code: str
    message: str
    source_id: UUID | None = Field(default=None, alias="sourceId")


class MappingResult(DomainModel):
    model: RelationalModel | None
    diagnostics: list[MappingDiagnostic] = Field(default_factory=list)
