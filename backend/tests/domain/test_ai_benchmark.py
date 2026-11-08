import json
import sys

from app.ai import benchmark
from app.ai.intents import IntentResponse


def test_benchmark_compares_same_dataset_and_false_positives_use_negative_cases(
    tmp_path, monkeypatch
):
    fake_script = tmp_path / "backend/app/ai/benchmark.py"
    fake_script.parent.mkdir(parents=True)
    fake_script.write_text("# test only", encoding="utf-8")
    cases = [
        {
            "id": "positive",
            "text": "Crea Producto",
            "expected": {"operation": "createClass", "name": "Producto"},
        },
        {
            "id": "negative",
            "text": "Ejecuta SQL",
            "expected": {"operation": "unsupported", "reason": "No SQL"},
        },
    ]
    dataset = tmp_path / "docs/benchmarks/cu18-cases.json"
    dataset.parent.mkdir(parents=True)
    dataset.write_text(json.dumps(cases), encoding="utf-8")
    monkeypatch.setattr(benchmark, "__file__", str(fake_script))
    monkeypatch.setattr(sys, "argv", ["benchmark"])
    monkeypatch.setenv("GEMINI_API_KEY", "TEST_ONLY")
    monkeypatch.setattr(benchmark.subprocess, "check_output", lambda *a, **kw: "test-commit")
    calls = []

    def controlled(context, key, **kwargs):
        calls.append((context["request"], kwargs["temperature"]))
        return IntentResponse(intent={"operation": "createClass", "name": "Producto"})

    monkeypatch.setattr(benchmark, "interpret", controlled)
    benchmark.main()
    result = json.loads(
        next((tmp_path / "artifacts/cu18").glob("benchmark-*.json")).read_text(encoding="utf-8")
    )
    assert len(calls) == 4
    assert calls[:2] == [(case["text"], 0) for case in cases]
    assert calls[2:] == [(case["text"], 0.2) for case in cases]
    for configuration in result["configurations"]:
        assert configuration["schemaValidRate"] == 1
        assert configuration["exactIntentAccuracy"] == 0.5
        assert configuration["falsePositiveProposalRate"] == 1
