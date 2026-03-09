"""Hetzner Cloud Firewall operations.

Idempotent management of firewalls and their rules in Hetzner Cloud.

Usage::

    from pyinfra_hetzner_cloud.operations.firewalls import firewall, firewall_apply

    firewall(
        name="Ensure default firewall exists",
        firewall_name="default-fw",
        rules=[
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "22",
                "source_ips": ["0.0.0.0/0", "::/0"],
                "description": "SSH",
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "443",
                "source_ips": ["0.0.0.0/0", "::/0"],
                "description": "HTTPS",
            },
            {
                "direction": "in",
                "protocol": "icmp",
                "source_ips": ["0.0.0.0/0", "::/0"],
                "description": "Ping",
            },
        ],
    )

    firewall_apply(
        name="Apply firewall to web server",
        firewall_name="default-fw",
        server_names=["web-1"],
    )
"""

from __future__ import annotations

from typing import Any

from pyinfra import host
from pyinfra.api import FunctionCommand, operation

from pyinfra_hetzner_cloud.client import get_client
from pyinfra_hetzner_cloud.facts.hcloud import get_firewall_by_name, get_server_by_name


def _normalize_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Normalize a rule dict for consistent comparison."""
    return {
        "direction": rule["direction"],
        "protocol": rule["protocol"],
        "port": rule.get("port"),
        "source_ips": sorted(rule.get("source_ips", [])),
        "destination_ips": sorted(rule.get("destination_ips", [])),
        "description": rule.get("description"),
    }


def _rules_match(desired: list[dict[str, Any]], current: list[dict[str, Any]]) -> bool:
    """Check if two sets of rules are equivalent (order-independent)."""
    if len(desired) != len(current):
        return False

    def _sort_key(r: dict[str, Any]) -> tuple[str, str, str, str]:
        return (r["direction"], r["protocol"], r.get("port", ""), r.get("description", ""))

    norm_desired = sorted([_normalize_rule(r) for r in desired], key=_sort_key)
    norm_current = sorted([_normalize_rule(r) for r in current], key=_sort_key)
    return norm_desired == norm_current


def _build_api_rules(rules: list[dict[str, Any]]) -> list[Any]:
    """Convert rule dicts to hcloud FirewallRule objects."""
    from hcloud.firewalls import FirewallRule

    api_rules = []
    for r in rules:
        api_rules.append(
            FirewallRule(
                direction=r["direction"],
                protocol=r["protocol"],
                port=r.get("port"),
                source_ips=r.get("source_ips", []),
                destination_ips=r.get("destination_ips", []),
                description=r.get("description"),
            )
        )
    return api_rules


def _create_firewall(
    firewall_name: str,
    rules: list[dict[str, Any]],
    labels: dict[str, str] | None,
) -> None:
    """Create a firewall via the Hetzner Cloud API."""
    client = get_client()
    client.firewalls.create(
        name=firewall_name,
        rules=_build_api_rules(rules),
        labels=labels,
    )


def _delete_firewall(firewall_id: int) -> None:
    """Delete a firewall via the Hetzner Cloud API."""
    from hcloud.firewalls import Firewall

    client = get_client()
    client.firewalls.delete(firewall=Firewall(id=firewall_id))


def _update_firewall_labels(
    firewall_id: int,
    firewall_name: str,
    labels: dict[str, str],
) -> None:
    """Update firewall labels."""
    from hcloud.firewalls import Firewall

    client = get_client()
    client.firewalls.update(
        firewall=Firewall(id=firewall_id),
        name=firewall_name,
        labels=labels,
    )


def _set_firewall_rules(firewall_id: int, rules: list[dict[str, Any]]) -> None:
    """Replace all rules on a firewall."""
    from hcloud.firewalls import Firewall

    client = get_client()
    actions = client.firewalls.set_rules(
        firewall=Firewall(id=firewall_id),
        rules=_build_api_rules(rules),
    )
    for action in actions:
        action.wait_until_finished()


def _resolve_firewall_by_name(firewall_name: str) -> int:
    """Resolve a firewall name to its ID at execution time."""
    client = get_client()
    fw = client.firewalls.get_by_name(firewall_name)
    if fw is None:
        raise ValueError(f"Firewall '{firewall_name}' not found in Hetzner Cloud.")
    return fw.data_model.id


def _apply_firewall_to_server_names(firewall_name: str, server_names: list[str]) -> None:
    """Apply a firewall to servers, resolving all names to IDs at execution time."""
    from hcloud._exceptions import APIException
    from hcloud.firewalls import Firewall, FirewallResource

    fw_id = _resolve_firewall_by_name(firewall_name)
    client = get_client()
    resources = []
    for sname in server_names:
        srv = client.servers.get_by_name(sname)
        if srv is None:
            raise ValueError(f"Server '{sname}' not found in Hetzner Cloud.")
        resources.append(FirewallResource(type="server", server=srv))
    try:
        actions = client.firewalls.apply_to_resources(
            firewall=Firewall(id=fw_id),
            resources=resources,
        )
        for action in actions:
            action.wait_until_finished()
    except APIException as exc:
        if "firewall_already_applied" not in str(exc):
            raise


def _remove_firewall_from_server_names(firewall_name: str, server_names: list[str]) -> None:
    """Remove a firewall from servers, resolving all names to IDs at execution time."""
    from hcloud._exceptions import APIException
    from hcloud.firewalls import Firewall, FirewallResource

    fw_id = _resolve_firewall_by_name(firewall_name)
    client = get_client()
    resources = []
    for sname in server_names:
        srv = client.servers.get_by_name(sname)
        if srv is None:
            raise ValueError(f"Server '{sname}' not found in Hetzner Cloud.")
        resources.append(FirewallResource(type="server", server=srv))
    try:
        actions = client.firewalls.remove_from_resources(
            firewall=Firewall(id=fw_id),
            resources=resources,
        )
        for action in actions:
            action.wait_until_finished()
    except APIException as exc:
        if "firewall_already_removed" not in str(exc):
            raise


@operation()
def firewall(
    firewall_name: str,
    rules: list[dict[str, Any]] | None = None,
    labels: dict[str, str] | None = None,
    present: bool = True,
) -> None:
    """Ensure a Hetzner Cloud firewall exists with the desired rules.

    + firewall_name: Name of the firewall (unique per project).
    + rules: List of rule dicts. Each rule has:
        - ``direction``: ``"in"`` or ``"out"``
        - ``protocol``: ``"tcp"``, ``"udp"``, ``"icmp"``, ``"esp"``, ``"gre"``
        - ``port``: Port or port range (e.g. ``"22"``, ``"1024-5000"``). Required
          for ``tcp`` and ``udp``.
        - ``source_ips``: List of CIDR blocks (for ``direction="in"``).
        - ``destination_ips``: List of CIDR blocks (for ``direction="out"``).
        - ``description``: Optional description.
    + labels: Labels for the firewall.
    + present: Whether the firewall should exist.

    Idempotency:
        - Firewall missing + ``present=True`` → create with rules.
        - Firewall exists + rules differ → replace all rules.
        - Firewall exists + labels differ → update labels.
        - Firewall exists + ``present=False`` → delete.
    """
    existing = get_firewall_by_name(firewall_name)

    if present:
        if existing is None:
            yield FunctionCommand(
                _create_firewall,
                [firewall_name, rules or [], labels],
                {},
            )
            return

        changed = False

        if rules is not None and not _rules_match(rules, existing.get("rules", [])):
            changed = True
            yield FunctionCommand(
                _set_firewall_rules,
                [existing["id"], rules],
                {},
            )

        current_labels = existing.get("labels", {})
        if labels is not None and current_labels != labels:
            changed = True
            yield FunctionCommand(
                _update_firewall_labels,
                [existing["id"], firewall_name, labels],
                {},
            )

        if not changed:
            host.noop(f"Firewall '{firewall_name}' already matches desired state")

    else:
        if existing is not None:
            yield FunctionCommand(
                _delete_firewall,
                [existing["id"]],
                {},
            )
        else:
            host.noop(f"Firewall '{firewall_name}' already absent")


@operation()
def firewall_apply(
    firewall_name: str,
    server_names: list[str] | None = None,
    present: bool = True,
) -> None:
    """Apply (or remove) a firewall to/from servers.

    + firewall_name: Name of the firewall.
    + server_names: List of server names to apply the firewall to.
    + present: If ``True``, apply the firewall. If ``False``, remove it.

    Idempotency:
        - Only adds/removes servers that are not already in the desired state.
    """
    if not server_names:
        return

    # When the firewall doesn't exist yet (e.g. --dry after a preceding create),
    # skip the check — the callback handles idempotency at execution time.
    existing_fw = get_firewall_by_name(firewall_name)

    if existing_fw is not None:
        applied_server_ids = {
            r["server_id"]
            for r in existing_fw.get("applied_to", [])
            if r.get("type") == "server"
        }
        desired_ids = set()
        for sname in server_names:
            srv = get_server_by_name(sname)
            if srv is not None:
                desired_ids.add(srv["id"])

        if present and desired_ids and desired_ids.issubset(applied_server_ids):
            host.noop(
                f"Firewall '{firewall_name}' already applied to"
                f" {', '.join(sorted(server_names))}",
            )
            return
        if not present and not desired_ids.intersection(applied_server_ids):
            host.noop(
                f"Firewall '{firewall_name}' already removed from"
                f" {', '.join(sorted(server_names))}",
            )
            return

    if present:
        yield FunctionCommand(
            _apply_firewall_to_server_names,
            [firewall_name, list(server_names)],
            {},
        )
    else:
        yield FunctionCommand(
            _remove_firewall_from_server_names,
            [firewall_name, list(server_names)],
            {},
        )
