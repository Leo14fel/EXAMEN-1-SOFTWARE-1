from uuid import UUID, uuid4

import pytest

from app.domain.relational.mapper import identifier, map_relational
from app.domain.relational.models import GenerationProfile
from app.domain.uml.models import CanonicalUmlModel, UmlAttribute, UmlClass


def uml_class(name="Cliente", attributes=None, identity=None):
    return UmlClass(
        id=identity or uuid4(), name=name, visibility="public", attributes=attributes or []
    )


def attribute(name="nombre", kind="String"):
    return UmlAttribute(name=name, type=kind, visibility="private")


@pytest.mark.parametrize(
    "source,target",
    [
        ("String", "text"),
        ("Integer", "integer"),
        ("Long", "bigint"),
        ("Decimal", "numeric"),
        ("Boolean", "boolean"),
        ("Date", "date"),
        ("DateTime", "timestamp with time zone"),
        ("UUID", "uuid"),
        ("Double", "double precision"),
    ],
)
def test_class_attribute_scalar_mapping_and_technical_primary_key(source, target):
    field = attribute(kind=source)
    cls = uml_class(attributes=[field])
    model = CanonicalUmlModel(elements=[cls])
    original = model.model_dump_json()
    result = map_relational(model)
    assert not result.diagnostics
    table = result.model.tables[0]
    assert table.source_class_id == cls.id
    assert table.primary_key == ["id"]
    assert table.columns[0].generated == "uuid" and not table.columns[0].nullable
    assert table.columns[1].sql_type == target and table.columns[1].nullable
    assert table.columns[1].source_attribute_id == field.id
    assert model.model_dump_json() == original
    assert map_relational(model).model_dump_json() == result.model_dump_json()


def test_explicit_profile_primary_key_required_unique_index_and_enum():
    key, email, state, count = (
        attribute("codigo"),
        attribute("correo"),
        attribute("estado", "Estado"),
        attribute("cantidad", "Integer"),
    )
    cls = uml_class(attributes=[key, email, state, count])
    profile = GenerationProfile.model_validate(
        {
            "classes": {
                str(cls.id): {"tableName": "clientes", "primaryKeyAttributeId": str(key.id)}
            },
            "attributes": {
                str(key.id): {"columnName": "codigo"},
                str(email.id): {
                    "required": True,
                    "unique": True,
                    "indexed": True,
                    "columnName": "correo",
                },
                str(count.id): {"indexed": True, "columnName": "cantidad"},
            },
            "enumTypes": {"Estado": ["ABIERTO", "CERRADO"]},
        }
    )
    result = map_relational(CanonicalUmlModel(elements=[cls]), profile)
    table = result.model.tables[0]
    assert table.name == "clientes" and table.primary_key == ["codigo"]
    assert not next(c for c in table.columns if c.name == "codigo").nullable
    assert table.unique_constraints == [["correo"]]
    assert [index.columns for index in table.indexes] == [["cantidad"]]
    enum = next(c for c in table.columns if c.source_attribute_id == state.id)
    assert enum.allowed_values == ["ABIERTO", "CERRADO"] and enum.enum_name == "Estado"


def test_unknown_type_invalid_uml_and_stale_profile_return_no_partial_model():
    cls = uml_class(attributes=[attribute(kind="Unknown")])
    result = map_relational(CanonicalUmlModel(elements=[cls]))
    assert result.model is None and result.diagnostics[-1].code == "TYPE_UNSUPPORTED"
    valid = uml_class()
    stale = GenerationProfile.model_validate({"attributes": {str(uuid4()): {"required": True}}})
    assert (
        map_relational(CanonicalUmlModel(elements=[valid]), stale).diagnostics[-1].code
        == "PROFILE_REFERENCE_UNKNOWN"
    )
    duplicate = CanonicalUmlModel(elements=[valid, uml_class(valid.name)])
    assert map_relational(duplicate).model is None


