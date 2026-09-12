# Flujo de trabajo recomendado

## Unidad de trabajo

```text
product.md
  + caso de uso aprobado
  + STATUS.md
        |
        v
incremento pequeño
        |
        v
pruebas -> revisión -> commit
```

## Antes de implementar

1. `git status`
2. `git branch --show-current`
3. revisar `/product.md`
4. revisar el CU actual
5. definir qué queda fuera de alcance

## Con OpenSpec/OpenCode

- `propose`: crear/refinar solamente el CU actual.
- revisar propuesta antes de aplicar.
- `apply`: ejecutar un bloque pequeño de tareas, no el CU completo si es grande.
- `verify`: validar únicamente cuando el incremento esté implementado.

## Gate por incremento

No avanzar si falla alguno de los checks aplicables:

- tests;
- typecheck;
- build;
- migraciones, cuando existan;
- criterios de aceptación del bloque.

## Commit

Un commit debe representar un cambio entendible y reversible.

Ejemplos:

```text
feat(uml): add canonical class model
test(uml): cover relationship validation
chore(db): initialize project migrations
```

## Ahorro de tokens

- Referenciar archivos en vez de volver a pegar su contenido.
- Dar al agente un solo CU.
- Delimitar explícitamente tareas y fuera de alcance.
- Pedir resumen de archivos cambiados y checks, no explicaciones repetitivas de todo el repositorio.
