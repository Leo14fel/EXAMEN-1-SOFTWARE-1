"""Build and exercise CU-14 against a disposable local PostgreSQL database.

Run from backend: python -m tests.manual.spring_crud_probe
Reads existing local SQL credentials privately; never reads/writes the legacy DB.
Creates only cu14_<UUID> and drops exactly that database in finally.
"""

import json
import os
import re
import shutil
import socket
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.domain.relational.mapper import map_relational
from app.domain.relational.models import GenerationProfile
from app.domain.uml.models import (
    CanonicalUmlModel,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlMultiplicity,
)
from app.generation.spring import generate_spring_sources


def fixture():
    def attr(identity, name, kind):
        return UmlAttribute(id=UUID(int=identity), name=name, type=kind, visibility="private")

    cliente = UmlClass(
        id=UUID(int=1),
        name="Cliente",
        visibility="public",
        attributes=[
            attr(11, "codigo", "String"),
            attr(12, "nombre", "String"),
            attr(13, "edad", "Integer"),
        ],
    )
    pedido = UmlClass(
        id=UUID(int=2),
        name="Pedido",
        visibility="public",
        attributes=[
            attr(21, "total", "Decimal"),
            attr(22, "estado", "Estado"),
            attr(23, "fecha", "Date"),
            attr(24, "activo", "Boolean"),
            attr(25, "instante", "DateTime"),
            attr(26, "numero", "Long"),
            attr(27, "ratio", "Double"),
            attr(28, "referencia", "UUID"),
        ],
    )
    catalogo = UmlClass(
        id=UUID(int=3),
        name="Catalogo",
        visibility="public",
        attributes=[
            attr(31, "codigo", "Integer"),
            attr(32, "etiqueta", "String"),
        ],
    )
    perfil = UmlClass(id=UUID(int=4), name="Perfil", visibility="public")
    relations = [
        UmlAssociation(
            id=UUID(int=100),
            sourceId=cliente.id,
            targetId=pedido.id,
            sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
            targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
        ),
        UmlAssociation(
            id=UUID(int=101),
            sourceId=cliente.id,
            targetId=perfil.id,
            sourceMultiplicity=UmlMultiplicity(lower=0, upper=1),
            targetMultiplicity=UmlMultiplicity(lower=0, upper=1),
        ),
        UmlAssociation(
            id=UUID(int=102),
            sourceId=cliente.id,
            targetId=cliente.id,
            sourceMultiplicity=UmlMultiplicity(lower=0, upper=1),
            targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
        ),
    ]
    profile = GenerationProfile.model_validate(
        {
            "classes": {
                str(cliente.id): {
                    "tableName": "clientes",
                    "primaryKeyAttributeId": str(UUID(int=11)),
                },
                str(pedido.id): {"tableName": "pedidos"},
                str(catalogo.id): {
                    "tableName": "catalogo",
                    "readOnly": True,
                    "primaryKeyAttributeId": str(UUID(int=31)),
                },
                str(perfil.id): {"tableName": "perfiles"},
            },
            "attributes": {
                str(a.id): {
                    "columnName": a.name,
                    **(
                        {"required": True, "unique": True, "searchable": True, "sortable": True}
                        if a.id == UUID(int=12)
                        else {"sortable": True}
                        if a.id == UUID(int=13)
                        else {"required": True}
                        if a.id in {UUID(int=21), UUID(int=22)}
                        else {}
                    ),
                }
                for c in [cliente, pedido, catalogo]
                for a in c.attributes
            },
            "enumTypes": {"Estado": ["NUEVO", "O'Reilly", "barra\\u000a", "línea\nsiguiente"]},
        }
    )
    result = map_relational(
        CanonicalUmlModel(elements=[cliente, pedido, catalogo, perfil, *relations]), profile
    )
    if result.model is None:
        raise RuntimeError("Probe fixture mapping failed")
    return result.model, profile


