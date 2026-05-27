"""GovernAI core options.

Provides the ``GovernAIOptions`` configuration dataclass used to control
runtime behaviour across all GovernAI core components.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class GovernAIOptions:
    """Configuration options for the GovernAI core runtime.

    All boolean flags default to secure-by-default values:
    hashing is enabled, and exporter failures are silently swallowed.
    Raw prompt and response text are **never** stored in ``GovernAIEvent``
    regardless of configuration — only their SHA-256 hashes are retained.

    Attributes:
        application_name: Name of the application using GovernAI.
        environment_name: Runtime environment (e.g., Production, Development).
        enable_prompt_hashing: Hash prompts with SHA-256 before storing.
        enable_response_hashing: Hash responses with SHA-256 before storing.
        allow_raw_prompt_capture: Reserved for future use. Currently has no
            effect — raw prompt text is never stored in ``GovernAIEvent``
            regardless of this setting. Default ``False``.
        allow_raw_response_capture: Reserved for future use. Currently has no
            effect — raw response text is never stored in ``GovernAIEvent``
            regardless of this setting. Default ``False``.
        fail_on_exporter_error: Re-raise exceptions from exporters.
            When ``False`` (default), exporter failures are logged and ignored.
        in_memory_exporter_capacity: Maximum number of events held by the
            ``InMemoryExporter`` before older events are discarded.
        file_exporter_path: File path for ``FileExporter`` output.
            ``None`` disables file exporting.
        max_prompt_scan_len: Maximum number of characters of the prompt
            passed to policy scanners. Prompts longer than this are
            silently truncated **before scanning only** — the full prompt
            is still hashed. Defaults to 65 536 characters. Set to 0 to
            disable the limit (not recommended for production).
    """

    application_name: str = ""
    environment_name: str = ""
    enable_prompt_hashing: bool = True
    enable_response_hashing: bool = True
    allow_raw_prompt_capture: bool = False   # Reserved — currently has no effect
    allow_raw_response_capture: bool = False  # Reserved — currently has no effect
    fail_on_exporter_error: bool = False
    in_memory_exporter_capacity: int = 1000
    file_exporter_path: str | None = None
    max_prompt_scan_len: int = 65_536
