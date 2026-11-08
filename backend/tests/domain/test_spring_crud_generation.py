from uuid import UUID

import pytest

from app.domain.relational.mapper import map_relational
from app.domain.relational.models import GenerationProfile
from app.domain.uml.models import (
    CanonicalUmlModel,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlMultiplicity,
)
from app.generation.spring import UnsupportedGeneration, generate_spring_sources


def relational_fixture():
    name = UmlAttribute(id=UUID(int=11), name="nombre", type="String", visibility="private")
    number = UmlAttribute(id=UUID(int=12), name="edad", type="Integer", visibility="private")
    parent = UmlClass(
        id=UUID(int=1), name="Cliente", visibility="public", attributes=[name, number]
    )
    child = UmlClass(id=UUID(int=2), name="Pedido", visibility="public")
    relation = UmlAssociation(
        id=UUID(int=3),
        sourceId=parent.id,
        targetId=child.id,
        sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
        targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
    )
    profile = GenerationProfile.model_validate(
        {
            "classes": {
                str(parent.id): {"tableName": "clientes"},
                str(child.id): {"tableName": "pedidos"},
            },
            "attributes": {
                str(name.id): {"columnName": "nombre", "searchable": True, "sortable": True}
            },
        }
    )
    mapped = map_relational(CanonicalUmlModel(elements=[parent, child, relation]), profile)
    assert mapped.model is not None
    return mapped.model, profile


def test_fk_schema_and_navigation_are_rendered_in_both_directions():
    model, profile = relational_fixture()
    before = model.model_dump_json()
    files = generate_spring_sources(model, profile=profile)
    sql = files["schema.sql"]
    key = next(k for t in model.tables for k in t.foreign_keys)
    assert sql.index('CREATE TABLE "pedidos"') < sql.index("ALTER TABLE")
    assert f'ADD CONSTRAINT "{key.name}"' in sql
    assert 'REFERENCES "clientes" ("id") ON DELETE RESTRICT' in sql
    controllers = "\n".join(s for p, s in files.items() if p.endswith("Controller.java"))
    assert f"/references/{key.name}" in controllers
    assert f"/related/{key.name}" in controllers
    assert "ResponseEntity.noContent()" in controllers
    assert model.model_dump_json() == before
    entities = [s for p, s in files.items() if "/domain/" in p]
    import re

    assert all("_" not in field for s in entities for field in re.findall(r"private \S+ (\w+);", s))


def test_read_only_metadata_omits_mutations_and_explicit_search_sort_policy():
    model, profile = relational_fixture()
    profile.classes[UUID(int=1)].read_only = True
    files = generate_spring_sources(model, profile=profile)
    controller = next(
        s for p, s in files.items() if p.endswith("Controller.java") and '"/api/clientes"' in s
    )
    assert "@PostMapping" not in controller and "@PutMapping" not in controller
    assert "@DeleteMapping" not in controller and "@GetMapping" in controller
    service = next(
        s for p, s in files.items() if p.endswith("Service.java") and 'Map.entry("nombre"' in s
    )
    assert "String.class, true, true" in service
    assert "public void delete" not in service
    query = files["src/main/java/com/example/generated/application/QuerySupport.java"]
    assert "fields.get(" in query and "Invalid filter value" in query
    assert "root.<String>get(field.property())" in query
    assert "Sort.by(fields.get(id).property())" in query


def test_inputs_do_not_accept_generated_ids_and_updates_never_replace_identity():
    model, _ = relational_fixture()
    files = generate_spring_sources(model)
    inputs = [s for p, s in files.items() if p.endswith("Input.java")]
    assert all('@JsonProperty("id")' not in s for s in inputs)
    services = [s for p, s in files.items() if p.endswith("Service.java")]
    assert all(
        "entityManager.persist(entity)" in s and "repository.save(" not in s for s in services
    )
    assert "fail-on-unknown-properties=true" in files["src/main/resources/application.properties"]


def test_profiles_are_revalidated_and_unknown_or_nontext_search_rejected():
    model, profile = relational_fixture()
    profile.attributes[UUID(int=12)] = type(profile.attributes[UUID(int=11)])(searchable=True)
    with pytest.raises(UnsupportedGeneration, match="text"):
        generate_spring_sources(model, profile=profile)
    profile = GenerationProfile.model_validate(
        {"classes": {str(UUID(int=999)): {"readOnly": True}}}
    )
    with pytest.raises(UnsupportedGeneration, match="unknown"):
        generate_spring_sources(model, profile=profile)


def test_no_writes_or_credentials_are_present_in_sources_and_no_sql_from_client():
    model, profile = relational_fixture()
    files = generate_spring_sources(model, profile=profile)
    service = "\n".join(s for p, s in files.items() if p.endswith("Service.java"))
    assert "createNativeQuery" not in service
    assert "System.getenv" not in service
    errors = files["src/main/java/com/example/generated/errors/ApiErrors.java"]
    assert "exception.getMessage()" not in errors
    assert "HttpStatus.CONFLICT" in errors
    assert "HttpStatus.BAD_REQUEST" in errors


def test_java_dto_parameter_limit_is_checked_before_generation():
    from app.domain.relational.models import Column

    model, _ = relational_fixture()
    model.tables[0].columns.extend(
        Column(name=f"extra{i}", sqlType="text", nullable=True) for i in range(201)
    )
    with pytest.raises(UnsupportedGeneration, match="200 columns"):
        generate_spring_sources(model)
