"""Shared Hetzner Cloud API client utilities.

Provides a thread-safe, lazy-initialized hcloud Client instance configured
through HCLOUD_TOKEN and HCLOUD_TIMEOUT.
"""

from __future__ import annotations

import os
import threading
from math import isfinite
from typing import TYPE_CHECKING

from pyinfra_hetzner_cloud import __version__

if TYPE_CHECKING:
    from hcloud import Client

_lock = threading.Lock()
_client: Client | None = None
DEFAULT_TIMEOUT = 30.0


class HCloudConfigError(Exception):
    """Raised when the Hetzner Cloud client cannot be configured."""


def _resolve_timeout(timeout: float | None) -> float:
    if timeout is None:
        value = os.environ.get("HCLOUD_TIMEOUT")
        if value is None:
            return DEFAULT_TIMEOUT
        try:
            timeout = float(value)
        except ValueError as exc:
            raise HCloudConfigError("HCLOUD_TIMEOUT must be a positive number.") from exc

    if not isfinite(timeout) or timeout <= 0:
        raise HCloudConfigError("HCLOUD_TIMEOUT must be a positive number.")
    return timeout


def get_client(token: str | None = None, timeout: float | None = None) -> Client:
    """Return a shared hcloud Client instance.

    The client is created once and reused. Token resolution order:
    1. Explicit ``token`` argument
    2. ``HCLOUD_TOKEN`` environment variable

    The per-request network timeout defaults to 30 seconds and can be set with
    the explicit ``timeout`` argument or ``HCLOUD_TIMEOUT`` environment variable.

    Raises:
        HCloudConfigError: If no token can be resolved or the timeout is invalid.
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

        _client = HCloudClient(
            token=resolved_token,
            application_name="pyinfra-hetzner-cloud",
            application_version=__version__,
            timeout=_resolve_timeout(timeout),
        )
        return _client


def reset_client() -> None:
    """Reset the cached client (useful for testing)."""
    global _client  # noqa: PLW0603
    with _lock:
        _client = None
