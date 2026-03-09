"""Shared Hetzner Cloud API client utilities.

Provides a thread-safe, lazy-initialized hcloud Client instance
sourced from the HCLOUD_TOKEN environment variable.
"""

from __future__ import annotations

import os
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hcloud import Client

_lock = threading.Lock()
_client: Client | None = None


class HCloudConfigError(Exception):
    """Raised when the Hetzner Cloud client cannot be configured."""


def get_client(token: str | None = None) -> Client:
    """Return a shared hcloud Client instance.

    The client is created once and reused. Token resolution order:
    1. Explicit ``token`` argument
    2. ``HCLOUD_TOKEN`` environment variable

    Raises:
        HCloudConfigError: If no token can be resolved.
    """
    global _client  # noqa: PLW0603

    if _client is not None:
        return _client

    with _lock:
        # Double-checked locking
        if _client is not None:
            return _client

        resolved_token = token or os.environ.get("HCLOUD_TOKEN")
        if not resolved_token:
            raise HCloudConfigError(
                "No Hetzner Cloud API token found. "
                "Set the HCLOUD_TOKEN environment variable or pass token= explicitly."
            )

        from hcloud import Client as HCloudClient

        _client = HCloudClient(token=resolved_token)
        return _client


def reset_client() -> None:
    """Reset the cached client (useful for testing)."""
    global _client  # noqa: PLW0603
    with _lock:
        _client = None
