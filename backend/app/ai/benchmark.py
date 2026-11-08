"""Frozen-dataset benchmark; fixtures-only never reports LLM success metrics."""

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import UUID

from app.ai.context import build_context
from app.ai.gemini import MODEL, SYSTEM_PROMPT, ProviderError, interpret
from app.ai.intents import IntentResponse, resolve_intent
from app.domain.uml.commands import UmlCommandExecutionError
from app.domain.uml.models import CanonicalUmlModel, ProjectDocument, UmlClass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    dataset = root / "docs/benchmarks/cu18-cases.json"
    cases = json.loads(dataset.read_text(encoding="utf-8"))
    for case in cases:
        IntentResponse(intent=case["expected"])
    project = ProjectDocument(
        id=UUID(int=99),
        ownerId=UUID(int=98),
        umlModel=CanonicalUmlModel(
            elements=[
                UmlClass(id=UUID(int=1), name="Cliente", visibility="public"),
                UmlClass(id=UUID(int=2), name="Pedido", visibility="public"),
            ]
        ),
    )

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()

    hardware_path = root / "artifacts/cu18/hardware.json"
    result = {
        "dateUtc": datetime.now(UTC).isoformat(),
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "python": platform.python_version(),
        "clientHardware": json.loads(hardware_path.read_text(encoding="utf-8-sig"))
        if hardware_path.exists()
        else {
            "os": platform.platform(),
            "cpu": platform.processor(),
            "ram": "not measured",
            "gpu": "not measured",
        },
        "remoteHardware": "not exposed by cloud provider",
        "pydantic": version("pydantic"),
        "modelCandidate": MODEL,
        "datasetVersion": 1,
        "datasetSha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "implementationSha256": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / "backend/app/ai").glob("*.py"))
        },
        "cases": len(cases),
        "prompt": SYSTEM_PROMPT,
        "maxOutputTokens": 1200,
        "configurations": [],
        "llmMetrics": None,
    }
    key = os.getenv("GEMINI_API_KEY", "")
    if not key and not args.fixtures_only:
        from dotenv import dotenv_values

        key = dotenv_values(root / "backend/.env").get("GEMINI_API_KEY") or ""
    if args.fixtures_only or not key:
        result["status"] = "NOT_RUN"
        result["reason"] = (
            "fixtures-only; no inference" if args.fixtures_only else "API key missing"
        )
        result["requestsSent"] = 0
    else:
        result["status"] = "MEASURED"
        for temperature in (0, 0.2):
            rows = []
            for case in cases:
                start = perf_counter()
                try:
                    observation = {}
                    response = interpret(
                        build_context(project, project.owner_id, case["text"], []),
                        key,
                        temperature=temperature,
                        observation=observation,
                    )
                    actual = response.intent.model_dump(by_alias=True)
                    expected = case["expected"]
                    exact = (
                        actual == expected
                        if expected["operation"] not in {"clarify", "unsupported"}
                        else actual["operation"] == expected["operation"]
                    )
                    resolvable = False
                    if actual["operation"] not in {"clarify", "unsupported"}:
                        try:
                            resolve_intent(project, response)
                            resolvable = True
                        except (ValueError, UmlCommandExecutionError):
                            pass
                    rows.append(
                        {
                            "id": case["id"],
                            "schemaValid": True,
                            "exactIntent": exact,
                            "resolved": resolvable,
                            "intent": actual,
                            "providerObservation": observation,
                            "seconds": perf_counter() - start,
                        }
                    )
                except (ProviderError, ValueError) as error:
                    rows.append(
                        {
                            "id": case["id"],
                            "schemaValid": False,
                            "exactIntent": False,
                            "errorType": type(error).__name__,
                            "seconds": perf_counter() - start,
                        }
                    )
            times = sorted(row["seconds"] for row in rows)
            result["configurations"].append(
                {
                    "temperature": temperature,
                    "rows": rows,
                    "schemaValidRate": sum(r["schemaValid"] for r in rows) / len(rows),
                    "exactIntentAccuracy": sum(r["exactIntent"] for r in rows) / len(rows),
                    "falsePositiveProposalRate": sum(
                        bool(row.get("resolved"))
                        and case["expected"]["operation"] in {"clarify", "unsupported"}
                        for row, case in zip(rows, cases, strict=True)
                    )
                    / sum(
                        case["expected"]["operation"] in {"clarify", "unsupported"}
                        for case in cases
                    ),
                    "latencyP50Seconds": statistics.median(times),
                    "latencyP95Seconds": times[math.ceil(0.95 * len(times)) - 1],
                }
            )
    output = root / "artifacts/cu18"
    output.mkdir(parents=True, exist_ok=True)
    target = output / ("benchmark-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": len(cases), "result": str(target)}))


if __name__ == "__main__":
    main()
