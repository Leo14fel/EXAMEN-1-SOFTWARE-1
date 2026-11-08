"""Create an isolated reproducible CU-14 compile fixture (no database writes).

Run from backend: python -m tests.manual.spring_foundation_probe
The printed project path can be built with Gradle 9.5.1 / Java 21.
"""

import json
from pathlib import Path
from uuid import UUID, uuid4

from app.domain.relational.mapper import map_relational
from app.domain.relational.models import GenerationProfile
from app.domain.uml.models import CanonicalUmlModel, UmlAttribute, UmlClass
from app.generation.spring import generate_spring_sources


def main() -> None:
    columns = [
        UmlAttribute(id=UUID(int=10 + index), name=name, type=kind, visibility="private")
        for index, (name, kind) in enumerate(
            [
                ("nombre", "String"),
                ("cantidad", "Integer"),
                ("importe", "Decimal"),
                ("activo", "Boolean"),
                ("fecha", "Date"),
                ("instante", "DateTime"),
                ("codigo", "Long"),
                ("ratio", "Double"),
                ("referencia", "UUID"),
                ("estado", "Estado"),
            ]
        )
    ]
    entity = UmlClass(id=UUID(int=1), name="Pedido", visibility="public", attributes=columns)
    profile = GenerationProfile.model_validate(
        {
            "classes": {str(entity.id): {"tableName": "order"}},
            "attributes": {
                str(columns[0].id): {"required": True, "unique": True, "indexed": True},
                str(columns[-1].id): {"required": True},
            },
            "enumTypes": {
                "Estado": ["ACTIVO", "O'Reilly", 'quote"; //', "barra\\u000a", "línea\nsiguiente"]
            },
        }
    )
    mapping = map_relational(CanonicalUmlModel(elements=[entity]), profile)
    if mapping.model is None:
        raise RuntimeError("Fixture mapping failed")
    files = generate_spring_sources(mapping.model)
    root = Path(__file__).resolve().parents[3] / "artifacts" / "cu14" / str(uuid4())
    for path, source in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8", newline="\n")
    # This test executes the generated Jakarta validators, not a mocked renderer.
    test = root / "src/test/java/com/example/generated/FoundationContractTest.java"
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text(
        '''package com.example.generated;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Table;
import jakarta.validation.Validation;
import jakarta.validation.constraints.NotNull;
import com.example.generated.validation.AllowedValues;
import java.lang.reflect.Field;

class FoundationContractTest {
    @Test void generatedConstraintsAcceptDeclaredLiteralsAndRejectInvalidValues() throws Exception {
        Class<?> type = Class.forName("ENTITY_CLASS");
        assertEquals("order", type.getAnnotation(Table.class).name());
        Object entity = type.getConstructor().newInstance();
        Field enumField = null;
        for (Field field : type.getDeclaredFields()) {
            field.setAccessible(true);
            if (field.isAnnotationPresent(NotNull.class) && field.getType() == String.class) {
                field.set(entity, "required value");
            }
            if (field.isAnnotationPresent(AllowedValues.class)) enumField = field;
        }
        assertNotNull(enumField);
        assertEquals(1, java.util.Arrays.stream(type.getDeclaredFields())
            .filter(f -> f.isAnnotationPresent(GeneratedValue.class)).count());
        try (var factory = Validation.buildDefaultValidatorFactory()) {
            var validator = factory.getValidator();
            for (String literal : enumField.getAnnotation(AllowedValues.class).value()) {
                enumField.set(entity, literal);
                assertTrue(validator.validate(entity).isEmpty());
            }
            enumField.set(entity, "UNDECLARED");
            assertFalse(validator.validate(entity).isEmpty());
            enumField.set(entity, null);
            assertFalse(validator.validate(entity).isEmpty());
        }
    }
}
'''.replace(
            "ENTITY_CLASS",
            next(
                path.removeprefix("src/main/java/").removesuffix(".java").replace("/", ".")
                for path in files
                if "/domain/" in path
            ),
        ),
        encoding="utf-8",
    )
    (root.parent / "latest.json").write_text(
        json.dumps({"path": str(root), "databaseWrites": False}, indent=2), encoding="utf-8"
    )
    print(root)


if __name__ == "__main__":
    main()
