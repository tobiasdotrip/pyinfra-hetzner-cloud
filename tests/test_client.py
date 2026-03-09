"""Tests for pyinfra_hetzner_cloud.client."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from pyinfra_hetzner_cloud.client import HCloudConfigError, get_client, reset_client


class TestGetClient:
    def setup_method(self) -> None:
        reset_client()

    def teardown_method(self) -> None:
        reset_client()

    def test_raises_without_token(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            # Ensure HCLOUD_TOKEN is not set
            os.environ.pop("HCLOUD_TOKEN", None)
            with pytest.raises(HCloudConfigError, match="No Hetzner Cloud API token"):
                get_client()

    @patch("hcloud.Client")
    def test_creates_client_from_env(self, mock_hcloud_cls: object) -> None:
        with patch.dict(os.environ, {"HCLOUD_TOKEN": "test-token-123"}):
            client = get_client()
            assert client is not None

    @patch("hcloud.Client")
    def test_creates_client_from_explicit_token(self, mock_hcloud_cls: object) -> None:
        client = get_client(token="explicit-token")
        assert client is not None

    @patch("hcloud.Client")
    def test_returns_same_instance(self, mock_hcloud_cls: object) -> None:
        with patch.dict(os.environ, {"HCLOUD_TOKEN": "test-token"}):
            c1 = get_client()
            c2 = get_client()
            assert c1 is c2

    @patch("hcloud.Client")
    def test_reset_clears_cache(self, mock_hcloud_cls: object) -> None:
        from unittest.mock import MagicMock

        mock_hcloud_cls.side_effect = [MagicMock(name="client-1"), MagicMock(name="client-2")]
        with patch.dict(os.environ, {"HCLOUD_TOKEN": "test-token"}):
            c1 = get_client()
            reset_client()
            c2 = get_client()
            # After reset, a new instance should be created
            assert c1 is not c2
