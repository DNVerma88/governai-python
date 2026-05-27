# GovernAI Event Schema

## Purpose

`GovernAIEvent` is the primary audit and governance event produced by the SDK.

It must be:

- provider-neutral
- cloud-neutral
- tenant-aware
- privacy-safe
- collector-ready
- OpenTelemetry-ready
- cross-language friendly

The schema must not depend on any specific AI provider.

---

## GovernAIEvent Required Fields

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

---

## Field Definitions

### EventId

Unique ID for each GovernAI event.

Recommended format:

```text
GUID without hyphen
```

---

### TraceId

Distributed trace ID if available.

Used for correlation with application logs and telemetry.

---

### CorrelationId

Request or operation-level correlation ID.

In Python web integrations, this may come from:

```text
X-Correlation-Id
```

If missing, GovernAI should generate one.

---

### ApplicationName

Name of the application using GovernAI.

Example:

```text
Enterprise.Api
```

---

### EnvironmentName

Runtime environment.

Examples:

```text
Development
QA
Staging
Production
```

---

### TenantId

Tenant identifier.

Rules:

- Must support multi-tenant apps.
- Can be empty if app is not multi-tenant.
- Must not assume a specific tenant model.

---

### UserId

User identifier.

Rules:

- Should be resolved from claims where possible.
- Can be empty for system/background operations.
- Should not store full user profile data.

---

### AgentName

Logical AI agent or workflow name.

Examples:

```text
ReportAgent
DocumentSummaryAgent
DataQueryAgent
```

---

### OperationName

Name of the AI operation.

Examples:

```text
GenerateSummary
ClassifyDocument
GenerateSqlQuery
ExtractTerms
```

---

### ModelProvider

Name of the model provider.

Examples:

```text
AzureOpenAI
OpenAI
Anthropic
Gemini
Bedrock
LocalModel
Unknown
```

GovernAI must not depend on any provider SDK.

---

### ModelName

Model name supplied by the application.

Examples:

```text
gpt-4.1
gpt-4o
claude-sonnet
gemini-pro
local-llama
```

---

### PromptHash

SHA-256 hash of the prompt.

Rules:

- Required when prompt is available.
- Raw prompt must not be stored by default.
- Empty if no prompt is provided.

---

### ResponseHash

SHA-256 hash of the response.

Rules:

- Required when response is available.
- Raw response must not be stored by default.
- Empty if no response is provided.

---

### InputTokens

Input token count if available.

Rules:

- Optional.
- SDK should not calculate tokens in MVP.
- Application can provide this value.

---

### OutputTokens

Output token count if available.

Rules:

- Optional.
- SDK should not calculate tokens in MVP.
- Application can provide this value.

---

### TotalTokens

Total token count.

Rules:

```text
TotalTokens = InputTokens + OutputTokens
```

when both values are available.

---

### RiskScore

Numeric risk score.

Recommended range:

```text
0 - 100
```

---

### RiskLevel

Risk classification.

Allowed values:

```text
None
Low
Medium
High
Critical
```

---

### RiskCategory

Human-readable risk category.

Examples:

```text
PromptInjection
SensitiveData
SecretExposure
Unknown
```

---

### PolicyDecision

Policy result.

Allowed values:

```text
Allow
Review
Deny
```

---

### PolicyReason

Reason behind policy decision.

Examples:

```text
Low risk prompt
Potential prompt injection detected
Critical secret exposure risk detected
```

---

### DurationMs

Operation duration in milliseconds.

Measured from before policy evaluation/execution to event creation.

---

### Success

Indicates whether the tracked AI operation completed successfully.

---

### ErrorCode

Optional error code.

Should be empty when operation succeeds.

---

### ErrorMessage

Optional sanitized error message.

Do not store secrets in error messages.

---

### TimestampUtc

UTC timestamp when event is created.

Must use UTC.

---

### Metadata

String-based key-value dictionary for extensibility.

Rules:

- Keys must be strings.
- Values must be strings.
- Do not store secrets.
- Do not store raw prompts by default.
- Keep cross-language compatibility.

---

## Raw Prompt and Response Rules

By default:

```text
RawPrompt = disabled
RawResponse = disabled
```

Raw capture may be allowed only when explicitly enabled for local development or controlled debugging.

MVP should avoid adding raw fields unless explicitly required.

---

## Hashing Rules

Use SHA-256.

Hashing must be deterministic.

Input normalization should be minimal and predictable.

Do not use external hashing packages.

---

## Token Rules

The SDK should not implement token counting in MVP.

Reason:

- Token counting varies by model/provider.
- Tokenization requires provider-specific logic.
- External tokenizer dependencies are not allowed in MVP.

Applications may provide token values manually.

---

## OpenTelemetry Readiness

The schema should later map to OpenTelemetry GenAI conventions.

Potential mappings:

```text
ModelProvider   -> gen_ai.system
ModelName       -> gen_ai.request.model / gen_ai.response.model
OperationName   -> gen_ai.operation.name
InputTokens     -> gen_ai.usage.input_tokens
OutputTokens    -> gen_ai.usage.output_tokens
AgentName       -> gen_ai.agent.name
DurationMs      -> span duration
Success         -> span status
```

Do not implement OpenTelemetry in MVP.

---

## Collector Readiness

`GovernAIEvent` must be serializable to JSON.

Future Collector flow:

```text
GovernAIEvent
   |
HTTP Exporter
   |
GovernAI Collector
   |
Storage / Dashboard / SIEM
```

Do not implement Collector in MVP.

---

## Example Event

```json
{
  "eventId": "8f5b6b4d68b84cf6942b6cc5d30e7f84",
  "traceId": "trace-123",
  "correlationId": "corr-123",
  "applicationName": "Enterprise.Api",
  "environmentName": "Development",
  "tenantId": "tenant-001",
  "userId": "user-001",
  "agentName": "ReportAgent",
  "operationName": "GenerateSummary",
  "modelProvider": "AzureOpenAI",
  "modelName": "gpt-4.1",
  "promptHash": "sha256-value",
  "responseHash": "sha256-value",
  "inputTokens": 1200,
  "outputTokens": 300,
  "totalTokens": 1500,
  "riskScore": 10,
  "riskLevel": "Low",
  "riskCategory": "None",
  "policyDecision": "Allow",
  "policyReason": "Low risk prompt",
  "durationMs": 850,
  "success": true,
  "errorCode": "",
  "errorMessage": "",
  "timestampUtc": "2026-05-25T00:00:00Z",
  "metadata": {
    "feature": "reporting"
  }
}
```