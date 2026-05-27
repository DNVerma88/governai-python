# GovernAI Architecture

## Purpose

GovernAI is a dependency-light, local-first Python SDK for AI governance, auditability, policy enforcement, redaction, risk scoring, and tenant-aware AI execution tracking.

The first version must run fully in-process without external infrastructure, while keeping the architecture ready for future expansion into:

- GovernAI Collector
- Remote Policy Server
- OpenTelemetry integration
- Dashboard
- Storage
- MCP security
- Cross-language SDKs

---

## Repository Name

```text
governai-python
```

---

## Architecture Style

GovernAI follows a modular SDK architecture.

Each package must have a clear responsibility and must be independently reusable.

```text
Python Application
   |
   |-- governai.wsgi
   |      - WSGI/ASGI middleware
   |      - dependency configuration
   |      - correlation ID handling
   |      - tenant/user resolution
   |
   |-- governai.core
   |      - runtime tracking
   |      - prompt/response hashing
   |      - event creation
   |      - local exporters
   |      - local policy execution
   |
   |-- governai.security
   |      - PII redaction
   |      - sensitive data detection
   |      - prompt risk scanning
   |      - local risk scoring
   |
   |-- governai.abstractions
          - protocols
          - models
          - enums
          - shared contracts
```

---

## Package Structure

```text
src/
  governai/
    __init__.py
    abstractions/
    core/
    security/
    wsgi/
```

Each sub-package is independently importable and may be published as a separate PyPI distribution:

```text
governai-abstractions
governai-core
governai-security
governai-wsgi
```

---

## Package Dependency Rules

```text
governai.abstractions
  - No internal dependency
  - No external package dependency
  - Standard library only

governai.core
  - Depends on governai.abstractions
  - No external package dependency
  - Standard library only

governai.security
  - Depends on governai.abstractions
  - Depends on governai.core
  - No external package dependency
  - Standard library only

governai.wsgi
  - Depends on governai.abstractions
  - Depends on governai.core
  - Depends on governai.security
  - Uses only Python standard library wsgiref / http.server
```

---

## MVP Runtime Architecture

```text
Application Code
   |
   | calls await track_async()
   |
GovernAI Runtime
   |
   |-- Resolve context
   |-- Evaluate local policy
   |-- Execute AI operation if allowed
   |-- Hash prompt/response
   |-- Redact sensitive values where configured
   |-- Build GovernAIEvent
   |-- Export event
   |
Exporter Protocol
   |-- InMemoryExporter
   |-- ConsoleExporter
   |-- FileExporter
   |-- CompositeExporter
```

---

## Future Collector Architecture

The SDK must be designed so an HTTP exporter can be added later without changing core runtime contracts.

```text
Python Application
   |
GovernAI SDK
   |
GovernAIExporter (Protocol)
   |
governai.exporter.http (future)
   |
GovernAI Collector
   |
Storage / Dashboard / SIEM / Azure Monitor / Datadog / Elastic
```

Do not implement the Collector in MVP.

---

## Future Remote Policy Server Architecture

The SDK must be designed so local policy evaluation can later be replaced or supplemented by a remote policy server.

```text
Python Application
   |
GovernAI SDK
   |
GovernAIPolicyEvaluator (Protocol)
   |
governai.policy.client (future)
   |
GovernAI Policy Server
   |
Allow / Review / Deny
```

Do not implement the Policy Server in MVP.

---

## Future OpenTelemetry Architecture

The SDK must be designed so events can later be mapped to OpenTelemetry GenAI semantic conventions.

```text
GovernAIEvent
   |
GovernAI.OpenTelemetry
   |
OpenTelemetry Traces / Metrics / Logs
   |
Application Insights / Azure Monitor / Grafana / Datadog / Elastic
```

Do not implement OpenTelemetry in MVP.

---

## Core Extension Points

GovernAI must expose small focused Protocols (`typing.Protocol`) and abstract base classes (`abc.ABC`).

```python
GovernAIExporter       # typing.Protocol
GovernAIPolicyEvaluator  # typing.Protocol
GovernAIRedactor       # typing.Protocol
GovernAITenantResolver # typing.Protocol
GovernAIUserResolver   # typing.Protocol
GovernAIClock          # typing.Protocol
```

These protocols are required so the SDK can be extended without modifying core runtime logic.

---

## Design Principles

The architecture must follow:

- SOLID
- KISS
- DRY
- YAGNI
- Composition over inheritance
- Interface-based extensibility
- Secure by default
- Privacy by default
- Provider-neutral design
- Cloud-neutral design
- Tenant-aware design

---

## Design Patterns

Use these patterns only where they add clear value:

### Strategy Pattern

Use for:

- policy evaluation
- redaction
- tenant resolution
- user resolution

### Composite Pattern

Use for:

- multiple exporters

### Null Object Pattern

Use for:

- no-op policy evaluator
- no-op exporter

### Adapter Pattern

Use later for:

- OpenTelemetry
- Collector
- Policy Server

### Middleware Pattern

Use for:

- Python WSGI/ASGI integration

### Options Pattern

Use for:

- SDK configuration

---

## Security Architecture

GovernAI must be secure by default.

Default behavior:

- Do not store raw prompt.
- Do not store raw response.
- Hash prompt using SHA-256.
- Hash response using SHA-256.
- Avoid logging request bodies.
- Avoid collecting secrets.
- Support redaction.
- Support risk scoring.
- Support policy decisions.

---

## Multi-Tenant Architecture

GovernAI must support tenant-aware applications from the beginning.

Tenant ID can come from:

- explicit context
- HTTP header
- claims
- custom resolver

The SDK must not assume a specific tenant model.

---

## Provider-Neutral Architecture

GovernAI must not depend on:

- OpenAI
- Azure OpenAI
- Anthropic
- Gemini
- AWS Bedrock
- Semantic Kernel
- LangChain

Applications can use any AI provider and wrap the call with GovernAI tracking.

---

## Cloud-Neutral Architecture

GovernAI must not depend on:

- Azure SDK
- AWS SDK
- GCP SDK

Cloud integrations must be added later as optional packages only.

---

## Non-Functional Requirements

GovernAI must be:

- thread-safe
- async-first (asyncio)
- testable
- extensible
- lightweight
- type-hint-friendly
- dependency-light
- high-throughput API friendly
- compatible with Python 3.10, 3.11, 3.12, 3.13, and 3.14

---

## MVP Scope

Implement only:

```text
governai.abstractions
governai.core
governai.security
governai.wsgi
```

Do not implement:

```text
governai.opentelemetry
governai.collector
governai.policy_server
governai.dashboard
governai.storage
governai.mcp
```