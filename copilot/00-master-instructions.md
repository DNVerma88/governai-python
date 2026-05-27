# GovernAI Master Instructions

## Product Vision

GovernAI is a dependency-light, local-first, extensible Python SDK for:

- AI governance
- AI runtime auditing
- AI policy enforcement
- Prompt/response hashing
- Sensitive data redaction
- Prompt risk analysis
- Tenant-aware AI execution tracking
- Python WSGI/ASGI integration
- Future OpenTelemetry integration
- Future Collector integration
- Future Remote Policy Server integration

The SDK must initially run fully in-process without requiring external infrastructure.

The architecture must be designed so that future versions can support:

- GovernAI Collector
- GovernAI Remote Policy Server
- GovernAI Dashboard
- OpenTelemetry integration
- MCP security
- Cross-language SDKs

---

# Architecture Goals

The SDK architecture must be:

- Local-first
- Dependency-light
- Vendor-neutral
- Cloud-neutral
- Extensible
- Type-hint-friendly
- Thread-safe
- Async-first
- Multi-tenant-ready
- OpenTelemetry-ready
- Collector-ready
- Policy-server-ready

---

# Hard Requirements

## External Dependencies

The MVP must NOT add external PyPI package dependencies unless explicitly approved.

Do NOT use:

- semantic-kernel
- langchain
- openai
- azure-sdk
- boto3
- pydantic
- httpx
- requests
- aiohttp
- structlog
- loguru
- tenacity
- celery

Use only the Python standard library unless explicitly approved.

---

# Target Python Versions

All packages must support:

```text
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Minimum required version: `python_requires >= "3.10"`

All projects must configure in `pyproject.toml`:

```toml
[project]
requires-python = ">=3.10"

[tool.mypy]
strict = true
python_version = "3.10"

[tool.ruff]
target-version = "py310"
```

Use only standard-library features available in Python 3.10 as a baseline.
Where newer Python features (3.11+, 3.12+, etc.) improve clarity, guard them with
`sys.version_info` checks or `TYPE_CHECKING` blocks to maintain 3.10 compatibility.

---

# Design Principles

The entire SDK must follow these principles:

## SOLID

### Single Responsibility Principle

Each class must have one responsibility only.

Examples:

- PromptHasher => hashing only
- BasicPiiRedactor => redaction only
- CompositeExporter => exporter orchestration only

### Open Closed Principle

SDK must support extensibility through interfaces and composition without modifying existing code.

### Liskov Substitution Principle

All interface implementations must behave consistently and safely.

### Interface Segregation Principle

Keep interfaces small and focused.

### Dependency Inversion Principle

Core runtime must depend on abstractions rather than concrete implementations.

---

## KISS

Keep implementation simple.

Avoid:

- unnecessary abstraction
- over-engineering
- speculative features
- complex policy engines in MVP

---

## DRY

Avoid duplicated:

- hashing logic
- redaction logic
- policy evaluation logic
- event creation logic

---

## YAGNI

Do not implement features that are not immediately required.

Do not build:

- dashboards
- database storage
- distributed policy engines
- remote collectors
- OpenTelemetry exporters

until explicitly requested.

---

# Architecture Principles

## Composition Over Inheritance

Prefer composition and interfaces instead of deep inheritance hierarchies.

## Interface-Based Extensibility

All extension points must use abstract base classes (`abc.ABC`) or `typing.Protocol`.

Examples:

- `GovernAIExporter` (Protocol)
- `GovernAIPolicyEvaluator` (Protocol)
- `GovernAIRedactor` (Protocol)
- `GovernAITenantResolver` (Protocol)
- `GovernAIUserResolver` (Protocol)

## Secure By Default

Default configuration must prioritize safety and privacy.

## Privacy By Default

Raw prompts and responses must NOT be stored by default.

## Provider Neutral

Do not couple to OpenAI, Azure OpenAI, Anthropic, or any specific provider.

## Cloud Neutral

Do not couple to Azure, AWS, or GCP.

## Tenant-Aware Design

Architecture must support multi-tenant applications from the beginning.

---

# Design Patterns To Use

Use patterns only where they provide real value.

## Strategy Pattern

Use for:

- policy evaluation
- redaction
- tenant resolution
- user resolution

## Factory Pattern

Use only where object creation becomes complex.

## Options Pattern

Use for SDK configuration.

## Composite Pattern

Use for multi-exporter support.

## Null Object Pattern

Use for:

- NoOpPolicyEvaluator
- NoOpExporter

## Adapter Pattern

Use for future:

- OpenTelemetry integration
- Collector integration
- Policy server integration

## Middleware Pattern

Use for Python WSGI/ASGI integration.

---

# Security Guidelines

GovernAI must align with OWASP LLM security guidance.

## Key Risk Areas

Focus especially on:

- Prompt Injection
- Sensitive Information Disclosure
- Insecure Output Handling
- Excessive Agency
- Supply Chain Vulnerabilities
- Model Denial of Service
- Insecure Plugin/Tool Design

---

# Security Defaults

GovernAI must provide secure defaults.

## Prompt Handling

- Do not store raw prompt by default.
- Do not store raw response by default.
- Hash prompts using SHA-256.
- Hash responses using SHA-256.

## Redaction

Redact:

- email addresses
- phone numbers
- API keys
- bearer tokens
- JWT tokens
- connection strings
- password-like values

## Prompt Risk Detection

Detect risky prompt patterns such as:

- ignore previous instructions
- reveal system prompt
- bypass security
- disable policy
- print secrets
- exfiltrate data
- jailbreak
- hidden instructions

## Policy Decisions

Support:

- Allow
- Review
- Deny

Default behavior:

- Low risk => Allow
- Medium risk => Allow with warning
- High risk => Review
- Critical risk => Deny

---

# Performance Guidelines

The SDK must:

- minimize object creation in hot paths
- avoid dynamic attribute inspection (`getattr`/`vars`) in hot paths
- avoid importing optional modules at startup
- avoid blocking I/O calls
- use `asyncio` async/await APIs
- support `asyncio.CancelledError` / cancellation signals
- be compatible with `asyncio`, `trio`-style cancellation via task cancellation
- avoid global mutable state

---

# Testing Requirements

All features must have unit tests.

Tests must cover:

- success scenarios
- failure scenarios
- edge cases
- concurrency behavior
- hashing
- redaction
- policy evaluation
- exporter behavior

---

# Documentation Requirements

All public APIs must:

- have docstrings (Google-style or NumPy-style, chosen consistently)
- have meaningful names
- follow consistent naming conventions (PEP 8: `snake_case` for functions/variables, `PascalCase` for classes)

All phases must update:

- README
- docs
- samples

---

# Repository Structure

```text
governai-python/
│
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore
├── .editorconfig
├── pyproject.toml
│
├── docs/
├── copilot/
├── src/
│   └── governai/
├── tests/
└── samples/
```

---

# Implementation Rules For Copilot Agent

1. Implement one phase at a time.
2. Do not implement future phases prematurely.
3. Keep public APIs minimal and stable.
4. Keep architecture extensible.
5. Keep code easy to understand.
6. Keep secure defaults.
7. Do not add external dependencies.
8. Prioritize maintainability and clarity.
9. Ensure all packages are compatible with Python 3.10, 3.11, 3.12, 3.13, and 3.14.
10. Keep the SDK future-ready for Collector and Policy Server expansion.