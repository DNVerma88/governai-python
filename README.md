# GovernAI Python SDK

Dependency-light, local-first Python SDK for AI governance, auditability, and policy enforcement.

---

## What is GovernAI?

GovernAI is a Python SDK that adds governance, auditability, and policy enforcement to AI-powered applications. It tracks every AI operation — recording hashes, risk scores, policy decisions, and timing — without storing raw prompts or responses by default.

GovernAI runs fully **in-process** with **zero external dependencies**. No cloud account, no API key, and no infrastructure are needed to get started.

---

## What GovernAI is NOT

- Not a firewall or a content filter that can fully block all malicious prompts.
- Not a replacement for responsible AI practices or human review.
- Not an AI provider — it wraps your existing AI calls.
- Not dependent on any cloud platform, AI vendor, or observability service.

---

## Requirements

- Python 3.10 or later
- No external package dependencies (standard library only)

---

## Packages

| Package | Description |
|---|---|
| `governai.abstractions` | Protocols, models, and enumerations — the shared SDK contract |
| `governai.core` | Runtime tracking, hashing, exporters, and no-op implementations |
| `governai.security` | PII redaction, risk scoring, and prompt injection detection |
| `governai.wsgi` | WSGI middleware for correlating and tracking AI requests |

---

## Installation

Install from source (editable):

```bash
pip install -e .
```

Or install individual packages once published:

```bash
pip install governai
```

---

## Quick Start

### Minimal — track an AI call

```python
import asyncio
from governai.abstractions.models import GovernAIContext
from governai.core.options import GovernAIOptions
from governai.core.runtime import GovernAIRuntime
from governai.core.exporters import ConsoleExporter

async def main() -> None:
    options = GovernAIOptions(
        application_name="MyApp",
        environment_name="development",
    )
    runtime = GovernAIRuntime(options=options, exporter=ConsoleExporter())

    context = GovernAIContext(
        application_name="MyApp",
        environment_name="development",
        operation_name="SummariseDocument",
        prompt="Summarise this document.",
    )

    response = await runtime.track_async(
        context,
        lambda: my_ai_provider_call_async("Summarise this document."),
    )
    print(response)

asyncio.run(main())
```

### WSGI Integration

```python
from governai.wsgi import GovernAIConfig, GovernAIMiddleware

config = GovernAIConfig(
    application_name="Enterprise.Api",
    environment_name="production",
)

app = GovernAIMiddleware(wsgi_app=your_wsgi_app, config=config)
```

Run with Python's built-in server:

```python
from wsgiref.simple_server import make_server

with make_server("0.0.0.0", 8000, app) as server:
    server.serve_forever()
```

### With Security — PII Redaction and Local Policy

```python
from governai.core.runtime import GovernAIRuntime
from governai.core.options import GovernAIOptions
from governai.core.exporters import ConsoleExporter
from governai.security.policy import DefaultLocalPolicyEvaluator
from governai.security.redaction import BasicPiiRedactor
from governai.wsgi import GovernAIConfig, GovernAIMiddleware

redactor = BasicPiiRedactor()
prompt = redactor.redact("My email is user@example.com")

options = GovernAIOptions(application_name="SecureApp", environment_name="production")
runtime = GovernAIRuntime(
    options=options,
    exporter=ConsoleExporter(),
    policy_evaluator=DefaultLocalPolicyEvaluator(),
)
config = GovernAIConfig(application_name="SecureApp", runtime=runtime)
app = GovernAIMiddleware(wsgi_app=your_wsgi_app, config=config)
```

---

## Security and Privacy Defaults

| Default | Value |
|---|---|
| Store raw prompt | **No** |
| Store raw response | **No** |
| Hash prompt (SHA-256) | **Yes** |
| Hash response (SHA-256) | **Yes** |
| Fail pipeline on exporter error | **No** |

GovernAI never reads the HTTP request body. It never logs `Authorization`, `Cookie`, or other sensitive headers.

> **Warning**: The heuristic PII redactor and prompt injection scanner do not guarantee complete protection. They reduce accidental exposure but are not a substitute for a dedicated DLP or content-safety system.

---

## Correlation IDs

`GovernAIMiddleware` automatically generates a `X-Correlation-Id` for every request. If the inbound request already carries this header, the existing value is reused. The correlation ID is:

- Added to the WSGI environ as `governai.correlation_id`.
- Appended to every response as a `X-Correlation-Id` header.
- Included in every governance event exported by the runtime.

---

## Samples

