# Phase 4 - Python WSGI Integration

## Goal

Add Python WSGI integration for GovernAI.

This phase must provide configuration helpers, WSGI middleware, correlation handling, tenant resolution, and user resolution.

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
/copilot/phase-4-wsgi.md
```

---

## Scope

Implement only `governai.wsgi`.

Do not implement:

- OpenTelemetry
- Collector
- Remote Policy Server
- Dashboard
- Database storage

---

## Required Components

Create these in `governai/wsgi/`:

```text
GovernAIMiddleware          (WSGI middleware class)
GovernAIConfig              (configuration dataclass)
HeaderTenantResolver        (resolves tenant from HTTP header)
HeaderUserResolver          (resolves user from HTTP header or environ)
GovernAIWSGIApp             (convenience WSGI wrapper)
```

Use only Python standard library (`wsgiref`, `http`, `uuid`, `re`, `json`).

---

## Configuration

Support this usage:

```python
from governai.wsgi import GovernAIConfig, GovernAIMiddleware

config = GovernAIConfig(
    application_name="Enterprise.Api",
    environment_name="production",
)

app = GovernAIMiddleware(wsgi_app=your_app, config=config)
```

`GovernAIConfig` must hold:

```text
GovernAIOptions
GovernAIClock
GovernAIPolicyEvaluator
GovernAIExporter
GovernAIRedactor
GovernAITenantResolver
GovernAIUserResolver
GovernAIRuntime / GovernAITracker
```

Use safe defaults (NoOp implementations).

---

## Middleware

The `GovernAIMiddleware` class must be a standard WSGI middleware:

```python
class GovernAIMiddleware:
    def __init__(self, wsgi_app, config: GovernAIConfig) -> None: ...

    def __call__(self, environ: dict, start_response) -> Iterable[bytes]: ...
```

Middleware must:

- create correlation ID (`uuid.uuid4().hex`) if `HTTP_X_CORRELATION_ID` is missing
- reuse `X-Correlation-Id` if present in request headers
- add correlation ID to response headers
- avoid reading `wsgi.input` (request body)
- avoid logging request body
- not block normal request execution

---

## Tenant Resolution

Support tenant resolution from:

```text
HTTP_X_TENANT_ID environ key (X-Tenant-Id header)
custom resolver callable
```

Priority:

```text
custom resolver
HTTP_X_TENANT_ID header
empty
```

---

## User Resolution

Support user resolution from:

```text
HTTP_X_USER_ID environ key (X-User-Id header)
governai.user_id environ key set by application
custom resolver callable
```

Priority:

```text
custom resolver
environ key
header
empty
```

---

## Endpoint Extensions

Provide simple endpoint extension hooks if needed.

Do not over-engineer.

---

## Security Rules

- Do not read request body.
- Do not store secrets.
- Do not log headers wholesale.
- Do not log authorization header.
- Do not log cookies.
- Do not fail request pipeline due to GovernAI internal errors by default.

---

## Tests

Add tests using `unittest` for:

- middleware instantiation
- correlation ID generation
- existing correlation ID reuse
- tenant from header
- user from environ
- middleware does not read request body

---

## Acceptance Criteria

- Python WSGI sample runs.
- `GovernAIMiddleware` wraps any WSGI app.
- Correlation ID behavior works.
- Tenant/user resolution works.
- No external package added.
- Tests pass.