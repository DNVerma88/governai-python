"""Tests for GovernAI WSGI middleware (governai.wsgi)."""

import asyncio
import io
import unittest

from governai.wsgi.config import GovernAIConfig
from governai.wsgi.middleware import GovernAIMiddleware, GovernAIWSGIApp
from governai.wsgi.resolvers import (
    HeaderTenantResolver,
    HeaderUserResolver,
    _wsgi_environ,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_environ(**kwargs: object) -> dict[str, object]:
    """Build a minimal WSGI environ."""
    base: dict[str, object] = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.StringIO(),
        "wsgi.url_scheme": "http",
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "HTTP_HOST": "localhost",
    }
    base.update(kwargs)
    return base


def _echo_app(environ: dict, start_response):  # type: ignore[no-untyped-def]
    """Minimal WSGI application that echoes 200 OK."""
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"OK"]


def _collect_response(app, environ: dict):  # type: ignore[no-untyped-def]
    """Run *app* against *environ* and collect (status, headers, body)."""
    captured_status: list[str] = []
    captured_headers: list[list[tuple[str, str]]] = []

    def start_response(status, headers, exc_info=None):  # type: ignore[no-untyped-def]
        captured_status.append(status)
        captured_headers.append(headers)

    body_iter = app(environ, start_response)
    body = b"".join(body_iter)
    return captured_status[0], captured_headers[0], body


# ---------------------------------------------------------------------------
# GovernAIConfig
# ---------------------------------------------------------------------------

class TestGovernAIConfig(unittest.TestCase):
    def test_defaults_are_safe(self) -> None:
        config = GovernAIConfig(application_name="TestApp", environment_name="test")
        self.assertEqual(config.application_name, "TestApp")
        self.assertIsNone(config.runtime)
        self.assertIsNone(config.exporter)

    def test_build_runtime_returns_runtime(self) -> None:
        from governai.core.runtime import GovernAIRuntime

        config = GovernAIConfig(application_name="App")
        runtime = config.build_runtime()
        self.assertIsInstance(runtime, GovernAIRuntime)

    def test_build_runtime_uses_provided_runtime(self) -> None:
        from governai.core.options import GovernAIOptions
        from governai.core.runtime import GovernAIRuntime

        options = GovernAIOptions(application_name="X")
        existing_runtime = GovernAIRuntime(options=options)
        config = GovernAIConfig(runtime=existing_runtime)
        self.assertIs(config.build_runtime(), existing_runtime)

    def test_build_runtime_called_twice_returns_same_object_when_provided(self) -> None:
        from governai.core.options import GovernAIOptions
        from governai.core.runtime import GovernAIRuntime

        options = GovernAIOptions(application_name="X")
        existing_runtime = GovernAIRuntime(options=options)
        config = GovernAIConfig(runtime=existing_runtime)
        self.assertIs(config.build_runtime(), config.build_runtime())


# ---------------------------------------------------------------------------
# GovernAIMiddleware — instantiation
# ---------------------------------------------------------------------------

class TestGovernAIMiddlewareInstantiation(unittest.TestCase):
    def test_instantiation_does_not_raise(self) -> None:
        config = GovernAIConfig(application_name="App")
        middleware = GovernAIMiddleware(wsgi_app=_echo_app, config=config)
        self.assertIsNotNone(middleware)

    def test_instantiation_builds_runtime(self) -> None:
        from governai.core.runtime import GovernAIRuntime

        config = GovernAIConfig(application_name="App")
        middleware = GovernAIMiddleware(wsgi_app=_echo_app, config=config)
        self.assertIsInstance(middleware._runtime, GovernAIRuntime)


# ---------------------------------------------------------------------------
# GovernAIMiddleware — correlation ID
# ---------------------------------------------------------------------------

