"""GovernAI WSGI integration package.

This package contains WSGI middleware, configuration, tenant resolvers,
and user resolvers for Python web framework integration.

Exported symbols:
    GovernAIConfig: Configuration dataclass for GovernAIMiddleware.
    GovernAIMiddleware: PEP 3333 WSGI middleware.
    GovernAIWSGIApp: Convenience WSGI wrapper.
    HeaderTenantResolver: Resolves tenant ID from X-Tenant-Id header.
    HeaderUserResolver: Resolves user ID from X-User-Id header or environ.
"""

from governai.wsgi.config import GovernAIConfig
from governai.wsgi.middleware import GovernAIMiddleware, GovernAIWSGIApp
from governai.wsgi.resolvers import HeaderTenantResolver, HeaderUserResolver

__all__ = [
    "GovernAIConfig",
    "GovernAIMiddleware",
    "GovernAIWSGIApp",
    "HeaderTenantResolver",
    "HeaderUserResolver",
]

