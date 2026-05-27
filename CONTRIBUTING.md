# Contributing to GovernAI

Thank you for your interest in contributing to the GovernAI Python SDK.

---

## Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/DNVerma88/governai-python.git
cd governai-python
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install in editable mode with dev dependencies

```bash
pip install -e .[dev]
```

---

## Running Tests

```bash
python -m unittest discover tests -v
```

---

## Type Checking

```bash
python -m mypy src
```

---

## Building Distribution Packages

```bash
python -m build
```

---

## Dependency Policy

GovernAI uses the **Python standard library only**. Do not add any third-party dependencies to the core packages (`governai.abstractions`, `governai.core`, `governai.security`, `governai.wsgi`). Development tools (`mypy`, `build`) belong in `[project.optional-dependencies] dev` only.

---


## Coding Standards

See [docs/coding-guidelines.md](docs/coding-guidelines.md).

---

## Security Guidelines

See [docs/security-guidelines.md](docs/security-guidelines.md).

---

## Architecture

See [docs/architecture.md](docs/architecture.md).

---

## Branch Strategy

- `main` — stable releases
- `develop` — active development
- Feature branches: `feature/<description>`

---

## Pull Request Requirements

- All tests must pass.
- No new external package dependencies unless explicitly approved.
- All public APIs must have docstrings.
- Type annotations required on all public functions and classes.