def test_sql_names_are_bounded_ascii_stable_and_explicit_collisions_are_rejected():
    identity = UUID(int=1)
    name = identifier("t", 'Árbol; DROP TABLE "X"' * 20, identity)
    assert name.isascii() and len(name.encode()) <= 63
    assert all(c.isalnum() or c == "_" for c in name)
    assert name == identifier("t", 'Árbol; DROP TABLE "X"' * 20, identity)
    a, b = uml_class("A"), uml_class("B")
    profile = GenerationProfile.model_validate(
        {"classes": {str(a.id): {"tableName": "same"}, str(b.id): {"tableName": "same"}}}
    )
    assert (
        map_relational(CanonicalUmlModel(elements=[b, a]), profile).diagnostics[-1].code
        == "TABLE_NAME_COLLISION"
    )


def test_profile_enum_values_and_identifier_overrides_are_validated():
    for profile in (
        {"enumTypes": {"Estado": ["X", "X"]}},
        {"classes": {str(uuid4()): {"tableName": "bad;sql"}}},
    ):
        with pytest.raises(ValueError):
            GenerationProfile.model_validate(profile)


def test_order_of_input_does_not_change_output_or_source():
    a, b = uml_class("A"), uml_class("B")
    first = map_relational(CanonicalUmlModel(elements=[a, b]))
    second = map_relational(CanonicalUmlModel(elements=[b, a]))
    assert first.model_dump_json() == second.model_dump_json()


def relationship(source, target, source_bounds=(1, 1), target_bounds=(0, "*"), kind="association"):
    from app.domain.uml.models import (
        UmlAggregation,
        UmlAssociation,
        UmlComposition,
        UmlMultiplicity,
    )

    cls = {
        "association": UmlAssociation,
        "aggregation": UmlAggregation,
        "composition": UmlComposition,
    }[kind]
    return cls(
        sourceId=source.id,
        targetId=target.id,
        sourceMultiplicity=UmlMultiplicity(lower=source_bounds[0], upper=source_bounds[1]),
        targetMultiplicity=UmlMultiplicity(lower=target_bounds[0], upper=target_bounds[1]),
    )


@pytest.mark.parametrize(
    "src,dst,cardinality,fk_on_source,nullable,unique",
    [
        ((1, 1), (0, "*"), "oneToMany", False, False, False),
        ((0, 1), (0, "*"), "oneToMany", False, True, False),
        ((0, "*"), (1, 1), "manyToOne", True, False, False),
        ((0, 1), (0, 1), "oneToOne", False, True, True),
    ],
)
def test_foreign_key_side_nullability_and_uniqueness(
    src, dst, cardinality, fk_on_source, nullable, unique
):
    a, b = uml_class("Cliente"), uml_class("Pedido")
    rel = relationship(a, b, src, dst)
    result = map_relational(CanonicalUmlModel(elements=[b, rel, a]))
    assert result.model is not None
    relation = result.model.relations[0]
    assert relation.cardinality == cardinality
    table = next(
        t for t in result.model.tables if t.source_class_id == (a.id if fk_on_source else b.id)
    )
    assert relation.storage_table == table.name
    column = next(c for c in table.columns if c.name == relation.columns[0])
    assert column.nullable == nullable
    assert bool(table.unique_constraints) == unique
    assert table.foreign_keys[0].on_delete == "RESTRICT"
    assert bool(table.indexes) == (not unique)


def test_many_to_many_self_relation_uses_two_distinct_fks_and_composite_key():
    a = uml_class("Persona")
    rel = relationship(a, a, (0, "*"), (0, "*"))
    result = map_relational(CanonicalUmlModel(elements=[rel, a]))
    join = next(t for t in result.model.tables if t.source_relationship_id == rel.id)
    assert join.primary_key == ["source_id", "target_id"]
    assert len(join.foreign_keys) == 2
    assert len({fk.name for fk in join.foreign_keys}) == 2
    assert [index.columns for index in join.indexes] == [["target_id"]]
    assert not result.model.relations[0].requires_runtime_validation


