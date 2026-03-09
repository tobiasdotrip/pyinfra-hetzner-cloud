"""Hetzner Cloud facts.

These functions query the Hetzner Cloud API and return structured data
about the current state of resources. They are used internally by operations
to make idempotency decisions, and can also be called directly in deploy scripts.

Usage in deploy code::

    from pyinfra_hetzner_cloud.facts.hcloud import get_servers, get_ssh_keys

    servers = get_servers()
    keys = get_ssh_keys()
"""

from __future__ import annotations

from typing import Any

from pyinfra_hetzner_cloud.client import get_client


def get_ssh_keys(
    *,
    name: str | None = None,
    label_selector: str | None = None,
) -> list[dict[str, Any]]:
    """Return all SSH keys, optionally filtered by name or label selector.

    Each key is returned as::

        {
            "id": int,
            "name": str,
            "public_key": str,
            "fingerprint": str,
            "labels": dict[str, str],
        }
    """
    client = get_client()
    keys = client.ssh_keys.get_all(name=name, label_selector=label_selector)
    return [
        {
            "id": k.data_model.id,
            "name": k.data_model.name,
            "public_key": k.data_model.public_key,
            "fingerprint": k.data_model.fingerprint,
            "labels": k.data_model.labels or {},
        }
        for k in keys
    ]


def get_ssh_key_by_name(name: str) -> dict[str, Any] | None:
    """Return a single SSH key by exact name, or None if not found."""
    client = get_client()
    key = client.ssh_keys.get_by_name(name)
    if key is None:
        return None
    return {
        "id": key.data_model.id,
        "name": key.data_model.name,
        "public_key": key.data_model.public_key,
        "fingerprint": key.data_model.fingerprint,
        "labels": key.data_model.labels or {},
    }


def _serialize_server(srv: Any) -> dict[str, Any]:
    """Normalize a BoundServer into a plain dict."""
    dm = srv.data_model
    public_net = dm.public_net
    return {
        "id": dm.id,
        "name": dm.name,
        "status": dm.status,
        "server_type": dm.server_type.name if dm.server_type else None,
        "image": dm.image.name if dm.image else None,
        "location": (
            dm.datacenter.location.name
            if dm.datacenter and dm.datacenter.location
            else None
        ),
        "datacenter": dm.datacenter.name if dm.datacenter else None,
        "ipv4": public_net.ipv4.ip if public_net and public_net.ipv4 else None,
        "ipv6": public_net.ipv6.ip if public_net and public_net.ipv6 else None,
        "labels": dm.labels or {},
    }


def get_servers(
    *,
    name: str | None = None,
    label_selector: str | None = None,
    status: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return all servers, optionally filtered."""
    client = get_client()
    servers = client.servers.get_all(
        name=name,
        label_selector=label_selector,
        status=status,
    )
    return [_serialize_server(s) for s in servers]


def get_server_by_name(name: str) -> dict[str, Any] | None:
    """Return a single server by exact name, or None."""
    client = get_client()
    srv = client.servers.get_by_name(name)
    if srv is None:
        return None
    return _serialize_server(srv)


def _serialize_rule(rule: Any) -> dict[str, Any]:
    """Normalize a firewall rule."""
    return {
        "direction": rule.direction,
        "protocol": rule.protocol,
        "port": rule.port,
        "source_ips": list(rule.source_ips) if rule.source_ips else [],
        "destination_ips": list(rule.destination_ips) if rule.destination_ips else [],
        "description": getattr(rule, "description", None),
    }


def _serialize_firewall(fw: Any) -> dict[str, Any]:
    """Normalize a BoundFirewall into a plain dict."""
    dm = fw.data_model
    applied = []
    for a in (dm.applied_to or []):
        entry: dict[str, Any] = {"type": a.type}
        if a.type == "server" and a.server:
            entry["server_id"] = a.server.id
        elif a.type == "label_selector" and a.label_selector:
            entry["selector"] = a.label_selector.selector
        applied.append(entry)

    return {
        "id": dm.id,
        "name": dm.name,
        "labels": dm.labels or {},
        "rules": [_serialize_rule(r) for r in (dm.rules or [])],
        "applied_to": applied,
    }


def get_firewalls(
    *,
    name: str | None = None,
    label_selector: str | None = None,
) -> list[dict[str, Any]]:
    """Return all firewalls, optionally filtered."""
    client = get_client()
    firewalls = client.firewalls.get_all(name=name, label_selector=label_selector)
    return [_serialize_firewall(fw) for fw in firewalls]


def get_firewall_by_name(name: str) -> dict[str, Any] | None:
    """Return a single firewall by exact name, or None."""
    client = get_client()
    fw = client.firewalls.get_by_name(name)
    if fw is None:
        return None
    return _serialize_firewall(fw)
