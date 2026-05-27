"""Sample Basic — minimal GovernAI WSGI integration demo.

Demonstrates:
- Configuring GovernAI with a ConsoleExporter.
- Wrapping a WSGI app with GovernAIMiddleware.
- Tracking a fake AI call inside a WSGI handler.
- Running on Python's built-in wsgiref.simple_server.

Run with:
    python -m samples.sample_basic
"""

from __future__ import annotations

import asyncio
import json
from wsgiref.simple_server import make_server

from governai.abstractions.models import GovernAIContext
from governai.core.exporters import ConsoleExporter
from governai.core.options import GovernAIOptions
from governai.core.runtime import GovernAIRuntime
from governai.wsgi.config import GovernAIConfig
from governai.wsgi.middleware import GovernAIMiddleware

_PORT = 8080


# ---------------------------------------------------------------------------
# Fake AI provider (no real AI calls)
# ---------------------------------------------------------------------------

async def _fake_ai_call_async(prompt: str) -> str:
    """Return a fake AI response without calling any real AI provider."""
    return f"Fake AI response for: {prompt}"


# ---------------------------------------------------------------------------
# WSGI Application
# ---------------------------------------------------------------------------

def _app(environ: dict, start_response) -> list[bytes]:  # type: ignore[no-untyped-def]
    """Simple WSGI handler that tracks a fake AI operation."""
    runtime: GovernAIRuntime = environ["governai.runtime"]
    correlation_id: str = environ.get("governai.correlation_id", "")

    prompt = "Tell me a joke."

    context = GovernAIContext(
        application_name="SampleBasic",
        environment_name="development",
        operation_name="FakeAiCall",
        prompt=prompt,
        correlation_id=correlation_id,
    )

    response_text = asyncio.run(
        runtime.track_async(context, lambda: _fake_ai_call_async(prompt))
    )

    body = json.dumps({"response": response_text}).encode()
    start_response("200 OK", [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(body))),
    ])
    return [body]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _build_app() -> GovernAIMiddleware:
    options = GovernAIOptions(
        application_name="SampleBasic",
        environment_name="development",
    )
    runtime = GovernAIRuntime(options=options, exporter=ConsoleExporter())
    config = GovernAIConfig(
        application_name="SampleBasic",
        environment_name="development",
        runtime=runtime,
    )
    return GovernAIMiddleware(wsgi_app=_app, config=config)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = _build_app()
    print(f"GovernAI Sample Basic running on http://localhost:{_PORT}")
    print("Press Ctrl+C to stop.\n")
    with make_server("", _PORT, app) as httpd:
        httpd.serve_forever()
