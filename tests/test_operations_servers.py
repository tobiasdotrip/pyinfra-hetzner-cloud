"""Tests for server operations — host.noop() feedback."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pyinfra.api import FunctionCommand

from pyinfra_hetzner_cloud.operations.servers import server


def _collect(gen):
    """Consume a generator and return the list of yielded values."""
    return list(gen)


class TestServerNoop:
    """Verify host.noop() is called when state already matches."""

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_already_matches(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, running, labels match -> noop, no commands."""
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "running",
            "labels": {"env": "prod"},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                labels={"env": "prod"},
                running=True,
                present=True,
            )
        )

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Server 'web-1' already matches desired state"
        )

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_matches_no_labels(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, running, labels=None (don't care) -> noop."""
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "running",
            "labels": {"whatever": "value"},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                labels=None,
                running=True,
                present=True,
            )
        )

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Server 'web-1' already matches desired state"
        )

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_absent_server_already_absent(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server does not exist, present=False -> noop."""
        mock_get_server.return_value = None

        commands = _collect(
            server._inner(
                server_name="gone-1",
                present=False,
            )
        )

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Server 'gone-1' already absent"
        )

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_missing_yields_create(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server missing, present=True -> create command, no noop."""
        mock_get_server.return_value = None

        commands = _collect(
            server._inner(
                server_name="new-1",
                server_type="cx22",
                image="debian-12",
                location="fsn1",
                present=True,
            )
        )

        assert len(commands) == 1
        assert isinstance(commands[0], FunctionCommand)
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_labels_differ_no_noop(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, labels differ -> update command, no noop."""
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "running",
            "labels": {"env": "staging"},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                labels={"env": "prod"},
                running=True,
                present=True,
            )
        )

        assert len(commands) == 1
        assert isinstance(commands[0], FunctionCommand)
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_wrong_power_state_no_noop(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, stopped but should be running -> power on, no noop."""
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "off",
            "labels": {"env": "prod"},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                labels={"env": "prod"},
                running=True,
                present=True,
            )
        )

        assert len(commands) == 1
        assert isinstance(commands[0], FunctionCommand)
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_labels_and_power_differ_no_noop(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, labels AND power state both wrong -> 2 commands, no noop."""
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "off",
            "labels": {"env": "staging"},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                labels={"env": "prod"},
                running=True,
                present=True,
            )
        )

        assert len(commands) == 2
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_absent_server_exists_yields_delete(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, present=False -> delete command, no noop."""
        mock_get_server.return_value = {
            "id": 42,
            "name": "old-1",
            "status": "running",
            "labels": {},
        }

        commands = _collect(
            server._inner(
                server_name="old-1",
                present=False,
            )
        )

        assert len(commands) == 1
        assert isinstance(commands[0], FunctionCommand)
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_present_server_stopped_matches(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        """Server exists, stopped, running=False, labels match -> noop."""
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "off",
            "labels": {},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                labels={},
                running=False,
                present=True,
            )
        )

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Server 'web-1' already matches desired state"
        )
