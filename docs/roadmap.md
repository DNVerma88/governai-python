# GovernAI Roadmap

## Product Direction

GovernAI will start as a dependency-light, local-first Python SDK.

The long-term goal is to evolve into a broader AI governance ecosystem supporting:

- Python
- .NET
- Java
- PHP
- JavaScript/TypeScript
- Collector
- Policy Server
- Dashboard
- OpenTelemetry
- MCP security

---

# Phase 1 - Foundation

## Goal

Create the base repository, solution, packages, contracts, models, and documentation placeholders.

## Packages

```text
governai-abstractions
governai-core
governai-security
governai-wsgi
```

## Deliverables

- pyproject.toml
- Source packages
- Test modules
- Protocols and abstract base classes
- Models (frozen dataclasses)
- Enums
- README placeholder
- Documentation placeholders

## Success Criteria

- All packages import cleanly.
- Tests run with `python -m unittest`.
- No external package dependencies.
- All packages compatible with Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- Public APIs have docstrings.

---

# Phase 2 - Core Runtime

## Goal

Implement local-first AI execution tracking.

## Deliverables

- GovernAIRuntime
- GovernAITracker
- GovernAIOptions
- PromptHasher
- ResponseHasher
- SystemClock
- NoOpPolicyEvaluator
- NoOpExporter
- CompositeExporter
- InMemoryExporter
- ConsoleExporter
- FileExporter

## Success Criteria

- Successful AI operation is tracked.
- Failed AI operation is tracked.
- Duration is captured.
- Prompt and response are hashed.
- Event is exported.
- Exporter failure does not break app by default.

---

# Phase 3 - Security

## Goal

Add basic security scanning, redaction, risk scoring, and local policy decisions.

## Deliverables

- BasicPiiRedactor
- SensitiveDataScanner
- PromptInjectionHeuristicScanner
- RiskScoreCalculator
- DefaultLocalPolicyEvaluator

## Success Criteria

- Common sensitive data is redacted.
- Prompt injection-like patterns are detected.
- Risk level is calculated.
- Local policy decision is returned.
- No false claim of full protection.

---

# Phase 4 - Python WSGI Integration

## Goal

Provide first-class Python WSGI integration.

## Deliverables

- GovernAIMiddleware (WSGI)
- GovernAIConfig
- HeaderTenantResolver
- HeaderUserResolver
- GovernAIWSGIApp

## Success Criteria

- WSGI sample runs with `wsgiref.simple_server`.
- Tenant can be resolved from `X-Tenant-Id` header.
- User can be resolved from environ or header.
- Correlation ID is generated or reused.
- Middleware does not read request body.

---

# Phase 5 - Samples

## Goal

Provide working developer examples.

## Samples

```text
samples/sample_basic/
samples/sample_multi_tenant/
samples/sample_policy_demo/
```

## Success Criteria

- Samples run without real AI provider.
- Samples use fake AI calls.
- Samples run with `wsgiref.simple_server`.
- README explains how to run samples.

---

# Phase 6 - Documentation

## Goal

Create useful developer documentation.

## Deliverables

- README
- architecture.md
- coding-guidelines.md
- security-guidelines.md
- event-schema.md
- roadmap.md
- getting-started.md if needed

## Success Criteria

- Docs explain purpose clearly.
- Docs explain secure defaults.
- Docs explain package structure.
- Docs explain future extensibility.
- Docs avoid overclaiming security guarantees.

---

# Phase 7 - CI/CD

## Goal

Prepare the repository for OSS quality.

## Deliverables

- GitHub Actions workflow
- Install
- Type check (mypy)
- Test (unittest)
- Build (python -m build)
- Pull request validation
- Main branch validation

## Success Criteria

- CI installs and type-checks all packages.
- CI runs tests.
- CI builds distribution packages.
- CI matrix covers Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- CI does not publish packages yet.

---

# Future Phase 8 - OpenTelemetry

## Goal

Add optional OpenTelemetry integration.

## Package

```text
governai-opentelemetry
```

## Scope

- Map GovernAIEvent to OpenTelemetry GenAI conventions.
- Add traces.
- Add metrics.
- Keep package optional.

Do not include this in MVP.

---

# Future Phase 9 - Collector

## Goal

Create centralized event ingestion.

## Packages

```text
governai-exporter-http
governai-collector
```

## Scope

- HTTP event exporter
- Collector API
- Event ingestion
- Future storage integration
- Future dashboard support

Do not include this in MVP.

---

# Future Phase 10 - Remote Policy Server

## Goal

Centralize policy decisions.

## Packages

```text
governai-policy-client
governai-policy-server
```

## Scope

- Remote policy evaluation
- Tenant-level policy rules
- Policy caching
- Fallback behavior
- Allow / Review / Deny decisions

Do not include this in MVP.

---

# Future Phase 11 - MCP Security

## Goal

Add MCP governance and security support.

## Packages

```text
GovernAI.MCP
GovernAI.MCP.Security
```

## Scope

- Tool authorization
- MCP audit trail
- Tool execution policies
- Secret protection
- Tenant-aware MCP access

Do not include this in MVP.

---

# Future Phase 12 - Cross-Language SDKs

## Goal

Expand GovernAI to all major languages.

## Repositories

```text
governai-python  (this repository)
governai-dotnet
governai-java
governai-php
governai-js
```

## Rule

All SDKs must follow the same event schema.

---

# MVP Boundary

MVP includes only:

```text
governai.abstractions
governai.core
governai.security
governai.wsgi
```

MVP excludes:

```text
governai.opentelemetry
governai.collector
governai.policy_server
governai.dashboard
governai.storage
governai.mcp
```