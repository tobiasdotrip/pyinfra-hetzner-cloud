"""Validate pyinfra plugin metadata against the installed pyinfra schema."""

from pathlib import Path

from pyinfra.api.metadata import parse_plugins


def test_pyinfra_metadata_is_valid() -> None:
    metadata = Path("pyinfra-metadata.toml").read_text()

    plugins = parse_plugins(metadata)

    assert {plugin.name for plugin in plugins} == {
        "hcloud",
        "hcloud_firewalls",
        "hcloud_servers",
        "hcloud_ssh_keys",
    }
