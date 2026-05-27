# Phase 6 - Documentation

## Goal

Complete developer documentation for GovernAI.

---

## Files To Read Before Starting

Read these files first:

```text
/copilot/00-master-instructions.md
/docs/architecture.md
/docs/coding-guidelines.md
/docs/security-guidelines.md
/docs/event-schema.md
/docs/roadmap.md
/copilot/phase-6-docs.md
```

---

## Scope

Documentation only.

Do not change runtime behavior unless required to fix incorrect docs.

---

## Required Documentation Files

Ensure these are complete:

```text
README.md
docs/architecture.md
docs/coding-guidelines.md
docs/security-guidelines.md
docs/event-schema.md
docs/roadmap.md
```

Optionally add:

```text
docs/getting-started.md
docs/package-structure.md
docs/extensibility.md
```

---

## README Requirements

README must include:

```text
Project name
Project purpose
What GovernAI is
What GovernAI is not
Package list
Installation commands
Quick start
Basic usage example
Python WSGI usage example
Security defaults
Privacy defaults
Roadmap summary
Contribution guidance
License
```

---

## Installation Examples

Show:

```bash
pip install governai-abstractions
pip install governai-core
pip install governai-security
pip install governai-wsgi
```

Or install all at once from source:

```bash
pip install -e .
```

---

## Quick Start Example

Include minimal usage:

```python
from governai.wsgi import GovernAIConfig, GovernAIMiddleware

config = GovernAIConfig(
    application_name="Enterprise.Api",
    environment_name="production",
)

app = GovernAIMiddleware(wsgi_app=your_wsgi_app, config=config)
```

Run locally:

```bash
from wsgiref.simple_server import make_server

with make_server("0.0.0.0", 8000, app) as server:
    server.serve_forever()
```

---

## Security Documentation

Clearly state:

- GovernAI does not fully prevent prompt injection.
- GovernAI provides governance assistance.
- Raw prompts are not stored by default.
- Raw responses are not stored by default.
- Sensitive data redaction is heuristic-based.

---

## Architecture Documentation

Must explain:

- local-first MVP
- future Collector
- future Policy Server
- future OpenTelemetry
- no provider lock-in
- no cloud lock-in

---

## Acceptance Criteria

- Docs are clear.
- Docs match implementation.
- No false claims.
- Examples compile or are clearly marked as illustrative.