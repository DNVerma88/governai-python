"""GovernAI WSGI tenant and user resolvers.

Provides:
- ``HeaderTenantResolver``: resolves tenant ID from the ``X-Tenant-Id``
  request header (``HTTP_X_TENANT_ID`` in WSGI environ).
- ``HeaderUserResolver``: resolves user ID from the ``X-User-Id`` request
  header or the ``governai.user_id`` environ key.

Both resolvers read request context from the ``_wsgi_environ`` context variable,
which is populated by ``GovernAIMiddleware`` before each request.
"""

from __future__ import annotations

import contextvars

# ContextVar that the middleware sets to the current WSGI environ dict before
# each request so that resolvers can access it without being explicitly passed
# a reference to the environ.
_wsgi_environ: contextvars.ContextVar[dict[str, object]] = contextvars.ContextVar(
    "governai_wsgi_environ"
)


class HeaderTenantResolver:
    """Resolves the tenant ID from the ``X-Tenant-Id`` HTTP request header.

    Reads the WSGI environ from the ``_wsgi_environ`` context variable, which
    must be populated by ``GovernAIMiddleware`` prior to calling this resolver.

    If the header is absent, returns an empty string.

    .. warning::
        **Security:** The ``X-Tenant-Id`` header is client-controlled. This
        resolver must only be used when the header is set exclusively by a
        trusted upstream component (API gateway, authentication middleware,
        or mTLS layer). Never accept this header directly from untrusted
        clients without verifying it against an authenticated identity (e.g.
        a JWT claim). Failure to do so allows any caller to spoof any tenant
        ID, corrupting the audit trail and potentially breaching multi-tenant
        isolation.
    """

    async def resolve_tenant_id_async(self, context: object) -> str:
        """Resolve tenant ID from the ``X-Tenant-Id`` request header.

        Args:
            context: The ``GovernAIContext`` for the current operation.
                Not used directly; the WSGI environ is read from the
                ``_wsgi_environ`` context variable instead.

        Returns:
            The tenant ID string extracted from the header, or an empty
            string if the header is not present.
        """
        environ = _wsgi_environ.get({})
        return str(environ.get("HTTP_X_TENANT_ID", ""))


class HeaderUserResolver:
    """Resolves the user ID from the WSGI request environment.

    Resolution order:

    1. ``governai.user_id`` — an application-set key in the WSGI environ
       (highest priority, allows the application to override).
    2. ``HTTP_X_USER_ID`` — the ``X-User-Id`` HTTP request header.
    3. Empty string — when neither is present.

    Reads the WSGI environ from the ``_wsgi_environ`` context variable, which
    must be populated by ``GovernAIMiddleware`` prior to calling this resolver.

    .. warning::
        **Security:** The ``X-User-Id`` header is client-controlled. Prefer
        reading the authenticated user identity from ``governai.user_id``,
        which should be set by upstream authentication middleware from a
        verified JWT claim or session token. Accepting the raw ``X-User-Id``
        header from untrusted clients allows any caller to impersonate any
        user, making the governance audit trail untrustworthy.
    """

    async def resolve_user_id_async(self, context: object) -> str:
        """Resolve user ID from the WSGI request environment.

        Args:
            context: The ``GovernAIContext`` for the current operation.
                Not used directly; the WSGI environ is read from the
                ``_wsgi_environ`` context variable instead.

        Returns:
            The user ID string, or an empty string if none is found.
        """
        environ = _wsgi_environ.get({})
        # Prefer application-set key over header
        app_user = environ.get("governai.user_id", "")
        if app_user:
            return str(app_user)
        return str(environ.get("HTTP_X_USER_ID", ""))
