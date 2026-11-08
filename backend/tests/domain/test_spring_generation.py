from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.relational.mapper import map_relational
from app.domain.relational.models import GenerationProfile, RelationalModel
from app.domain.uml.models import CanonicalUmlModel, UmlAttribute, UmlClass
from app.generation.spring import (
    SpringOptions,
    UnsupportedGeneration,
    generate_spring_sources,
)


def scalar_model():
    attributes = [
        UmlAttribute(id=UUID(int=10 + index), name=name, type=kind, visibility="private")
        for index, (name, kind) in enumerate(
            [
                ("nombre", "String"),
                ("edad", "Integer"),
                ("saldo", "Decimal"),
                ("activo", "Boolean"),
                ("fecha", "Date"),
                ("hora", "DateTime"),
                ("codigo", "Long"),
                ("ratio", "Double"),
                ("referencia", "UUID"),
            ]
        )
    ]
    cls = UmlClass(id=UUID(int=1), name="Cliente", visibility="public", attributes=attributes)
    return map_relational(CanonicalUmlModel(elements=[cls])).model


def test_source_foundation_is_deterministic_without_mutating_model():
    model = scalar_model()
    original = model.model_dump_json()
    files = generate_spring_sources(model)
    assert generate_spring_sources(model) == files
    assert model.model_dump_json() == original
    assert list(files) == sorted(files)
    assert "4.1.2" in files["build.gradle"]
    assert "JavaLanguageVersion.of(21)" in files["build.gradle"]
    assert "spring-boot-starter-webmvc" in files["build.gradle"]
    assert "spring-boot-starter-data-jpa" in files["build.gradle"]
    assert "springdoc-openapi-starter-webmvc-ui:3.2.0" in files["build.gradle"]
    entity = next(text for path, text in files.items() if "/domain/" in path)
    for java_type in (
        "String",
        "Integer",
        "Long",
        "Boolean",
        "Double",
        "java.math.BigDecimal",
        "java.time.LocalDate",
        "java.time.OffsetDateTime",
        "java.util.UUID",
    ):
        assert f"private {java_type} " in entity
    assert "GenerationType.UUID" in entity
    assert all(not path.startswith(("/", "..")) and "\\" not in path for path in files)
    assert "ddl-auto=validate" in files["src/main/resources/application.properties"]
    assert "${DB_PASSWORD}" in files["src/main/resources/application.properties"]
    assert any("Controller.java" in path for path in files)


@pytest.mark.parametrize(
    "package",
    [
        "../escape",
        "com.class",
        "java.custom",
        "com.hello;evil",
        "com.bad-name",
        "single",
        "com.\\u0061",
        "com._",
        "com..empty",
        "com.Upper",
        "jakarta.custom",
    ],
)
def test_reject_package_injection_and_reserved_segments(package):
    with pytest.raises(ValidationError):
        SpringOptions(packageName=package)


@pytest.mark.parametrize("name", ["../escape", "x'\nplugins {}", "a/b", "a\\b", "", "Upper"])
def test_reject_build_artifact_injection(name):
    with pytest.raises(ValidationError):
        SpringOptions(artifactName=name)


