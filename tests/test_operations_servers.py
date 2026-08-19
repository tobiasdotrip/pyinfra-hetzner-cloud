"""Tests for server operations — host.noop() feedback."""

from __future__ import annotations

from collections.abc import Iterable
from unittest.mock import MagicMock, patch

from pyinfra.api.command import FunctionCommand

from pyinfra_hetzner_cloud.operations.servers import (
    _change_server_protection,
    _set_server_power_by_name,
    server,
)


def _collect(gen: Iterable[FunctionCommand]) -> list[FunctionCommand]:
    """Consume a generator and return the list of yielded values."""
    return list(gen)


@patch("pyinfra_hetzner_cloud.operations.servers.get_client")
def test_change_server_protection_executes_and_waits(mock_get_client: MagicMock) -> None:
    client = MagicMock()
    srv = MagicMock()
    client.servers.get_by_name.return_value = srv
    mock_get_client.return_value = client

    _change_server_protection("web-1", True, False)

    client.servers.change_protection.assert_called_once_with(
        srv,
        delete=True,
        rebuild=False,
    )
    client.servers.change_protection.return_value.wait_until_finished.assert_called_once()


@patch("pyinfra_hetzner_cloud.operations.servers.get_client")
def test_set_server_power_by_name_executes_and_waits(mock_get_client: MagicMock) -> None:
    client = MagicMock()
    srv = MagicMock()
    client.servers.get_by_name.return_value = srv
    mock_get_client.return_value = client

    _set_server_power_by_name("web-1", False)

    client.servers.shutdown.assert_called_once_with(srv)
    client.servers.shutdown.return_value.wait_until_finished.assert_called_once()


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

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_create_reconciles_requested_power_state(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        mock_get_server.return_value = None

        commands = _collect(
            server._inner(
                server_name="new-1",
                running=False,
                start_after_create=True,
            )
        )

        assert len(commands) == 2
        assert commands[1].function is _set_server_power_by_name
        assert commands[1].args == ["new-1", False]
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_existing_server_updates_protection(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "running",
            "labels": {},
            "protection": {"delete": False, "rebuild": False},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                delete_protection=True,
                rebuild_protection=True,
            )
        )

        assert len(commands) == 1
        assert commands[0].function is _change_server_protection
        assert commands[0].args == ["web-1", True, True]
        mock_host.noop.assert_not_called()

    @patch("pyinfra_hetzner_cloud.operations.servers.host")
    @patch("pyinfra_hetzner_cloud.operations.servers.get_server_by_name")
    def test_delete_can_explicitly_disable_protection_first(
        self, mock_get_server: MagicMock, mock_host: MagicMock
    ) -> None:
        mock_get_server.return_value = {
            "id": 1,
            "name": "web-1",
            "status": "running",
            "labels": {},
            "protection": {"delete": True, "rebuild": True},
        }

        commands = _collect(
            server._inner(
                server_name="web-1",
                delete_protection=False,
                present=False,
            )
        )

        assert len(commands) == 2
        assert commands[0].function is _change_server_protection
        assert commands[0].args == ["web-1", False, None]
        mock_host.noop.assert_not_called()