class TestGovernAIMiddlewareCorrelationId(unittest.TestCase):
    def _middleware(self) -> GovernAIMiddleware:
        return GovernAIMiddleware(
            wsgi_app=_echo_app,
            config=GovernAIConfig(application_name="App"),
        )

    def test_generates_correlation_id_when_absent(self) -> None:
        environ = _make_environ()
        _, headers, _ = _collect_response(self._middleware(), environ)
        header_map = dict(headers)
        self.assertIn("X-Correlation-Id", header_map)
        self.assertTrue(header_map["X-Correlation-Id"])

    def test_reuses_inbound_correlation_id(self) -> None:
        environ = _make_environ(**{"HTTP_X_CORRELATION_ID": "my-existing-id"})
        _, headers, _ = _collect_response(self._middleware(), environ)
        header_map = dict(headers)
        self.assertEqual(header_map["X-Correlation-Id"], "my-existing-id")

    def test_generated_ids_are_unique_per_request(self) -> None:
        mw = self._middleware()
        ids = set()
        for _ in range(5):
            _, headers, _ = _collect_response(mw, _make_environ())
            ids.add(dict(headers)["X-Correlation-Id"])
        self.assertEqual(len(ids), 5)

    def test_oversized_inbound_id_replaced_with_new(self) -> None:
        oversized = "x" * 200
        environ = _make_environ(**{"HTTP_X_CORRELATION_ID": oversized})
        _, headers, _ = _collect_response(self._middleware(), environ)
        self.assertNotEqual(dict(headers)["X-Correlation-Id"], oversized)

    def test_crlf_in_correlation_id_is_rejected(self) -> None:
        """Correlation ID containing CRLF must be discarded and replaced (OWASP A03 — Header Injection)."""
        crlf_id = "legit-id\r\nX-Injected: evil"
        environ = _make_environ(**{"HTTP_X_CORRELATION_ID": crlf_id})
        _, headers, _ = _collect_response(self._middleware(), environ)
        header_map = dict(headers)
        # The injected value must never appear in the response headers.
        self.assertNotIn("X-Injected", header_map)
        # A fresh ID must have been generated instead.
        self.assertNotEqual(header_map.get("X-Correlation-Id"), crlf_id)
        # The replacement must not contain CRLF.
        self.assertNotIn("\r", header_map.get("X-Correlation-Id", ""))
        self.assertNotIn("\n", header_map.get("X-Correlation-Id", ""))

    def test_correlation_id_injected_into_environ(self) -> None:
        captured: list[dict] = []

        def capturing_app(environ, start_response):  # type: ignore[no-untyped-def]
            captured.append(dict(environ))
            start_response("200 OK", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=capturing_app, config=GovernAIConfig())
        _collect_response(mw, _make_environ(**{"HTTP_X_CORRELATION_ID": "abc"}))
        self.assertEqual(captured[0]["governai.correlation_id"], "abc")


# ---------------------------------------------------------------------------
# GovernAIMiddleware — environ injection
# ---------------------------------------------------------------------------

