# Phase 1 - Foundation

## Goal

Create the initial GovernAI Python SDK repository foundation.

This phase must create the package structure, source modules, test modules, shared build settings, core abstractions, models, and enums.

Do not implement runtime behavior in this phase.

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
```

---

## Scope

Implement only:

- Package structure
- Source module structure
- Test module structure
- pyproject.toml
- Core protocols and abstract base classes
- Core models
- Core enums
- Basic README placeholder
- Basic documentation placeholders

---

## Repository Structure To Create

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
│   ├── architecture.md
│   ├── coding-guidelines.md
│   ├── security-guidelines.md
│   ├── event-schema.md
│   └── roadmap.md
│
├── copilot/
│   ├── 00-master-instructions.md
│   ├── phase-1-foundation.md
│   ├── phase-2-core-runtime.md
│   ├── phase-3-security.md
│   ├── phase-4-wsgi.md
│   ├── phase-5-samples.md
│   ├── phase-6-docs.md
│   └── phase-7-cicd.md
│
├── src/
│   └── governai/
│       ├── __init__.py
│       ├── abstractions/
│       │   └── __init__.py
│       ├── core/
│       │   └── __init__.py
│       ├── security/
│       │   └── __init__.py
│       └── wsgi/
│           └── __init__.py
│
├── tests/
│   ├── test_abstractions/
│   │   └── __init__.py
│   ├── test_core/
│   │   └── __init__.py
│   ├── test_security/
│   │   └── __init__.py
│   └── test_wsgi/
│       └── __init__.py
│
└── samples/
    ├── sample_basic/
    ├── sample_multi_tenant/
    └── sample_policy_demo/
```

---

## Project Requirements

Create these source modules:

```text
src/governai/abstractions/__init__.py
src/governai/core/__init__.py
src/governai/security/__init__.py
src/governai/wsgi/__init__.py
```

Create these test modules:

```text
tests/test_abstractions/__init__.py
tests/test_core/__init__.py
tests/test_security/__init__.py
tests/test_wsgi/__init__.py
```

---

## Target Python Versions

All packages must support:

```text
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Set `python_requires = ">=3.10"` in `pyproject.toml`.

---

## Build Settings

Create `pyproject.toml` at repository root.

It must include:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "governai"
version = "0.1.0"
description = "Dependency-light, local-first Python SDK for AI governance"
requires-python = ">=3.10"
license = { expression = "MIT" }
authors = [
    { name = "GovernAI Contributors" }
]
dependencies = []

[tool.mypy]
strict = true
python_version = "3.10"

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "S"]
```

---

## Dependency Rules

Do not add external PyPI packages.

Allowed:

- Internal imports between `governai.*` sub-packages.
- Python standard library only.

Not allowed:

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

---

## Package Dependency Rules

```text
governai.abstractions
  - No dependency

governai.core
  - Depends on governai.abstractions

governai.security
  - Depends on governai.abstractions
  - Depends on governai.core

governai.wsgi
  - Depends on governai.abstractions
  - Depends on governai.core
  - Depends on governai.security
```

---

## Required Protocols and Abstract Base Classes

Create these in `governai/abstractions/` using `typing.Protocol` (Python 3.8+, available in 3.10+).

### `GovernAIExporter`

```python
from typing import Protocol
from governai.abstractions.models import GovernAIEvent

class GovernAIExporter(Protocol):
    async def export_async(
        self,
        event: GovernAIEvent,
    ) -> None: ...
```

### `GovernAIPolicyEvaluator`

```python
class GovernAIPolicyEvaluator(Protocol):
    async def evaluate_async(
        self,
        context: GovernAIContext,
    ) -> GovernAIPolicyDecision: ...
```

### `GovernAIRedactor`

```python
class GovernAIRedactor(Protocol):
    def redact(self, input: str | None) -> str: ...
```

### `GovernAITenantResolver`

```python
class GovernAITenantResolver(Protocol):
    async def resolve_tenant_id_async(self) -> str | None: ...
```

### `GovernAIUserResolver`

```python
class GovernAIUserResolver(Protocol):
    async def resolve_user_id_async(self) -> str | None: ...
```

### `GovernAIClock`

```python
class GovernAIClock(Protocol):
    @property
    def utc_now(self) -> datetime: ...
```

> `str | None` union syntax requires Python 3.10+. For 3.9 compatibility use `Optional[str]` from `typing`; since the minimum is 3.10 the `|` shorthand is preferred.

---

## Required Models

Create these dataclasses in `governai/abstractions/models.py` using `@dataclasses.dataclass(frozen=True)`.

### `GovernAIContext`

Must include:

```text
TraceId
CorrelationId
ApplicationName
EnvironmentName
TenantId
UserId
AgentName
OperationName
ModelProvider
ModelName
Prompt
Response
InputTokens
OutputTokens
Metadata
```

### `GovernAIEvent`

Must include:

```text
EventId
TraceId
CorrelationId
ApplicationName
EnvironmentName
TenantId
UserId
AgentName
OperationName
ModelProvider
ModelName
PromptHash
ResponseHash
InputTokens
OutputTokens
TotalTokens
RiskScore
RiskLevel
RiskCategory
PolicyDecision
PolicyReason
DurationMs
Success
ErrorCode
ErrorMessage
TimestampUtc
Metadata
```

### `GovernAIPolicyDecision`

Must include:

```text
Decision
Reason
RiskScore
RiskLevel
RiskCategory
Metadata
```

### `GovernAIRiskResult`

Must include:

```text
RiskScore
RiskLevel
RiskCategory
Reason
MatchedPatterns
```

---

## Required Enums

Create using `enum.Enum` in `governai/abstractions/enums.py`.

```text
GovernAIPolicyDecisionType
GovernAIRiskLevel
```

### `GovernAIPolicyDecisionType`

Values:

```text
ALLOW
REVIEW
DENY
```

### `GovernAIRiskLevel`

Values:

```text
NONE
LOW
MEDIUM
HIGH
CRITICAL
```

---

## Docstrings

All public classes, methods, and module-level symbols must have Google-style docstrings.

---

## Tests

Create basic tests using `unittest` (standard library) to verify:

- models can be instantiated
- enum values exist
- protocols can be implemented by concrete classes

Do not add external test packages.

---

## Acceptance Criteria

- All packages import cleanly.
- Compatible with Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- No external package dependencies are added.
- Public APIs have docstrings.
- Basic tests pass with `python -m unittest`.
- No runtime logic implemented yet.