"""Sample Multi-Tenant — demonstrates tenant and user resolution.

Demonstrates:
- Resolving tenant ID from the X-Tenant-Id request header.
- Resolving user ID from the X-User-Id request header.
- Including tenant and user in the governance context.
- Tracking a fake AI call per tenant.

Run with:
    python -m samples.sample_multi_tenant

Example requests:
    curl -H "X-Tenant-Id: tenant-alpha" -H "X-User-Id: user-001" http://localhost:8081/
    curl -H "X-Tenant-Id: tenant-beta"  http://localhost:8081/
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

_PORT = 8081


# ---------------------------------------------------------------------------
# Fake AI provider
# ---------------------------------------------------------------------------

async def _fake_ai_call_async(prompt: str, tenant_id: str) -> str:
    return f"[tenant={tenant_id}] Fake AI response for: {prompt}"


# ---------------------------------------------------------------------------
# WSGI Application
# ---------------------------------------------------------------------------

def _app(environ: dict, start_response) -> list[bytes]:  # type: ignore[no-untyped-def]
    runtime: GovernAIRuntime = environ["governai.runtime"]
    correlation_id: str = environ.get("governai.correlation_id", "")
    tenant_id: str = environ.get("governai.tenant_id", "")
    user_id: str = environ.get("governai.user_id", "")

    prompt = "Summarise the latest news."

    context = GovernAIContext(
        application_name="SampleMultiTenant",
        environment_name="development",
        operation_name="FakeAiCall",
        prompt=prompt,
        correlation_id=correlation_id,
        tenant_id=tenant_id or None,
        user_id=user_id or None,
    )

    response_text = asyncio.run(
        runtime.track_async(context, lambda: _fake_ai_call_async(prompt, tenant_id))
    )

    body = json.dumps({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "response": response_text,
    }).encode()
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
        application_name="SampleMultiTenant",
        environment_name="development",
    )
    runtime = GovernAIRuntime(options=options, exporter=ConsoleExporter())
    config = GovernAIConfig(
        application_name="SampleMultiTenant",
        environment_name="development",
        runtime=runtime,
    )
    return GovernAIMiddleware(wsgi_app=_app, config=config)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = _build_app()
    print(f"GovernAI Sample Multi-Tenant running on http://localhost:{_PORT}")
    print("Send X-Tenant-Id and X-User-Id headers to see them in events.")
    print("Press Ctrl+C to stop.\n")
    with make_server("", _PORT, app) as httpd:
        httpd.serve_forever()
