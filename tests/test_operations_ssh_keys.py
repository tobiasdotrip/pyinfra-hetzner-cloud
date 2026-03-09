"""Tests for ssh_key operation noop behaviour."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pyinfra_hetzner_cloud.operations.ssh_keys import ssh_key

MODULE = "pyinfra_hetzner_cloud.operations.ssh_keys"


class TestSshKeyNoopWhenAlreadyMatches:
    """host.noop() is called when the key already matches desired state."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_noop_when_key_matches_public_key_and_labels(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "public_key": "ssh-ed25519 AAAA...",
            "labels": {"env": "prod"},
        }

        commands = list(ssh_key._inner(
            key_name="deploy-key",
            public_key="ssh-ed25519 AAAA...",
            labels={"env": "prod"},
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "SSH key 'deploy-key' already matches desired state"
        )

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_noop_when_key_matches_no_labels_specified(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        """When labels=None (not specified), no label drift check, so noop."""
        mock_get.return_value = {
            "id": 1,
            "public_key": "ssh-ed25519 AAAA...",
            "labels": {"env": "prod"},
        }

        commands = list(ssh_key._inner(
            key_name="deploy-key",
            public_key="ssh-ed25519 AAAA...",
            labels=None,
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "SSH key 'deploy-key' already matches desired state"
        )

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_noop_when_key_matches_no_public_key_specified(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        """When public_key=None and key exists with matching labels, noop."""
        mock_get.return_value = {
            "id": 1,
            "public_key": "ssh-ed25519 AAAA...",
            "labels": {"env": "prod"},
        }

        commands = list(ssh_key._inner(
            key_name="deploy-key",
            public_key=None,
            labels={"env": "prod"},
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "SSH key 'deploy-key' already matches desired state"
        )


class TestSshKeyNoopWhenAlreadyAbsent:
    """host.noop() is called when key is already absent and present=False."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_noop_when_key_absent_and_present_false(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = None

        commands = list(ssh_key._inner(
            key_name="old-key",
            present=False,
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "SSH key 'old-key' already absent"
        )


class TestSshKeyNoNoopOnChanges:
    """host.noop() must NOT be called when the operation yields commands."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_no_noop_when_creating(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = None

        commands = list(ssh_key._inner(
            key_name="new-key",
            public_key="ssh-ed25519 AAAA...",
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_no_noop_when_deleting(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {"id": 1, "public_key": "ssh-ed25519 AAAA...", "labels": {}}

        commands = list(ssh_key._inner(
            key_name="old-key",
            present=False,
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_ssh_key_by_name")
    def test_no_noop_when_updating_labels(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "public_key": "ssh-ed25519 AAAA...",
            "labels": {"env": "staging"},
        }

        commands = list(ssh_key._inner(
            key_name="deploy-key",
            public_key="ssh-ed25519 AAAA...",
            labels={"env": "prod"},
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()
