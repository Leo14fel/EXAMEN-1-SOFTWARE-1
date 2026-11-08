import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from app.ai import gemini


def response(intent=None, **changes):
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "intent": intent
                                    or {"operation": "createClass", "name": "Producto"}
                                }
                            )
                        }
                    ]
                },
            }
        ],
        **changes,
    }


def stub(monkeypatch, payload):
    class Opener:
        def open(self, request, timeout):
            assert request.full_url.startswith("https://generativelanguage.googleapis.com/")
            assert "TEST_KEY" not in request.full_url
            assert request.headers["X-goog-api-key"] == "TEST_KEY"
            body = json.loads(request.data)
            assert (
                "tools" not in body
                and body["generationConfig"]["responseMimeType"] == "application/json"
            )
            assert timeout == 20
            return BytesIO(payload if isinstance(payload, bytes) else json.dumps(payload).encode())

    monkeypatch.setattr(gemini, "build_opener", lambda *_: Opener())


def test_rest_contract_validates_output_and_keeps_secret_out_of_url(monkeypatch):
    stub(monkeypatch, response())
    result = gemini.interpret({"request": "crea Producto"}, "TEST_KEY")
    assert result.intent.operation == "createClass"


@pytest.mark.parametrize(
    "payload",
    [
        b"invalid",
        b"null",
        b"[]",
        {"candidates": [None]},
        {"candidates": "invalid"},
        {"candidates": [{"finishReason": "STOP", "content": {"parts": [None]}}]},
        {
            "candidates": [
                {
                    "finishReason": "STOP",
                    "content": {
                        "parts": [
                            {
                                "text": '{"intent":{"operation":"createClass",'
                                '"operation":"deleteClass","name":"x"}}'
                            }
                        ]
                    },
                }
            ]
        },
        b"x" * 32001,
        {},
        {"candidates": [{"finishReason": "MAX_TOKENS"}]},
        response({"operation": "executeCode", "code": "evil"}),
        {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {}}]}}]},
        {
            "candidates": [
                {"finishReason": "STOP", "content": {"parts": [{"text": "{}"}, {"text": "{}"}]}}
            ]
        },
    ],
)
def test_malformed_truncated_or_tool_responses_are_rejected(monkeypatch, payload):
    stub(monkeypatch, payload)
    with pytest.raises(gemini.ProviderError):
        gemini.interpret({}, "TEST_KEY")


@pytest.mark.parametrize(
    "error,code",
    [
        (HTTPError("https://fixed", 429, "SECRET_BODY", None, None), "AI_RATE_LIMIT"),
        (HTTPError("https://fixed", 403, "SECRET_BODY", None, None), "AI_PROVIDER_ERROR"),
        (URLError("SECRET_BODY"), "AI_PROVIDER_UNAVAILABLE"),
    ],
)
def test_provider_failures_never_include_raw_error_body(monkeypatch, error, code):
    class Opener:
        def open(self, *_args, **_kwargs):
            raise error

    monkeypatch.setattr(gemini, "build_opener", lambda *_: Opener())
    with pytest.raises(gemini.ProviderError, match=code) as raised:
        gemini.interpret({}, "TEST_KEY")
    assert "SECRET" not in str(raised.value)


def test_missing_key_large_context_and_host_injection_fail_before_network():
    with pytest.raises(gemini.ProviderError, match="NOT_CONFIGURED"):
        gemini.interpret({}, "")
    with pytest.raises(ValueError):
        gemini.interpret({}, "TEST_KEY", model="../other-host")
    with pytest.raises(gemini.ProviderError, match="CONTEXT_TOO_LARGE"):
        gemini.interpret({"x": "z" * 64000}, "TEST_KEY")


def test_redirects_cannot_forward_api_key():
    assert (
        gemini.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test") is None
    )
