"""Tests for firewall_apply planning phase.

Verifies idempotency checks and correct FunctionCommand generation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pyinfra_hetzner_cloud.operations.firewalls import (
    _apply_firewall_to_server_names,
    _remove_firewall_from_server_names,
    firewall_apply,
)

MODULE = "pyinfra_hetzner_cloud.operations.firewalls"


class TestFirewallApplyYieldsCorrectCallbacks:
    """The yielded FunctionCommand references the correct callback function."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_server_by_name")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_present_true_yields_apply_callback(
        self,
        mock_get_fw: MagicMock,
        mock_get_srv: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = {"id": 10, "applied_to": []}
        mock_get_srv.return_value = {"id": 100, "name": "srv-a"}

        commands = list(firewall_apply._inner(
            firewall_name="my-fw",
            server_names=["srv-a"],
            present=True,
        ))

        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.function is _apply_firewall_to_server_names
        assert cmd.args == ["my-fw", ["srv-a"]]

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_server_by_name")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_present_false_yields_remove_callback(
        self,
        mock_get_fw: MagicMock,
        mock_get_srv: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = {
            "id": 10,
            "applied_to": [{"type": "server", "server_id": 100}],
        }
        mock_get_srv.return_value = {"id": 100, "name": "srv-a"}

        commands = list(firewall_apply._inner(
            firewall_name="my-fw",
            server_names=["srv-a"],
            present=False,
        ))

        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.function is _remove_firewall_from_server_names
        assert cmd.args == ["my-fw", ["srv-a"]]


class TestFirewallApplyIdempotency:
    """Noop when firewall is already in desired state."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_server_by_name")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_already_applied(
        self,
        mock_get_fw: MagicMock,
        mock_get_srv: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = {
            "id": 10,
            "applied_to": [{"type": "server", "server_id": 100}],
        }
        mock_get_srv.return_value = {"id": 100, "name": "srv-a"}

        commands = list(firewall_apply._inner(
            firewall_name="my-fw",
            server_names=["srv-a"],
            present=True,
        ))

        assert commands == []
        mock_host.noop.assert_called_once()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_server_by_name")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_already_removed(
        self,
        mock_get_fw: MagicMock,
        mock_get_srv: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = {
            "id": 10,
            "applied_to": [],
        }
        mock_get_srv.return_value = {"id": 100, "name": "srv-a"}

        commands = list(firewall_apply._inner(
            firewall_name="my-fw",
            server_names=["srv-a"],
            present=False,
        ))

        assert commands == []
        mock_host.noop.assert_called_once()


class TestFirewallApplyDryRunFallback:
    """When firewall doesn't exist yet, yield FunctionCommand anyway."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_yields_apply_when_firewall_missing(
        self,
        mock_get_fw: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = None

        commands = list(firewall_apply._inner(
            firewall_name="new-fw",
            server_names=["srv-a"],
            present=True,
        ))

        assert len(commands) == 1
        assert commands[0].function is _apply_firewall_to_server_names

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_yields_remove_when_firewall_missing(
        self,
        mock_get_fw: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = None

        commands = list(firewall_apply._inner(
            firewall_name="new-fw",
            server_names=["srv-a"],
            present=False,
        ))

        assert len(commands) == 1
        assert commands[0].function is _remove_firewall_from_server_names


class TestFirewallApplyEdgeCases:
    """Edge cases: empty server list, None server list."""

    @patch(f"{MODULE}.host")
    def test_empty_server_names_yields_nothing(
        self,
        mock_host: MagicMock,
    ) -> None:
        commands = list(firewall_apply._inner(
            firewall_name="my-fw",
            server_names=[],
        ))

        assert commands == []

    @patch(f"{MODULE}.host")
    def test_none_server_names_yields_nothing(
        self,
        mock_host: MagicMock,
    ) -> None:
        commands = list(firewall_apply._inner(
            firewall_name="my-fw",
            server_names=None,
        ))

        assert commands == []
