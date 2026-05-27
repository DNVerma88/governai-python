# Phase 2 - Core Runtime

## Goal

Implement the local-first GovernAI runtime engine.

This phase must add runtime tracking, hashing, policy evaluation orchestration, and local exporters.

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
/copilot/phase-2-core-runtime.md
```

---

## Scope

Implement only `governai.core`.

Do not implement:

- Python WSGI middleware
- Security scanning
- OpenTelemetry
- Collector
- Remote Policy Server
- Dashboard
- Database storage

---

## Required Classes

Create these in `governai/core/`:

```text
GovernAIRuntime
GovernAITracker
GovernAIOptions
SystemClock
PromptHasher
ResponseHasher
NoOpPolicyEvaluator
NoOpExporter
CompositeExporter
InMemoryExporter
ConsoleExporter
FileExporter
```

---

## Runtime Behavior

The runtime must support tracking AI operations.

Required usage style:

```python
response = await govern_ai.track_async(
    context=context,
    operation=lambda: execute_ai_call_async(context.prompt),
)
```

The runtime must:

1. accept `GovernAIContext`
2. evaluate policy using `GovernAIPolicyEvaluator`
3. skip operation when decision is `DENY`
4. execute operation when decision is `ALLOW` or `REVIEW`
5. measure duration
6. hash prompt
7. hash response
8. create `GovernAIEvent`
9. export event using `GovernAIExporter`
10. capture success/failure
11. never store raw prompt/response by default

---

## `GovernAIOptions`

Must support:

```text
ApplicationName
EnvironmentName
EnablePromptHashing
EnableResponseHashing
AllowRawPromptCapture
AllowRawResponseCapture
FailOnExporterError
InMemoryExporterCapacity
FileExporterPath
```

Defaults:

```text
EnablePromptHashing = true
EnableResponseHashing = true
AllowRawPromptCapture = false
AllowRawResponseCapture = false
FailOnExporterError = false
InMemoryExporterCapacity = 1000
```

---

## Hashing

### `PromptHasher`

- Use `hashlib.sha256` (standard library).
- Return lowercase hex string.
- Return empty string for `None`/empty input.
- Do not use external packages.

### `ResponseHasher`

- Use `hashlib.sha256` (standard library).
- Return lowercase hex string.
- Return empty string for `None`/empty input.
- Do not use external packages.

---

## Policy Evaluation

### `NoOpPolicyEvaluator`

Always returns:

```text
Decision = Allow
RiskScore = 0
RiskLevel = None
RiskCategory = None
Reason = No policy evaluator configured
```

---

## Exporters

### `NoOpExporter`

Does nothing.

### `CompositeExporter`

- Accepts multiple exporters.
- Exports to all exporters.
- If one exporter fails, continue to next exporter when `FailOnExporterError = false`.
- If `FailOnExporterError = true`, throw.

### `InMemoryExporter`

- Stores bounded number of events.
- Default capacity: 1000.
- Must be thread-safe.

### `ConsoleExporter`

- Writes event as JSON to console.
- Use `json` (standard library).

### `FileExporter`

- Writes event as JSON Lines.
- One event per line.
- Must use `asyncio` async file APIs (`asyncio.to_thread` for file I/O).
- Must be thread-safe.

---

## Event Creation Rules

`GovernAIEvent` must be populated according to `/docs/event-schema.md`.

Rules:

- Generate `EventId` if missing.
- Use UTC timestamp.
- Calculate `TotalTokens` when possible.
- Capture duration in milliseconds.
- Include sanitized error message.
- Do not include raw prompt/response.

---

## Error Handling

- If AI operation fails, export failure event and rethrow original exception.
- If exporter fails and `FailOnExporterError = false`, do not throw.
- If exporter fails and `FailOnExporterError = true`, throw exporter exception.
- Policy denial should not execute AI operation.

---

## Tests

Add tests for:

- successful operation tracking
- failed operation tracking
- policy deny behavior
- prompt hashing
- response hashing
- in-memory exporter capacity
- composite exporter behavior
- exporter failure handling
- total token calculation
- duration capture

---

## Acceptance Criteria

- Core runtime works without external dependencies.
- Successful AI calls generate events.
- Failed AI calls generate events.
- Policy denial prevents execution.
- Prompt and response are hashed.
- Raw prompt/response are not stored.
- Tests pass.