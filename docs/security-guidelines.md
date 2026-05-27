# GovernAI Security Guidelines

# Security Goals

GovernAI must help applications improve AI runtime governance and reduce common LLM-related risks.

---

# OWASP LLM Alignment

GovernAI should align with OWASP LLM risk areas:

- Prompt Injection
- Sensitive Information Disclosure
- Insecure Output Handling
- Excessive Agency
- Supply Chain Vulnerabilities
- Model Denial of Service
- Insecure Plugin/Tool Design

---

# Secure Defaults

GovernAI must always prioritize secure defaults.

## Prompt Storage

- Raw prompts must NOT be stored by default.
- Raw responses must NOT be stored by default.

## Hashing

Use SHA-256 for:

- prompt hashing
- response hashing

---

# Sensitive Data Redaction

GovernAI should redact:

- email addresses
- phone numbers
- bearer tokens
- API keys
- JWT tokens
- passwords
- connection strings
- secret-like values

---

# Prompt Injection Detection

Detect risky prompt patterns such as:

- ignore previous instructions
- reveal system prompt
- bypass security
- disable policy
- print secrets
- hidden instructions
- jailbreak attempts
- system prompt extraction

---

# Policy Decisions

Support:

- Allow
- Review
- Deny

Recommended default behavior:

```text
Low Risk      => Allow
Medium Risk   => Allow with warning
High Risk     => Review
Critical Risk => Deny
```

---

# Logging Rules

GovernAI must:

- avoid logging secrets
- avoid logging tokens
- avoid logging request bodies
- avoid logging raw prompts by default
- avoid logging raw responses by default

---

# Privacy Principles

GovernAI must be privacy-first.

Applications may explicitly enable raw prompt/response capture for local development only.

---

# Security Limitations

GovernAI does NOT guarantee:

- full prompt injection prevention
- full jailbreak prevention
- complete AI security

The SDK provides heuristic-based protection and governance assistance only.