def test_composition_cascade_and_advanced_bounds_are_explicit_not_claimed_enforced():
    a, b = uml_class("Todo"), uml_class("Parte")
    rel = relationship(a, b, (1, 1), (2, 5), "composition")
    model = CanonicalUmlModel(elements=[a, rel, b])
    original = model.model_dump_json()
    result = map_relational(model)
    assert result.model.relations[0].requires_runtime_validation
    part = next(t for t in result.model.tables if t.source_class_id == b.id)
    assert part.foreign_keys[0].on_delete == "CASCADE"
    assert result.diagnostics[0].code == "RELATION_RUNTIME_VALIDATION"
    assert model.model_dump_json() == original
    result.model.relations[0].target_multiplicity.lower = 0
    assert rel.target_multiplicity.lower == 2


def test_invalid_composition_and_zero_upper_are_errors_without_partial_plan():
    a, b = uml_class("A"), uml_class("B")
    for rel, code in (
        (relationship(a, b, (0, "*"), (0, "*"), "composition"), "COMPOSITION_OWNERSHIP"),
        (relationship(a, b, (0, 0), (0, "*")), "ZERO_MULTIPLICITY"),
    ):
        result = map_relational(CanonicalUmlModel(elements=[a, b, rel]))
        assert result.model is None and result.diagnostics[-1].code == code


def test_joined_inheritance_and_attribute_reference_follow_declared_parent_key_type():
    from app.domain.uml.models import UmlGeneralization

    key = attribute("codigo", "Long")
    root = uml_class("Base", [key])
    child = uml_class("Hijo")
    ref = attribute("hijo", "Hijo")
    owner = uml_class("Propietario", [ref])
    edge = UmlGeneralization(sourceId=child.id, targetId=root.id)
    profile = GenerationProfile.model_validate(
        {"classes": {str(root.id): {"primaryKeyAttributeId": str(key.id)}}}
    )
    result = map_relational(CanonicalUmlModel(elements=[owner, child, edge, root]), profile)
    assert result.model is not None
    child_table = next(t for t in result.model.tables if t.source_class_id == child.id)
    assert child_table.columns[0].sql_type == "bigint" and child_table.columns[0].generated is None
    assert child_table.foreign_keys[0].on_delete == "CASCADE"
    owner_table = next(t for t in result.model.tables if t.source_class_id == owner.id)
    assert (
        next(c for c in owner_table.columns if c.source_attribute_id == ref.id).sql_type == "bigint"
    )
    assert owner_table.foreign_keys[0].target_table == child_table.name


def test_multiple_inheritance_and_child_primary_key_override_are_rejected():
    from app.domain.uml.models import UmlGeneralization

    a, b, c = uml_class("A"), uml_class("B"), uml_class("C")
    one = UmlGeneralization(sourceId=c.id, targetId=a.id)
    two = UmlGeneralization(sourceId=c.id, targetId=b.id)
    result = map_relational(CanonicalUmlModel(elements=[a, b, c, one, two]))
    assert result.model is None and result.diagnostics[-1].code == "MULTIPLE_INHERITANCE"
    key = attribute("codigo")
    c.attributes.append(key)
    profile = GenerationProfile.model_validate(
        {"classes": {str(c.id): {"primaryKeyAttributeId": str(key.id)}}}
    )
    result = map_relational(CanonicalUmlModel(elements=[a, c, one]), profile)
    assert result.model is None and result.diagnostics[-1].code == "INHERITED_PRIMARY_KEY"


def test_relations_and_metadata_remain_deterministic_under_input_reordering():
    a, b = uml_class("A"), uml_class("B")
    r1, r2 = relationship(a, b), relationship(b, a, (0, "*"), (0, "*"), "aggregation")
    model = CanonicalUmlModel(elements=[a, b, r1, r2])
    first = map_relational(model)
    second = map_relational(CanonicalUmlModel(elements=list(reversed(model.elements))))
    assert first.model_dump_json() == second.model_dump_json()
