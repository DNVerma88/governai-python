# GovernAI Coding Guidelines

# General Principles

The GovernAI SDK must prioritize:

- simplicity
- maintainability
- extensibility
- performance
- security
- readability
- testability

---

# SOLID Principles

## Single Responsibility Principle

Each class should have one responsibility.

Examples:

- PromptHasher => hashing only
- ResponseHasher => hashing only
- BasicPiiRedactor => redaction only
- CompositeExporter => exporter orchestration only

---

## Open Closed Principle

New exporters, policy evaluators, and redactors should be extendable without modifying existing runtime code.

---

## Liskov Substitution Principle

All implementations must safely substitute their interfaces.

---

## Interface Segregation Principle

Keep interfaces focused and small.

Avoid large multi-purpose interfaces.

---

## Dependency Inversion Principle

Depend on abstractions rather than concrete implementations.

---

# KISS

Keep implementation simple.

Avoid:

- deep inheritance
- unnecessary abstraction
- speculative architecture
- overly generic frameworks

---

# DRY

Avoid duplication across:

- event creation
- hashing
- exporter orchestration
- policy logic
- redaction logic

---

# YAGNI

Do not implement features before they are required.

Examples:

- dashboards
- distributed storage
- remote collectors
- OpenTelemetry exporters
- distributed policy engines

must not be added until explicitly requested.

---

# Performance Guidelines

The SDK must:

- minimize object creation in hot paths
- avoid dynamic attribute inspection (`getattr`/`vars`) in hot paths
- avoid importing optional modules at startup
- avoid blocking I/O calls
- use `asyncio` async/await APIs
- support `asyncio.CancelledError` / cancellation signals
- avoid global mutable state

---

# Async Guidelines

Prefer:

- `async`/`await` with `asyncio`
- `asyncio.to_thread` for blocking I/O (file writes, etc.)
- `asyncio.CancelledError` for cancellation

Avoid synchronous I/O inside async functions.

---

# Error Handling

- SDK should not crash host applications by default.
- Exporter failure should not break request execution by default.
- Policy denial should be explicit.
- Failed AI operations must still generate events.

---

# Thread Safety

- All shared services must be thread-safe.
- Avoid mutable shared state.
- Prefer frozen dataclasses (`@dataclasses.dataclass(frozen=True)`) for models.
- Use `threading.Lock` or `asyncio.Lock` where shared mutable state is unavoidable.

---

# Naming Guidelines

Use clear names.

Examples:

Good:

- PromptHasher
- CompositeExporter
- DefaultLocalPolicyEvaluator

Bad:

- Utils
- Helper
- Manager
- Processor

---

# Architecture Guidelines

Prefer:

- composition over inheritance
- protocol-driven architecture (`typing.Protocol`)
- explicit dependencies passed via constructor
- dependency injection via dataclass fields or factory functions

Avoid:

- service locator / global registry
- module-level mutable state
- hidden side effects

---

# Testing Guidelines

All features must have unit tests using `unittest` (standard library).

Tests should cover:

- success scenarios
- failure scenarios
- edge cases
- concurrency
- redaction
- hashing
- policy evaluation
- exporter failures