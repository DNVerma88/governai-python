"""GovernAI WSGI middleware.

Provides ``GovernAIMiddleware``, a standard PEP 3333 WSGI middleware that:

- Generates or propagates a correlation ID via the ``X-Correlation-Id``
  header.
- Populates the WSGI environ with ``governai.runtime``,
  ``governai.correlation_id``, ``governai.tenant_id``, and
  ``governai.user_id`` for downstream use.
- Sets the ``_wsgi_environ`` context variable so that tenant and user
  resolvers can access request context without being passed the environ
  explicitly.
- Adds the correlation ID to response headers.
- Does **not** read the request body (``wsgi.input``).
- Does **not** fail the request pipeline on GovernAI internal errors by
  default.

Also provides ``GovernAIWSGIApp``, a convenience class that wraps a
bare WSGI callable with ``GovernAIMiddleware``.
"""

from __future__ import annotations

import logging
import uuid
from typing import Callable, Iterable

from governai.wsgi.config import GovernAIConfig
from governai.wsgi.resolvers import _wsgi_environ

_logger = logging.getLogger(__name__)

# Maximum length of the correlation ID accepted from the inbound header.
# Values longer than this are ignored and a new ID is generated.
_MAX_CORRELATION_ID_LEN = 128


class GovernAIMiddleware:
    """Standard WSGI middleware that integrates GovernAI governance.

    Wraps any WSGI application and enriches the request/response cycle
    with GovernAI correlation, tenant, and user identification.

    Usage::

        from governai.wsgi import GovernAIConfig, GovernAIMiddleware

        config = GovernAIConfig(
            application_name="MyApp",
            environment_name="production",
        )
        wrapped_app = GovernAIMiddleware(wsgi_app=my_wsgi_app, config=config)

    The following keys are injected into the WSGI ``environ`` dict before
    the wrapped application is called:

    ``governai.runtime``
        The ``GovernAIRuntime`` instance for this middleware instance.
    ``governai.correlation_id``
        The correlation ID (either reused from the inbound
        ``X-Correlation-Id`` header or freshly generated).
    ``governai.tenant_id``
        Tenant ID resolved by the configured ``GovernAITenantResolver``
        (or empty string if unresolved).
    ``governai.user_id``
        User ID resolved by the configured ``GovernAIUserResolver``
        (or empty string if unresolved).
    """

    def __init__(self, wsgi_app: Callable, config: GovernAIConfig) -> None:
        """Initialise the middleware.

        Args:
            wsgi_app: The WSGI application to wrap.
            config: GovernAI configuration. A ``GovernAIRuntime`` is
                built from this config if one is not already provided.
        """
        self._app = wsgi_app
        self._config = config
        self._runtime = config.build_runtime()

    def __call__(
        self,
        environ: dict[str, object],
        start_response: Callable,
    ) -> Iterable[bytes]:
        """Handle a single WSGI request.

        Args:
            environ: The WSGI environment dictionary.
            start_response: The WSGI ``start_response`` callable.

        Returns:
            An iterable of response body byte strings, as per PEP 3333.
        """
        # ------------------------------------------------------------------
        # 1. Correlation ID
        # Validate the inbound header: must be a non-empty string, within
        # the length limit, and must not contain CRLF sequences that would
        # allow HTTP response-header injection.
        # ------------------------------------------------------------------
        raw_correlation_id = environ.get("HTTP_X_CORRELATION_ID", "")
        if (
            raw_correlation_id
            and isinstance(raw_correlation_id, str)
            and len(raw_correlation_id) <= _MAX_CORRELATION_ID_LEN
            and "\r" not in raw_correlation_id
            and "\n" not in raw_correlation_id
        ):
            correlation_id = raw_correlation_id
        else:
            correlation_id = uuid.uuid4().hex

        # ------------------------------------------------------------------
        # 2. Populate environ with GovernAI values
        # ------------------------------------------------------------------
        environ["governai.runtime"] = self._runtime
        environ["governai.correlation_id"] = correlation_id

        # ------------------------------------------------------------------
        # 3. Set ContextVar so that resolvers can access the environ
        # ------------------------------------------------------------------
        token = _wsgi_environ.set(environ)  # type: ignore[arg-type]

        # ------------------------------------------------------------------
        # 4. Resolve tenant and user (best-effort; never fail the request)
        # ------------------------------------------------------------------
        tenant_id = ""
        user_id = ""
        try:
            import asyncio  # noqa: PLC0415 — lazily imported to keep startup light

            def _run_coro(coro):  # type: ignore[no-untyped-def]
                """Run a coroutine safely regardless of whether an event loop is running."""
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop is not None and loop.is_running():
                    # We are inside an async context (e.g. Uvicorn/Hypercorn).
                    # Run the coroutine in a new thread with its own event loop
                    # to avoid "This event loop is already running".
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(asyncio.run, coro)
                        return future.result()
                else:
                    return asyncio.run(coro)

            if self._config.tenant_resolver is not None:
                tenant_id = _run_coro(
                    self._config.tenant_resolver.resolve_tenant_id_async(None)
                ) or ""
            else:
                tenant_id = str(environ.get("HTTP_X_TENANT_ID", ""))

            if self._config.user_resolver is not None:
                user_id = _run_coro(
                    self._config.user_resolver.resolve_user_id_async(None)
                ) or ""
            else:
                app_user = environ.get("governai.user_id", "")
                if app_user:
                    user_id = str(app_user)
                else:
                    user_id = str(environ.get("HTTP_X_USER_ID", ""))
        except Exception:  # noqa: BLE001 — never fail request on resolver error
            _logger.warning("GovernAI: resolver error during request setup", exc_info=True)

        environ["governai.tenant_id"] = tenant_id
        environ["governai.user_id"] = user_id

        # ------------------------------------------------------------------
        # 5. Intercept start_response to inject correlation ID header
        # ------------------------------------------------------------------
        def _start_response_wrapper(
            status: str,
            response_headers: list[tuple[str, str]],
            exc_info: object = None,
        ) -> Callable:
            # Inject correlation ID header only when not already present
            header_names = {name.lower() for name, _ in response_headers}
            if "x-correlation-id" not in header_names:
                response_headers.append(("X-Correlation-Id", correlation_id))
            if exc_info is not None:
                return start_response(status, response_headers, exc_info)
            return start_response(status, response_headers)

        # ------------------------------------------------------------------
        # 6. Call wrapped application
        # ------------------------------------------------------------------
        try:
            return self._app(environ, _start_response_wrapper)
        finally:
            _wsgi_environ.reset(token)


class GovernAIWSGIApp:
    """Convenience wrapper that applies ``GovernAIMiddleware`` to a WSGI app.

    Identical to constructing ``GovernAIMiddleware(wsgi_app, config)``
    directly; provided for readability when sub-classing or composing apps.

    Usage::

        from governai.wsgi import GovernAIConfig, GovernAIWSGIApp

        config = GovernAIConfig(application_name="MyApp")
        app = GovernAIWSGIApp(wsgi_app=my_wsgi_app, config=config)
    """

    def __init__(self, wsgi_app: Callable, config: GovernAIConfig) -> None:
        self._middleware = GovernAIMiddleware(wsgi_app=wsgi_app, config=config)

    def __call__(
        self,
        environ: dict[str, object],
        start_response: Callable,
    ) -> Iterable[bytes]:
        return self._middleware(environ, start_response)