def test_constraints_enums_literals_and_identifier_collisions():
    fields = [
        UmlAttribute(id=UUID(int=10), name="a", type="Status", visibility="private"),
        UmlAttribute(id=UUID(int=11), name="b", type="String", visibility="private"),
    ]
    cls = UmlClass(id=UUID(int=1), name="Clase", visibility="public", attributes=fields)
    literals = ["Activo", "O'Reilly", 'quote"; //', "barra\\u000a", "línea\nsiguiente"]
    profile = GenerationProfile.model_validate(
        {
            "classes": {str(cls.id): {"tableName": "order"}},
            "attributes": {
                str(fields[0].id): {"columnName": "a_b", "required": True, "indexed": True},
                str(fields[1].id): {"columnName": "a__b", "unique": True},
            },
            "enumTypes": {"Status": literals},
        }
    )
    mapped = map_relational(CanonicalUmlModel(elements=[cls]), profile)
    assert mapped.model is not None
    files = generate_spring_sources(mapped.model, SpringOptions(packageName="org.demo.app"))
    entity = next(text for path, text in files.items() if "/domain/" in path)
    assert '@Table(name = "order")' in entity
    assert entity.count("private String ") == 2
    fields_generated = [line.strip() for line in entity.splitlines() if "private String" in line]
    assert len(set(fields_generated)) == 2
    assert "@AllowedValues" in entity and "@NotNull" in entity
    assert '"order"' in files["schema.sql"]
    assert "O''Reilly" in files["schema.sql"]
    assert "CREATE INDEX" in files["schema.sql"]
    assert 'UNIQUE ("a__b")' in files["schema.sql"]
    assert '"a_b" text NOT NULL CHECK' in files["schema.sql"]
    assert 'quote\\"; //' in entity


def test_explicit_identity_is_assigned_not_invented_and_output_order_is_stable():
    model = scalar_model()
    table = model.tables[0]
    table.columns[0].generated = None
    table.columns.reverse()
    first = generate_spring_sources(model)
    table.columns.reverse()
    assert generate_spring_sources(model) == first
    entity = next(text for path, text in first.items() if "/domain/" in path)
    assert "@GeneratedValue" not in entity


def test_revalidate_mutated_model_and_options_before_render():
    model = scalar_model()
    model.tables[0].name = 'bad"; DROP TABLE users; --'
    with pytest.raises(ValidationError):
        generate_spring_sources(model)
    options = SpringOptions()
    options.package_name = "../../escape"
    with pytest.raises(ValidationError):
        generate_spring_sources(scalar_model(), options)


def test_no_partial_sources_for_composite_keys_or_schema_namespace_collisions():
    model = scalar_model()
    table = model.tables[0]
    other = table.columns[1]
    other.nullable = False
    table.primary_key.append(other.name)
    with pytest.raises(UnsupportedGeneration, match="Composite"):
        generate_spring_sources(model)
    model = scalar_model()
    from app.domain.relational.models import Index

    model.tables[0].indexes = [Index(name=model.tables[0].name, columns=["id"])]
    with pytest.raises(UnsupportedGeneration, match="schema-wide"):
        generate_spring_sources(model)


def test_reject_unrepresentable_enum_data_and_invalid_generated_identity():
    for value in ["nul\x00byte", "surrogate\ud800"]:
        model = scalar_model()
        column = next(c for c in model.tables[0].columns if c.sql_type == "text")
        column.allowed_values = [value]
        with pytest.raises(UnsupportedGeneration):
            generate_spring_sources(model)
    model = scalar_model()
    model.tables[0].columns[1].generated = "uuid"
    with pytest.raises(UnsupportedGeneration, match="primary key"):
        generate_spring_sources(model)


def test_empty_model_produces_only_valid_application_foundation():
    files = generate_spring_sources(RelationalModel(tables=[]))
    assert not any("/domain/" in path for path in files)
    assert "COMMIT;" in files["schema.sql"]
    assert "GeneratedApplication" in next(
        text for path, text in files.items() if path.endswith("GeneratedApplication.java")
    )


def test_relationships_and_runtime_obligations_are_not_silently_dropped():
    model = scalar_model()
    table = model.tables[0]
    from app.domain.relational.models import RelationalRelation

    model.relations.append(
        RelationalRelation(
            sourceId=UUID(int=500),
            kind="association",
            sourceTable=table.name,
            targetTable=table.name,
            cardinality="manyToMany",
            storageTable=table.name,
            columns=["id"],
            requiresRuntimeValidation=True,
        )
    )
    with pytest.raises(UnsupportedGeneration, match="runtime"):
        generate_spring_sources(model)
