"""Tests for pyinfra_hetzner_cloud.facts.hcloud."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pyinfra_hetzner_cloud.facts.hcloud import (
    get_firewall_by_name,
    get_firewalls,
    get_server_by_name,
    get_servers,
    get_ssh_key_by_name,
    get_ssh_keys,
)
from tests.conftest import (
    make_mock_firewall,
    make_mock_rule,
    make_mock_server,
    make_mock_ssh_key,
)


@patch("pyinfra_hetzner_cloud.facts.hcloud.get_client")
class TestSSHKeyFacts:
    def test_get_ssh_keys_returns_all(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.ssh_keys.get_all.return_value = [
            make_mock_ssh_key(id=1, name="key-a"),
            make_mock_ssh_key(id=2, name="key-b"),
        ]
        mock_get_client.return_value = client

        result = get_ssh_keys()

        assert len(result) == 2
        assert result[0]["name"] == "key-a"
        assert result[1]["name"] == "key-b"
        client.ssh_keys.get_all.assert_called_once_with(name=None, label_selector=None)

    def test_get_ssh_keys_with_filter(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.ssh_keys.get_all.return_value = [make_mock_ssh_key(name="deploy")]
        mock_get_client.return_value = client

        result = get_ssh_keys(name="deploy")

        assert len(result) == 1
        client.ssh_keys.get_all.assert_called_once_with(name="deploy", label_selector=None)

    def test_get_ssh_key_by_name_found(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.ssh_keys.get_by_name.return_value = make_mock_ssh_key(
            id=42, name="my-key", public_key="ssh-ed25519 test"
        )
        mock_get_client.return_value = client

        result = get_ssh_key_by_name("my-key")

        assert result is not None
        assert result["id"] == 42
        assert result["public_key"] == "ssh-ed25519 test"

    def test_get_ssh_key_by_name_not_found(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.ssh_keys.get_by_name.return_value = None
        mock_get_client.return_value = client

        result = get_ssh_key_by_name("nonexistent")

        assert result is None


@patch("pyinfra_hetzner_cloud.facts.hcloud.get_client")
class TestServerFacts:
    def test_get_servers_returns_all(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.servers.get_all.return_value = [
            make_mock_server(id=1, name="web-1"),
            make_mock_server(id=2, name="web-2", status="off"),
        ]
        mock_get_client.return_value = client

        result = get_servers()

        assert len(result) == 2
        assert result[0]["name"] == "web-1"
        assert result[0]["status"] == "running"
        assert result[1]["status"] == "off"

    def test_get_server_by_name_found(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.servers.get_by_name.return_value = make_mock_server(
            id=10, name="db-1", ipv4="10.0.0.1"
        )
        mock_get_client.return_value = client

        result = get_server_by_name("db-1")

        assert result is not None
        assert result["id"] == 10
        assert result["ipv4"] == "10.0.0.1"

    def test_get_server_by_name_not_found(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.servers.get_by_name.return_value = None
        mock_get_client.return_value = client

        assert get_server_by_name("ghost") is None


@patch("pyinfra_hetzner_cloud.facts.hcloud.get_client")
class TestFirewallFacts:
    def test_get_firewalls_returns_all(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        rules = [make_mock_rule(port="22"), make_mock_rule(protocol="icmp", port=None)]
        client.firewalls.get_all.return_value = [
            make_mock_firewall(id=1, name="fw-1", rules=rules),
        ]
        mock_get_client.return_value = client

        result = get_firewalls()

        assert len(result) == 1
        assert result[0]["name"] == "fw-1"
        assert len(result[0]["rules"]) == 2
        assert result[0]["rules"][0]["port"] == "22"
        assert result[0]["rules"][1]["protocol"] == "icmp"

    def test_get_firewall_by_name_not_found(self, mock_get_client: MagicMock) -> None:
        client = MagicMock()
        client.firewalls.get_by_name.return_value = None
        mock_get_client.return_value = client

        assert get_firewall_by_name("nope") is None

    def test_firewall_applied_to_serialization(self, mock_get_client: MagicMock) -> None:
        applied = MagicMock()
        applied.type = "server"
        applied.server.id = 99
        applied.label_selector = None

        client = MagicMock()
        client.firewalls.get_by_name.return_value = make_mock_firewall(
            id=5, name="app-fw", applied_to=[applied]
        )
        mock_get_client.return_value = client

        result = get_firewall_by_name("app-fw")
        assert result is not None
        assert result["applied_to"] == [{"type": "server", "server_id": 99}]