def main():
    root = Path(__file__).resolve().parents[3]
    run = root / "artifacts" / "cu14" / ("crud-" + uuid4().hex)
    run.mkdir(parents=True)
    model, profile = fixture()
    for name, text in generate_spring_sources(model, profile=profile).items():
        target = run / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    gradle = next(
        (Path.home() / ".gradle/wrapper/dists/gradle-9.5.1-bin").glob(
            "*/gradle-9.5.1/bin/gradle.bat"
        ),
        None,
    )
    if gradle is None:
        raise RuntimeError("Gradle 9.5.1 is required for this probe")
    with (run / "gradle.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            [str(gradle), "--no-daemon", "--console=plain", "build"],
            cwd=run,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    print("Generated CRUD compiled", flush=True)
    origin = make_url(settings.database_url)
    if origin.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Probe requires local PostgreSQL")
    credentials = dict(
        host=origin.host,
        port=origin.port or 5432,
        user=origin.username,
        password=origin.password,
        connect_timeout=5,
    )
    database = "cu14_" + uuid4().hex
    assert re.fullmatch(r"cu14_[0-9a-f]{32}", database) and database != origin.database
    created = False
    server = None
    server_log = None
    passed = []
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    java = shutil.which("java")
    jar = next(p for p in (run / "build/libs").glob("*.jar") if not p.name.endswith("-plain.jar"))
    environment = {
        **os.environ,
        "DB_URL": f"jdbc:postgresql://{origin.host}:{origin.port or 5432}/{database}",
        "DB_USER": origin.username,
        "DB_PASSWORD": origin.password,
        "PORT": str(port),
    }

    def launch():
        nonlocal server_log
        server_log = (run / ("server-" + uuid4().hex + ".log")).open("w", encoding="utf-8")
        process = subprocess.Popen(
            [java, "-jar", str(jar), "--server.address=127.0.0.1"],
            env=environment,
            cwd=run,
            stdout=server_log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for _ in range(120):
            if process.poll() is not None:
                raise RuntimeError(f"Generated server exited; inspect local logs in {run}")
            try:
                if (
                    httpx.get(f"http://127.0.0.1:{port}/api/catalogo/count", timeout=1).status_code
                    == 200
                ):
                    return process
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
        process.terminate()
        process.wait(timeout=15)
        raise RuntimeError("Generated server readiness timed out")

    def stop():
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
        if server_log:
            server_log.close()

    try:
        with psycopg.connect(dbname="postgres", autocommit=True, **credentials) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
            created = True
        with psycopg.connect(dbname=database, autocommit=True, **credentials) as connection:
            connection.execute((run / "schema.sql").read_text(encoding="utf-8"))
            connection.execute(
                'INSERT INTO "catalogo" ("codigo", "etiqueta") VALUES (1, %s)', ("Solo lectura",)
            )
        passed.append("schema applied with PK/FK/UNIQUE/CHECK/indexes")
        server = launch()
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10) as client:

            def request(method, path, expected=200, **kwargs):
                response = client.request(method, "/api/" + path, **kwargs)
                assert response.status_code == expected, (
                    method,
                    path,
                    response.status_code,
                    response.text[:600],
                )
                passed.append(f"{method} {path}: {expected}")
                return response.json() if response.content else None

            cid = "C / ? # % ü"
            first = {"codigo": cid, "nombre": "Ana %_ Uno", "edad": 25}
            request("POST", "clientes", 201, json=first)
            request("POST", "clientes", 409, json={**first, "nombre": "No sobrescribir"})
            assert request("GET", "clientes/item", params={"id": cid})["nombre"] == first["nombre"]
            request("POST", "clientes", 409, json={"codigo": "otro", "nombre": first["nombre"]})
            request("POST", "clientes", 400, json={"codigo": "x"})
            request("POST", "clientes", 400, json={**first, "unknown": "x"})
            request("POST", "clientes", 400, json={"codigo": "nul", "nombre": "a\x00b"})
            request("GET", "clientes/item", 400, params={"id": "a\x00b"})
            request("POST", "clientes", 201, json={"codigo": "B", "nombre": "Bruno", "edad": 40})
            page = request(
                "GET", "clientes", params={"size": 1, "sort": "edad", "direction": "desc"}
            )
            assert page["total"] == 2 and page["items"][0]["codigo"] == "B"
            page = request("GET", "clientes", params={"q": "%_"})
            assert page["total"] == 1 and page["items"][0]["codigo"] == cid
            assert request("GET", "clientes/count", params={"filter.edad": "25"}) == 1
            for query in [
                {"size": 0},
                {"sort": "nombre; drop"},
                {"filter.edad": "invalid"},
                {"filter.unknown": "x"},
                {"surprise": "x"},
                {"direction": "evil"},
                {"filter.nombre": "a\x00b"},
                {"q": "a\x00b"},
            ]:
                request("GET", "clientes", 400, params=query)
            request("GET", "clientes", 400, params=[("size", "1"), ("size", "2")])
            request(
                "PUT", "clientes/item", 400, params={"id": cid}, json={**first, "codigo": "changed"}
            )
            updated = request(
                "PUT", "clientes/item", params={"id": cid}, json={**first, "edad": 26}
            )
            assert updated["edad"] == 26
            request("GET", "clientes/item", 404, params={"id": "missing"})
            keys = {t.name: t.foreign_keys[0] for t in model.tables if t.foreign_keys}
            fk = keys["pedidos"]
            payload = {
                "total": "12.34",
                "estado": "NUEVO",
                "fecha": "2026-11-07",
                "activo": True,
                "instante": "2026-11-07T12:00:00Z",
                "numero": 9223372036854770000,
                "ratio": 0.75,
                "referencia": str(UUID(int=999)),
                fk.columns[0]: cid,
            }
            request("POST", "pedidos", 409, json={**payload, fk.columns[0]: "missing"})
            request("POST", "pedidos", 400, json={**payload, "estado": "INVALID"})
            request("POST", "pedidos", 400, json={**payload, "id": str(uuid4())})
            order = request("POST", "pedidos", 201, json=payload)
            assert order["total"] == 12.34 and order["numero"] == payload["numero"]
            assert (
                request("GET", "pedidos/references/" + fk.name, params={"id": order["id"]})[
                    "codigo"
                ]
                == cid
            )
            related = request("GET", "clientes/related/" + fk.name, params={"id": cid})
            assert related["total"] == 1 and related["items"][0]["id"] == order["id"]
            request("DELETE", "clientes/item", 409, params={"id": cid})
            pk = keys["perfiles"]
            empty_profile = request("POST", "perfiles", 201, json={})
            request(
                "GET", "perfiles/references/" + pk.name, 204, params={"id": empty_profile["id"]}
            )
            request("POST", "perfiles", 201, json={pk.columns[0]: cid})
            request("POST", "perfiles", 409, json={pk.columns[0]: cid})
            self_key = keys["clientes"]
            request(
                "PUT",
                "clientes/item",
                params={"id": "B"},
                json={"codigo": "B", "nombre": "Bruno", self_key.columns[0]: cid},
            )
            assert (
                request("GET", "clientes/references/" + self_key.name, params={"id": "B"})["codigo"]
                == cid
            )
            assert (
                request("GET", "clientes/related/" + self_key.name, params={"id": cid})["total"]
                == 1
            )
            assert request("GET", "catalogo/item", params={"id": 1})["etiqueta"] == "Solo lectura"
            request("POST", "catalogo", 405, json={"codigo": 2})
            request("PUT", "catalogo/item", 405, params={"id": 1}, json={"codigo": 1})
            request("DELETE", "catalogo/item", 405, params={"id": 1})
            request("GET", "catalogo", 400, params={"q": "x"})
            request("GET", "pedidos", 400, params={"filter.activo": "no"})
            request("GET", "pedidos", 400, params={"filter.ratio": "NaN"})
            request("GET", "pedidos", 400, params={"filter.fecha": "not-a-date"})
            # Restart the generated JVM, preserving only the temporary database.
            stop()
            server = launch()
            assert request("GET", "pedidos/item", params={"id": order["id"]})["estado"] == "NUEVO"
            passed.append("generated JVM restarted; PostgreSQL data recovered")
            request("DELETE", "pedidos/item", 204, params={"id": order["id"]})
            request("GET", "pedidos/item", 404, params={"id": order["id"]})
        result = {
            "status": "PASS",
            "dateUtc": datetime.now(UTC).isoformat(),
            "project": str(run),
            "postgresql": "17.6 local, isolated disposable database",
            "checks": passed,
            "legacyDatabaseAccessed": False,
            "cloud": False,
        }
    finally:
        stop()
        if created:
            assert re.fullmatch(r"cu14_[0-9a-f]{32}", database) and database != origin.database
            with psycopg.connect(dbname="postgres", autocommit=True, **credentials) as admin:
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
                )
    result["temporaryDatabaseRemoved"] = True
    (root / "artifacts/cu14/crud-result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "checks": len(passed),
                "project": str(run),
                "temporaryDatabaseRemoved": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
