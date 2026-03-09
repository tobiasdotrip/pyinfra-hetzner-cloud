"""Hetzner Cloud Server operations.

Idempotent management of cloud servers in Hetzner Cloud.

Usage::

    from pyinfra_hetzner_cloud.operations.servers import server

    server(
        name="Ensure web server exists",
        server_name="web-1",
        server_type="cx22",
        image="debian-12",
        location="fsn1",
        ssh_keys=["deploy-key"],
        firewalls=["default-fw"],
        labels={"role": "web", "env": "prod"},
    )

    server(
        name="Delete staging server",
        server_name="staging-1",
        present=False,
    )
"""

from __future__ import annotations

from pyinfra import host
from pyinfra.api import FunctionCommand, operation

from pyinfra_hetzner_cloud.client import get_client
from pyinfra_hetzner_cloud.facts.hcloud import get_server_by_name


def _create_server(
    server_name: str,
    server_type: str,
    image: str,
    location: str | None,
    ssh_keys: list[str] | None,
    firewalls: list[str] | None,
    user_data: str | None,
    labels: dict[str, str] | None,
    start_after_create: bool,
) -> None:
    """Create a server via the Hetzner Cloud API."""
    from hcloud.images import Image
    from hcloud.locations import Location
    from hcloud.server_types import ServerType

    client = get_client()

    resolved_ssh_keys = None
    if ssh_keys:
        resolved_ssh_keys = []
        for key_ref in ssh_keys:
            found = client.ssh_keys.get_by_name(key_ref)
            if found is None:
                raise ValueError(f"SSH key '{key_ref}' not found in Hetzner Cloud.")
            resolved_ssh_keys.append(found)

    resolved_firewalls = None
    if firewalls:
        resolved_firewalls = []
        for fw_ref in firewalls:
            found = client.firewalls.get_by_name(fw_ref)
            if found is None:
                raise ValueError(f"Firewall '{fw_ref}' not found in Hetzner Cloud.")
            resolved_firewalls.append(found)

    response = client.servers.create(
        name=server_name,
        server_type=ServerType(name=server_type),
        image=Image(name=image),
        location=Location(name=location) if location else None,
        ssh_keys=resolved_ssh_keys,
        firewalls=resolved_firewalls,
        user_data=user_data,
        labels=labels,
        start_after_create=start_after_create,
    )
    response.action.wait_until_finished()


def _delete_server(server_id: int) -> None:
    """Delete a server via the Hetzner Cloud API."""
    from hcloud.servers import Server

    client = get_client()
    action = client.servers.delete(server=Server(id=server_id))
    if action is not None:
        action.wait_until_finished()


def _update_server_labels(server_id: int, server_name: str, labels: dict[str, str]) -> None:
    """Update server labels."""
    from hcloud.servers import Server

    client = get_client()
    client.servers.update(server=Server(id=server_id), name=server_name, labels=labels)


def _power_on_server(server_id: int) -> None:
    """Power on a server."""
    from hcloud.servers import Server

    client = get_client()
    action = client.servers.power_on(server=Server(id=server_id))
    action.wait_until_finished()


def _power_off_server(server_id: int) -> None:
    """Power off a server (graceful shutdown)."""
    from hcloud.servers import Server

    client = get_client()
    action = client.servers.shutdown(server=Server(id=server_id))
    action.wait_until_finished()


@operation()
def server(
    server_name: str,
    server_type: str = "cx22",
    image: str = "debian-12",
    location: str | None = "fsn1",
    ssh_keys: list[str] | None = None,
    firewalls: list[str] | None = None,
    user_data: str | None = None,
    labels: dict[str, str] | None = None,
    running: bool = True,
    start_after_create: bool = True,
    present: bool = True,
) -> None:
    """Ensure a Hetzner Cloud server exists with the desired state.

    + server_name: Name of the server (must be unique per project, valid hostname).
    + server_type: Server type (e.g. ``cx22``, ``cx32``, ``cax11``).
    + image: Image to use for creation (e.g. ``debian-12``, ``ubuntu-24.04``).
    + location: Location (e.g. ``fsn1``, ``nbg1``, ``hel1``, ``ash``, ``hil``).
    + ssh_keys: List of SSH key names to inject at creation time.
    + firewalls: List of firewall names to apply at creation time.
    + user_data: Cloud-init user data string (max 32 KiB).
    + labels: Labels (key-value pairs) for the server.
    + running: Whether the server should be running (only applied if server exists).
    + start_after_create: Start the server after creation (default True).
    + present: Whether the server should exist. Set to ``False`` to delete.

    Idempotency:
        - Server does not exist + ``present=True`` → create.
        - Server exists + ``present=False`` → delete.
        - Server exists + different labels → update labels.
        - Server exists + wrong power state → power on/off.
        - Server type / image changes are **not** applied (would require rebuild).

    Note:
        ``ssh_keys`` and ``firewalls`` are only used at creation time.
        Changing them after the server exists has no effect (use the firewall
        operations to manage firewall rules independently).
    """
    existing = get_server_by_name(server_name)

    if present:
        if existing is None:
            yield FunctionCommand(
                _create_server,
                [
                    server_name,
                    server_type,
                    image,
                    location,
                    ssh_keys,
                    firewalls,
                    user_data,
                    labels,
                    start_after_create,
                ],
                {},
            )
            return

        changed = False
        current_labels = existing.get("labels", {})
        if labels is not None and current_labels != labels:
            yield FunctionCommand(
                _update_server_labels,
                [existing["id"], server_name, labels],
                {},
            )
            changed = True

        status = existing.get("status")
        if running and status != "running":
            yield FunctionCommand(_power_on_server, [existing["id"]], {})
            changed = True
        elif not running and status == "running":
            yield FunctionCommand(_power_off_server, [existing["id"]], {})
            changed = True

        if not changed:
            host.noop(f"Server '{server_name}' already matches desired state")

    else:
        if existing is not None:
            yield FunctionCommand(_delete_server, [existing["id"]], {})
        else:
            host.noop(f"Server '{server_name}' already absent")
