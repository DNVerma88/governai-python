# Phase 5 - Samples

## Goal

Create working samples that demonstrate GovernAI usage without connecting to any real AI provider.

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
/copilot/phase-5-samples.md
```

---

## Scope

Create samples only.

Do not implement new SDK features unless required to make samples compile.

---

## Required Samples

```text
samples/sample_basic/
samples/sample_multi_tenant/
samples/sample_policy_demo/
```

---

## Sample 1: `sample_basic`

Must demonstrate:

- configuring GovernAI
- using `GovernAIMiddleware`
- tracking a fake AI call
- console exporter
- returning fake response

Serve using Python's built-in `wsgiref.simple_server`.
No real AI provider.

---

## Sample 2: `sample_multi_tenant`

Must demonstrate:

- tenant ID from `X-Tenant-Id` header
- user ID from `X-User-Id` header or environ
- event includes tenant ID
- tracking fake AI operation

No real AI provider.

---

## Sample 3: `sample_policy_demo`

Must demonstrate:

- safe prompt allowed
- risky prompt reviewed
- critical prompt denied
- sensitive data redaction example

No real AI provider.

---

## Fake AI Provider

Create a simple fake AI function inside samples:

```python
async def fake_ai_call_async(prompt: str) -> str:
    return f"Fake AI response for: {prompt}"
```

Do not call:

- OpenAI
- Azure OpenAI
- Anthropic
- Gemini
- AWS Bedrock

---

## README Updates

Update sample documentation with:

```text
how to run each sample
expected behavior
sample requests
sample responses
```

---

## Acceptance Criteria

- All samples run with `python -m sample_basic` (or equivalent).
- All samples run locally using `wsgiref.simple_server`.
- No real AI provider used.
- No external dependency added.