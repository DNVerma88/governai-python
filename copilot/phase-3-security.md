# Phase 3 - Security

## Goal

Implement basic local security capabilities.

This phase adds redaction, sensitive data detection, prompt injection heuristic scanning, risk scoring, and default local policy evaluation.

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
/copilot/phase-3-security.md
```

---

## Scope

Implement only `governai.security`.

Do not implement:

- Python WSGI middleware
- OpenTelemetry
- Collector
- Remote Policy Server
- Dashboard
- Database storage

---

## Required Classes

Create these in `governai/security/`:

```text
BasicPiiRedactor
SensitiveDataScanner
PromptInjectionHeuristicScanner
RiskScoreCalculator
DefaultLocalPolicyEvaluator
```

---

## `BasicPiiRedactor`

Must implement the `GovernAIRedactor` protocol.

Redact:

```text
Email addresses
Phone numbers
Credit card-like numbers
API keys
Bearer tokens
JWT-like tokens
SQL connection strings
Azure Storage connection strings
Password-like key/value pairs
```

Replacement examples:

```text
[REDACTED_EMAIL]
[REDACTED_PHONE]
[REDACTED_CARD]
[REDACTED_API_KEY]
[REDACTED_TOKEN]
[REDACTED_CONNECTION_STRING]
[REDACTED_SECRET]
```

---

## `SensitiveDataScanner`

Must detect sensitive data patterns.

Return a `GovernAIRiskResult`.

Risk mapping suggestion:

```text
Email only => Low
Phone only => Low
Bearer token/API key/JWT => High
Connection string/password => Critical
Credit card-like number => High
```

---

## `PromptInjectionHeuristicScanner`

Must detect prompt injection-like patterns.

Detect phrases including:

```text
ignore previous instructions
ignore all previous instructions
reveal system prompt
show system prompt
print system prompt
bypass security
disable policy
disable guardrails
print secrets
show secrets
exfiltrate data
jailbreak
developer message
system message
hidden prompt
override instructions
act as unrestricted
```

Risk mapping suggestion:

```text
weak suspicious pattern => Medium
system prompt extraction => High
secret extraction => Critical
bypass/disable policy => High
jailbreak => High
```

---

## `RiskScoreCalculator`

Must combine scanner results.

Risk score range:

```text
0 - 100
```

Risk level mapping:

```text
0      => None
1-30   => Low
31-60  => Medium
61-85  => High
86-100 => Critical
```

---

## `DefaultLocalPolicyEvaluator`

Must implement the `GovernAIPolicyEvaluator` protocol.

Policy behavior:

```text
None      => Allow
Low       => Allow
Medium    => Allow
High      => Review
Critical  => Deny
```

Must evaluate:

- prompt injection risk
- sensitive data risk

---

## Security Limitations

Do not claim full protection.

The implementation is heuristic-based and intended for governance assistance only.

---

## Dependency Rules

Do not add external packages.

Use only the Python standard library (`re`, `hashlib`, `hmac`, `dataclasses`, `enum`, `typing`).

---

## Tests

Add tests for:

- email redaction
- phone redaction
- bearer token redaction
- API key redaction
- connection string redaction
- prompt injection detection
- risk score mapping
- policy allow
- policy review
- policy deny
- null/empty input handling

---

## Acceptance Criteria

- Sensitive data is redacted.
- Prompt injection-like input is detected.
- Policy evaluator returns Allow/Review/Deny.
- No external dependencies are added.
- Tests pass.