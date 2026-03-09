"""Tests for firewall operations noop behaviour."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pyinfra_hetzner_cloud.operations.firewalls import firewall

MODULE = "pyinfra_hetzner_cloud.operations.firewalls"


# ---------------------------------------------------------------------------
# firewall operation
# ---------------------------------------------------------------------------


class TestFirewallNoopWhenAlreadyMatches:
    """host.noop() is called when the firewall already matches desired state."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_rules_and_labels_match(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "rules": [
                {
                    "direction": "in",
                    "protocol": "tcp",
                    "port": "22",
                    "source_ips": ["0.0.0.0/0"],
                },
            ],
            "labels": {"env": "prod"},
        }

        commands = list(firewall._inner(
            firewall_name="default-fw",
            rules=[
                {
                    "direction": "in",
                    "protocol": "tcp",
                    "port": "22",
                    "source_ips": ["0.0.0.0/0"],
                },
            ],
            labels={"env": "prod"},
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Firewall 'default-fw' already matches desired state"
        )

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_no_rules_or_labels_specified(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        """When rules=None and labels=None, no drift check triggers, so noop."""
        mock_get.return_value = {
            "id": 1,
            "rules": [{
                "direction": "in", "protocol": "tcp",
                "port": "22", "source_ips": ["0.0.0.0/0"],
            }],
            "labels": {"env": "prod"},
        }

        commands = list(firewall._inner(
            firewall_name="default-fw",
            rules=None,
            labels=None,
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Firewall 'default-fw' already matches desired state"
        )

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_rules_match_labels_not_specified(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "rules": [{"direction": "in", "protocol": "icmp", "source_ips": ["0.0.0.0/0"]}],
            "labels": {},
        }

        commands = list(firewall._inner(
            firewall_name="my-fw",
            rules=[{"direction": "in", "protocol": "icmp", "source_ips": ["0.0.0.0/0"]}],
            labels=None,
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Firewall 'my-fw' already matches desired state"
        )


class TestFirewallNoopWhenAlreadyAbsent:
    """host.noop() is called when firewall absent and present=False."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_noop_when_firewall_absent_and_present_false(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = None

        commands = list(firewall._inner(
            firewall_name="old-fw",
            present=False,
        ))

        assert commands == []
        mock_host.noop.assert_called_once_with(
            "Firewall 'old-fw' already absent"
        )


class TestFirewallNoNoopOnChanges:
    """host.noop() must NOT be called when the operation yields commands."""

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_no_noop_when_creating(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = None

        commands = list(firewall._inner(
            firewall_name="new-fw",
            rules=[{
                "direction": "in", "protocol": "tcp",
                "port": "22", "source_ips": ["0.0.0.0/0"],
            }],
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_no_noop_when_deleting(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {"id": 1, "rules": [], "labels": {}}

        commands = list(firewall._inner(
            firewall_name="old-fw",
            present=False,
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_no_noop_when_updating_rules(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "rules": [{
                "direction": "in", "protocol": "tcp",
                "port": "22", "source_ips": ["0.0.0.0/0"],
            }],
            "labels": {},
        }

        commands = list(firewall._inner(
            firewall_name="my-fw",
            rules=[{
                "direction": "in", "protocol": "tcp",
                "port": "443", "source_ips": ["0.0.0.0/0"],
            }],
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_no_noop_when_updating_labels(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "rules": [],
            "labels": {"env": "staging"},
        }

        commands = list(firewall._inner(
            firewall_name="my-fw",
            rules=None,
            labels={"env": "prod"},
        ))

        assert len(commands) == 1
        mock_host.noop.assert_not_called()

    @patch(f"{MODULE}.host")
    @patch(f"{MODULE}.get_firewall_by_name")
    def test_no_noop_when_updating_both_rules_and_labels(
        self,
        mock_get: MagicMock,
        mock_host: MagicMock,
    ) -> None:
        mock_get.return_value = {
            "id": 1,
            "rules": [{
                "direction": "in", "protocol": "tcp",
                "port": "22", "source_ips": ["0.0.0.0/0"],
            }],
            "labels": {"env": "staging"},
        }

        commands = list(firewall._inner(
            firewall_name="my-fw",
            rules=[{
                "direction": "in", "protocol": "tcp",
                "port": "443", "source_ips": ["0.0.0.0/0"],
            }],
            labels={"env": "prod"},
        ))

        assert len(commands) == 2
        mock_host.noop.assert_not_called()