| Sample | Description | Run |
|---|---|---|
| `sample_basic` | Minimal WSGI + ConsoleExporter demo | `python -m samples.sample_basic` |
| `sample_multi_tenant` | Tenant/user resolution from headers | `python -m samples.sample_multi_tenant` |
| `sample_policy_demo` | Allow / Review / Deny with local policy | `python -m samples.sample_policy_demo` |

---

## Extending GovernAI

Implement any of the protocols in `governai.abstractions` to plug in custom behaviour:

| Protocol | Purpose |
|---|---|
| `GovernAIExporter` | Export events to any backend |
| `GovernAIPolicyEvaluator` | Custom risk scoring and policy decisions |
| `GovernAIRedactor` | Custom PII / sensitive data redaction |
| `GovernAITenantResolver` | Resolve tenant ID from any source |
| `GovernAIUserResolver` | Resolve user ID from any source |
| `GovernAIClock` | Substitute clock for testing |

### Persisting events to a database or custom destination

Every governance event is delivered to whichever `GovernAIExporter` you configure. To persist events to a database, a message queue, a remote API, or any other store, implement the `GovernAIExporter` protocol — it requires only one async method:

```python
import asyncio
from governai.abstractions.models import GovernAIEvent

class MyDatabaseExporter:
    """Persist GovernAI events to a database of your choice."""

    async def export_async(self, event: GovernAIEvent) -> None:
        # Replace the body below with any storage backend:
        # psycopg2 (PostgreSQL), pyodbc (SQL Server), pymongo (MongoDB),
        # boto3 (DynamoDB), aiohttp (REST API), etc.
        await asyncio.to_thread(self._write, event)

    def _write(self, event: GovernAIEvent) -> None:
        # example: write one row to a relational database
        # con.execute(
        #     "INSERT INTO ai_events (event_id, operation, decision, risk, duration_ms)"
        #     " VALUES (?, ?, ?, ?, ?)",
        #     (event.event_id, event.operation_name,
        #      event.policy_decision.value if event.policy_decision else None,
        #      event.risk_level.value if event.risk_level else None,
        #      event.duration_ms),
        # )
        pass
```

Wire it in at startup:

```python
from governai.core.runtime import GovernAIRuntime
from governai.core.options import GovernAIOptions

runtime = GovernAIRuntime(
    options=GovernAIOptions(application_name="MyApp"),
    exporter=MyDatabaseExporter(),
)
```

**Combine multiple exporters** to write to several destinations at once — for example, buffer events in memory for a live UI feed while also persisting them to a database:

```python
from governai.core.exporters import CompositeExporter, InMemoryExporter

mem = InMemoryExporter(capacity=200)   # used by /events UI endpoint
db  = MyDatabaseExporter()

runtime = GovernAIRuntime(
    options=GovernAIOptions(application_name="MyApp"),
    exporter=CompositeExporter([mem, db]),
)
```

`CompositeExporter` fans out every event to all exporters. If one fails, the others continue; set `fail_on_error=True` only if a failed export should be treated as fatal.

**Key fields available on every `GovernAIEvent`:**

| Field | Description |
|---|---|
| `event_id` | Unique event identifier (UUID hex) |
| `operation_name` | Name of the tracked AI operation |
| `policy_decision` | `ALLOW`, `REVIEW`, or `DENY` |
| `risk_level` | `NONE`, `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `risk_score` | Numeric score 0–100 |
| `policy_reason` | Human-readable explanation of the decision |
| `duration_ms` | Wall-clock time of the AI call in milliseconds |
| `success` | Whether the operation completed without error |
| `error_message` | Exception message if the operation failed |
| `tenant_id` / `user_id` | Multi-tenant identity |
| `trace_id` / `correlation_id` | Request tracing identifiers |
| `prompt_hash` / `response_hash` | SHA-256 fingerprints (no raw text stored) |
| `timestamp_utc` | UTC datetime of the event |

---

## Architecture

GovernAI is designed as a **local-first MVP** with a clear extension path:

```
[Your App]
    │
    ▼
GovernAIMiddleware (WSGI)
    │
    ▼
GovernAIRuntime ──► GovernAIPolicyEvaluator (local or remote)
    │
    ▼
GovernAIExporter ──► Console / InMemory / File / (future: Collector)
```

Future phases will add:
- **GovernAI Collector** — aggregated event collection service
- **Remote Policy Server** — centralised policy evaluation
- **OpenTelemetry** — trace and metric export
- **Dashboard** — governance observability UI

See [docs/architecture.md](docs/architecture.md) and [docs/roadmap.md](docs/roadmap.md) for details.

---

## Contributing

1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # macOS/Linux
   ```
3. Install in editable mode:
   ```bash
   pip install -e .
   ```
4. Run tests:
   ```bash
   python -m unittest discover tests -v
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## License

MIT

