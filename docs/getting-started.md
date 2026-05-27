# Getting Started with GovernAI

This guide walks you through installing GovernAI and tracking your first AI call.

---

## Prerequisites

- Python 3.10 or later
- A virtual environment (recommended)

GovernAI has **no external package dependencies**. It uses the Python standard library only.

---

## Installation

### From source (recommended during development)

```bash
git clone https://github.com/your-org/governai-python.git
cd governai-python
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate      # macOS / Linux
pip install -e .
```

### Verify the install

```python
python -c "import governai; print(governai.__version__)"
# 0.1.0
```

---

## Tracking Your First AI Call

GovernAI wraps your existing AI calls. It does not provide an AI model — you bring your own.

```python
import asyncio
from governai.abstractions.models import GovernAIContext
from governai.core.options import GovernAIOptions
from governai.core.runtime import GovernAIRuntime
from governai.core.exporters import ConsoleExporter

# 1. Configure the runtime
options = GovernAIOptions(
    application_name="MyApp",
    environment_name="development",
)
runtime = GovernAIRuntime(options=options, exporter=ConsoleExporter())

# 2. Describe the AI operation context
context = GovernAIContext(
    application_name="MyApp",
    environment_name="development",
    operation_name="Summarise",
    prompt="Summarise this document in three bullet points.",
)

# 3. Track the call
async def main() -> None:
    response = await runtime.track_async(
        context,
        lambda: my_ai_call_async("Summarise this document in three bullet points."),
    )
    print(response)

asyncio.run(main())
```

When the call completes, `ConsoleExporter` prints a JSON governance event to stdout.

---

## Using the WSGI Middleware

Add `GovernAIMiddleware` to any WSGI application to automatically:

- Generate or propagate correlation IDs via `X-Correlation-Id`.
- Resolve tenant and user IDs from request headers.
- Inject the GovernAI runtime into the WSGI environ.

```python
from governai.wsgi import GovernAIConfig, GovernAIMiddleware

config = GovernAIConfig(
    application_name="MyApi",
    environment_name="production",
)
app = GovernAIMiddleware(wsgi_app=my_wsgi_app, config=config)
```

Inside your WSGI handler, access the runtime via `environ["governai.runtime"]`.

---

## Adding Security: PII Redaction and Local Policy

```python
from governai.core.runtime import GovernAIRuntime
from governai.core.options import GovernAIOptions
from governai.core.exporters import ConsoleExporter
from governai.security.policy import DefaultLocalPolicyEvaluator
from governai.security.redaction import BasicPiiRedactor

# Redact PII before building the context
redactor = BasicPiiRedactor()
safe_prompt = redactor.redact(raw_prompt)  # emails, tokens, cards → [REDACTED_...]

# Use local policy for Allow / Review / Deny
options = GovernAIOptions(application_name="MyApp", environment_name="prod")
runtime = GovernAIRuntime(
    options=options,
    exporter=ConsoleExporter(),
    policy_evaluator=DefaultLocalPolicyEvaluator(),
)
```

`DefaultLocalPolicyEvaluator` applies two scanners:

| Scanner | What it detects |
|---|---|
| `SensitiveDataScanner` | Emails, phones, credit cards, API keys, bearer tokens, connection strings, passwords |
| `PromptInjectionHeuristicScanner` | Phrases like "ignore previous instructions", "bypass security", "print secrets" |

Risk score → policy decision mapping:

| Score | Level | Decision |
|---|---|---|
| 0 | NONE | ALLOW |
| 1–30 | LOW | ALLOW |
| 31–60 | MEDIUM | ALLOW |
| 61–85 | HIGH | REVIEW |
| 86–100 | CRITICAL | DENY |

---

## Running the Samples

```bash
# Basic WSGI demo with ConsoleExporter
python -m samples.sample_basic

# Multi-tenant: pass X-Tenant-Id and X-User-Id headers
python -m samples.sample_multi_tenant

# Policy demo: safe / risky / critical prompts
python -m samples.sample_policy_demo
```

---

## Next Steps

- [Architecture overview](architecture.md)
- [Security guidelines](security-guidelines.md)
- [Event schema reference](event-schema.md)
- [Roadmap](roadmap.md)
