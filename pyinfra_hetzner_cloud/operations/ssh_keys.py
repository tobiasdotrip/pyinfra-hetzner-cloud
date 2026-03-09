"""Hetzner Cloud SSH Key operations.

Idempotent management of SSH keys in Hetzner Cloud.

Usage::

    from pyinfra_hetzner_cloud.operations.ssh_keys import ssh_key

    ssh_key(
        name="Ensure deploy key exists",
        key_name="deploy-key",
        public_key="ssh-ed25519 AAAA...",
        labels={"env": "production"},
    )

    ssh_key(
        name="Remove old key",
        key_name="legacy-key",
        present=False,
    )
"""

from __future__ import annotations

from pyinfra import host
from pyinfra.api import FunctionCommand, operation

from pyinfra_hetzner_cloud.client import get_client
from pyinfra_hetzner_cloud.facts.hcloud import get_ssh_key_by_name


def _create_ssh_key(
    key_name: str,
    public_key: str,
    labels: dict[str, str] | None,
) -> None:
    """Create an SSH key via the Hetzner Cloud API."""
    client = get_client()
    client.ssh_keys.create(
        name=key_name,
        public_key=public_key,
        labels=labels,
    )


def _update_ssh_key(
    key_id: int,
    key_name: str,
    labels: dict[str, str] | None,
) -> None:
    """Update an SSH key's labels via the Hetzner Cloud API."""
    from hcloud.ssh_keys import SSHKey

    client = get_client()
    client.ssh_keys.update(
        ssh_key=SSHKey(id=key_id),
        name=key_name,
        labels=labels,
    )


def _delete_ssh_key(key_id: int) -> None:
    """Delete an SSH key via the Hetzner Cloud API."""
    from hcloud.ssh_keys import SSHKey

    client = get_client()
    client.ssh_keys.delete(ssh_key=SSHKey(id=key_id))


@operation()
def ssh_key(
    key_name: str,
    public_key: str | None = None,
    labels: dict[str, str] | None = None,
    present: bool = True,
) -> None:
    """Ensure a Hetzner Cloud SSH key exists (or is absent).

    + key_name: Name of the SSH key in Hetzner Cloud (must be unique per project).
    + public_key: The SSH public key string (required when ``present=True`` and key
      does not yet exist).
    + labels: Labels to apply to the key. If the key exists with different labels,
      they will be updated.
    + present: Whether the key should exist. Set to ``False`` to delete.

    Idempotency:
        - If the key exists with the same public_key and labels → no change.
        - If the key exists with different labels → update labels.
        - If the key exists but ``present=False`` → delete.
        - If the key does not exist and ``present=True`` → create.

    Note:
        Hetzner Cloud does not allow updating the public_key of an existing SSH key.
        If the public_key has changed, the operation will raise an error suggesting
        you delete and recreate the key.
    """
    existing = get_ssh_key_by_name(key_name)

    if present:
        if public_key is None and existing is None:
            raise ValueError(
                f"public_key is required to create SSH key '{key_name}' "
                f"(it does not exist yet)."
            )

        if existing is None:
            yield FunctionCommand(
                _create_ssh_key,
                [key_name, public_key, labels],
                {},
            )
            return

        if public_key and existing["public_key"].strip() != public_key.strip():
            raise ValueError(
                f"SSH key '{key_name}' exists with a different public_key. "
                f"Hetzner Cloud does not support updating public keys in-place. "
                f"Delete the key first (present=False), then recreate it."
            )

        current_labels = existing.get("labels", {})
        if labels is not None and current_labels != labels:
            yield FunctionCommand(
                _update_ssh_key,
                [existing["id"], key_name, labels],
                {},
            )
            return

        host.noop(f"SSH key '{key_name}' already matches desired state")

    else:
        if existing is not None:
            yield FunctionCommand(
                _delete_ssh_key,
                [existing["id"]],
                {},
            )
        else:
            host.noop(f"SSH key '{key_name}' already absent")