class TestGovernAIMiddlewareEnviron(unittest.TestCase):
    def test_runtime_injected_into_environ(self) -> None:
        captured: list[dict] = []

        def app(environ, start_response):  # type: ignore[no-untyped-def]
            captured.append(dict(environ))
            start_response("200 OK", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        _collect_response(mw, _make_environ())
        self.assertIn("governai.runtime", captured[0])

    def test_tenant_id_from_header(self) -> None:
        captured: list[dict] = []

        def app(environ, start_response):  # type: ignore[no-untyped-def]
            captured.append(dict(environ))
            start_response("200 OK", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        environ = _make_environ(**{"HTTP_X_TENANT_ID": "tenant-abc"})
        _collect_response(mw, environ)
        self.assertEqual(captured[0]["governai.tenant_id"], "tenant-abc")

    def test_user_id_from_header(self) -> None:
        captured: list[dict] = []

        def app(environ, start_response):  # type: ignore[no-untyped-def]
            captured.append(dict(environ))
            start_response("200 OK", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        environ = _make_environ(**{"HTTP_X_USER_ID": "user-xyz"})
        _collect_response(mw, environ)
        self.assertEqual(captured[0]["governai.user_id"], "user-xyz")

    def test_user_id_from_app_environ_key(self) -> None:
        captured: list[dict] = []

        def app(environ, start_response):  # type: ignore[no-untyped-def]
            captured.append(dict(environ))
            start_response("200 OK", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        environ = _make_environ(**{"governai.user_id": "app-set-user"})
        _collect_response(mw, environ)
        self.assertEqual(captured[0]["governai.user_id"], "app-set-user")

    def test_does_not_read_wsgi_input(self) -> None:
        """Middleware must not consume wsgi.input."""
        body = b"sensitive request body"
        buf = io.BytesIO(body)

        def app(environ, start_response):  # type: ignore[no-untyped-def]
            start_response("200 OK", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        environ = _make_environ(**{"wsgi.input": buf})
        _collect_response(mw, environ)
        # Buffer position should be at 0 — middleware did not read it
        self.assertEqual(buf.tell(), 0)


# ---------------------------------------------------------------------------
# GovernAIMiddleware — response passthrough
# ---------------------------------------------------------------------------

class TestGovernAIMiddlewareResponsePassthrough(unittest.TestCase):
    def test_response_body_passed_through(self) -> None:
        def app(environ, start_response):  # type: ignore[no-untyped-def]
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"Hello, world!"]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        _, _, body = _collect_response(mw, _make_environ())
        self.assertEqual(body, b"Hello, world!")

    def test_response_status_passed_through(self) -> None:
        def app(environ, start_response):  # type: ignore[no-untyped-def]
            start_response("404 Not Found", [])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        status, _, _ = _collect_response(mw, _make_environ())
        self.assertEqual(status, "404 Not Found")

    def test_existing_response_headers_preserved(self) -> None:
        def app(environ, start_response):  # type: ignore[no-untyped-def]
            start_response("200 OK", [("X-Custom-Header", "custom-value")])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        _, headers, _ = _collect_response(mw, _make_environ())
        header_map = dict(headers)
        self.assertIn("X-Custom-Header", header_map)

    def test_correlation_id_not_duplicated_if_app_sets_it(self) -> None:
        def app(environ, start_response):  # type: ignore[no-untyped-def]
            start_response("200 OK", [("X-Correlation-Id", "from-app")])
            return [b""]

        mw = GovernAIMiddleware(wsgi_app=app, config=GovernAIConfig())
        _, headers, _ = _collect_response(mw, _make_environ())
        count = sum(1 for name, _ in headers if name == "X-Correlation-Id")
        # Middleware should not add a second one if the app already set it
        self.assertEqual(count, 1)


# ---------------------------------------------------------------------------
# HeaderTenantResolver
# ---------------------------------------------------------------------------

class TestHeaderTenantResolver(unittest.TestCase):
    def _run(self, coro):  # type: ignore[no-untyped-def]
        return asyncio.run(coro)

    def test_returns_tenant_from_environ(self) -> None:
        resolver = HeaderTenantResolver()
        token = _wsgi_environ.set({"HTTP_X_TENANT_ID": "tenant-123"})  # type: ignore[arg-type]
        try:
            result = self._run(resolver.resolve_tenant_id_async(None))
        finally:
            _wsgi_environ.reset(token)
        self.assertEqual(result, "tenant-123")

    def test_returns_empty_when_header_absent(self) -> None:
        resolver = HeaderTenantResolver()
        token = _wsgi_environ.set({})  # type: ignore[arg-type]
        try:
            result = self._run(resolver.resolve_tenant_id_async(None))
        finally:
            _wsgi_environ.reset(token)
        self.assertEqual(result, "")

    def test_returns_empty_when_context_var_not_set(self) -> None:
        resolver = HeaderTenantResolver()
        result = self._run(resolver.resolve_tenant_id_async(None))
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# HeaderUserResolver
# ---------------------------------------------------------------------------

class TestHeaderUserResolver(unittest.TestCase):
    def _run(self, coro):  # type: ignore[no-untyped-def]
        return asyncio.run(coro)

    def test_returns_user_from_header(self) -> None:
        resolver = HeaderUserResolver()
        token = _wsgi_environ.set({"HTTP_X_USER_ID": "user-456"})  # type: ignore[arg-type]
        try:
            result = self._run(resolver.resolve_user_id_async(None))
        finally:
            _wsgi_environ.reset(token)
        self.assertEqual(result, "user-456")

    def test_app_environ_key_takes_priority(self) -> None:
        resolver = HeaderUserResolver()
        token = _wsgi_environ.set(  # type: ignore[arg-type]
            {"governai.user_id": "app-user", "HTTP_X_USER_ID": "header-user"}
        )
        try:
            result = self._run(resolver.resolve_user_id_async(None))
        finally:
            _wsgi_environ.reset(token)
        self.assertEqual(result, "app-user")

    def test_returns_empty_when_neither_present(self) -> None:
        resolver = HeaderUserResolver()
        token = _wsgi_environ.set({})  # type: ignore[arg-type]
        try:
            result = self._run(resolver.resolve_user_id_async(None))
        finally:
            _wsgi_environ.reset(token)
        self.assertEqual(result, "")

    def test_returns_empty_when_context_var_not_set(self) -> None:
        resolver = HeaderUserResolver()
        result = self._run(resolver.resolve_user_id_async(None))
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# GovernAIWSGIApp
# ---------------------------------------------------------------------------

class TestGovernAIWSGIApp(unittest.TestCase):
    def test_wraps_app_transparently(self) -> None:
        config = GovernAIConfig(application_name="App")
        wrapper = GovernAIWSGIApp(wsgi_app=_echo_app, config=config)
        status, headers, body = _collect_response(wrapper, _make_environ())
        self.assertEqual(status, "200 OK")
        self.assertEqual(body, b"OK")
        self.assertIn("X-Correlation-Id", dict(headers))


if __name__ == "__main__":
    unittest.main()
