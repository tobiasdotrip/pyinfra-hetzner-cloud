"""Tests for firewall_apply planning phase.

Verifies idempotency checks and correct FunctionCommand generation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pyinfra.api.exceptions import OperationError

from pyinfra_hetzner_cloud.operations.firewalls import (
    _apply_firewall_to_resources,
    _build_firewall_resources,
    _remove_firewall_from_resources,
    firewall_apply,
)

MODULE = "pyinfra_hetzner_cloud.operations.firewalls"


@patch(f"{MODULE}.get_client")
def test_build_firewall_resources_supports_servers_and_selectors(
    mock_get_client: MagicMock,
) -> None:
    client = MagicMock()
    server = MagicMock()
    server.id = 42
    client.servers.get_by_name.return_value = server
    mock_get_client.return_value = client

    resources = _build_firewall_resources(["web-1"], ["env=prod"])

    assert [resource.to_payload() for resource in resources] == [
        {"type": "server", "server": {"id": 42}},
        {"type": "label_selector", "label_selector": {"selector": "env=prod"}},
    ]


@patch(f"{MODULE}.get_client")
def test_build_firewall_resources_rejects_unknown_server(
    mock_get_client: MagicMock,
) -> None:
    client = MagicMock()
    client.servers.get_by_name.return_value = None
    mock_get_client.return_value = client

    with pytest.raises(OperationError, match="Server 'missing' not found"):
        _build_firewall_resources(["missing"], [])


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
        assert cmd.function is _apply_firewall_to_resources
        assert cmd.args == ["my-fw", ["srv-a"], []]

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
        assert cmd.function is _remove_firewall_from_resources
        assert cmd.args == ["my-fw", ["srv-a"], []]


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
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_label_selector_already_applied(
        self,
        mock_get_fw: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = {
            "id": 10,
            "applied_to": [
                {"type": "label_selector", "selector": "env=prod"},
            ],
        }

        commands = list(
            firewall_apply._inner(
                firewall_name="my-fw",
                label_selectors=["env=prod"],
            )
        )

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Firewall 'my-fw' already applied to labels:env=prod"
        )

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_yields_when_label_selector_is_missing(
        self,
        mock_get_fw: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get_fw.return_value = {"id": 10, "applied_to": []}

        commands = list(
            firewall_apply._inner(
                firewall_name="my-fw",
                label_selectors=["env=prod"],
            )
        )

        assert len(commands) == 1
        assert commands[0].function is _apply_firewall_to_resources
        assert commands[0].args == ["my-fw", [], ["env=prod"]]
        mock_host.noop.assert_not_called()

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
        assert commands[0].function is _apply_firewall_to_resources

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
        assert commands[0].function is _remove_firewall_from_resources


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

    @patch(f"{MODULE}.host")
    def test_empty_server_names_and_selector_names_yields_nothing(
        self,
        mock_host: MagicMock,
    ) -> None:
        commands = list(
            firewall_apply._inner(
                firewall_name="my-fw",
                server_names=[],
                label_selectors=[],
            )
        )

        assert commands == []
