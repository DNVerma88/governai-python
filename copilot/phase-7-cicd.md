# Phase 7 - CI/CD

## Goal

Prepare GovernAI repository for OSS-ready build, test, and package validation.

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
/copilot/phase-7-cicd.md
```

---

## Scope

Add CI/CD readiness only.

Do not publish to PyPI in this phase.

---

## Required Files

Create or update:

```text
.github/workflows/build.yml
.editorconfig
.gitignore
LICENSE
CONTRIBUTING.md
pyproject.toml
```

---

## GitHub Actions Workflow

The workflow must:

- run on pull request
- run on main branch push
- install dependencies from source
- run type checking (mypy)
- run tests (unittest)
- build distribution packages (wheel + sdist)
- upload package artifacts if appropriate
- not publish to PyPI

---

## Python Versions

Test against:

```text
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Use a matrix strategy in GitHub Actions so all versions are validated.

---

## Required Commands

Workflow should run equivalent of:

```bash
pip install -e .[dev]
python -m mypy src
python -m unittest discover -s tests
python -m build
```

---

## Packaging Requirements

Distributions:

```text
governai-abstractions
governai-core
governai-security
governai-wsgi
```

Do not publish packages.

---

## OSS Files

### LICENSE

Use MIT unless changed by repository owner.

### CONTRIBUTING.md

Include:

- how to set up a virtual environment
- how to install from source (`pip install -e .`)
- how to run tests (`python -m unittest discover`)
- coding guidelines
- dependency policy (standard library only)
- security-first contribution expectations

---

## Acceptance Criteria

- CI file is valid.
- Install/lint step exists.
- Test step exists.
- Build/package step exists.
- No publish step.
- Matrix covers Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- Repository is ready for PR validation.