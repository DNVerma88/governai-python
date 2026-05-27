"""GovernAI core package.

This package contains the GovernAI runtime, event tracking, prompt/response
hashing, local exporters, and local policy evaluation.

Exported symbols:
    GovernAIOptions: Runtime configuration.
    GovernAIRuntime: Public tracking facade.
    GovernAITracker: Core tracking engine (dependency-injectable).
    SystemClock: Real-time UTC clock.
    PromptHasher: SHA-256 prompt hasher.
    ResponseHasher: SHA-256 response hasher.
    NoOpPolicyEvaluator: Pass-through policy evaluator (always ALLOW).
    NoOpExporter: Discards all events.
    CompositeExporter: Fans out to multiple exporters.
    InMemoryExporter: Bounded in-memory event buffer.
    ConsoleExporter: Writes events as JSON to stdout.
    FileExporter: Writes events as JSON Lines to a file.
"""

from governai.core.clock import SystemClock
from governai.core.exporters import (
    CompositeExporter,
    ConsoleExporter,
    FileExporter,
    InMemoryExporter,
    NoOpExporter,
)
from governai.core.hashing import PromptHasher, ResponseHasher
from governai.core.options import GovernAIOptions
from governai.core.policy import NoOpPolicyEvaluator
from governai.core.runtime import GovernAIRuntime
from governai.core.tracker import GovernAITracker

__all__ = [
    "GovernAIOptions",
    "GovernAIRuntime",
    "GovernAITracker",
    "SystemClock",
    "PromptHasher",
    "ResponseHasher",
    "NoOpPolicyEvaluator",
    "NoOpExporter",
    "CompositeExporter",
    "InMemoryExporter",
    "ConsoleExporter",
    "FileExporter",
]

