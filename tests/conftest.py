"""Shared test fixtures and mock helpers."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock


def make_mock_ssh_key(
    id: int = 1,
    name: str = "test-key",
    public_key: str = "ssh-ed25519 AAAA...",
    fingerprint: str = "aa:bb:cc:dd",
    labels: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock BoundSSHKey."""
    key = MagicMock()
    key.data_model.id = id
    key.data_model.name = name
    key.data_model.public_key = public_key
    key.data_model.fingerprint = fingerprint
    key.data_model.labels = labels or {}
    return key


def make_mock_server(
    id: int = 1,
    name: str = "test-server",
    status: str = "running",
    server_type: str = "cx22",
    image: str = "debian-12",
    location: str = "fsn1",
    datacenter: str = "fsn1-dc14",
    ipv4: str = "1.2.3.4",
    ipv6: str = "2001:db8::1",
    labels: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock BoundServer."""
    srv = MagicMock()
    dm = srv.data_model
    dm.id = id
    dm.name = name
    dm.status = status
    dm.server_type.name = server_type
    dm.image.name = image
    dm.datacenter.name = datacenter
    dm.datacenter.location.name = location
    dm.public_net.ipv4.ip = ipv4
    dm.public_net.ipv6.ip = ipv6
    dm.labels = labels or {}
    return srv


def make_mock_firewall(
    id: int = 1,
    name: str = "test-fw",
    labels: dict[str, str] | None = None,
    rules: list[Any] | None = None,
    applied_to: list[Any] | None = None,
) -> MagicMock:
    """Create a mock BoundFirewall."""
    fw = MagicMock()
    dm = fw.data_model
    dm.id = id
    dm.name = name
    dm.labels = labels or {}
    dm.rules = rules or []
    dm.applied_to = applied_to or []
    return fw


def make_mock_rule(
    direction: str = "in",
    protocol: str = "tcp",
    port: str | None = "22",
    source_ips: list[str] | None = None,
    destination_ips: list[str] | None = None,
    description: str | None = None,
) -> MagicMock:
    """Create a mock FirewallRule."""
    rule = MagicMock()
    rule.direction = direction
    rule.protocol = protocol
    rule.port = port
    rule.source_ips = source_ips or ["0.0.0.0/0", "::/0"]
    rule.destination_ips = destination_ips or []
    rule.description = description
    return rule
