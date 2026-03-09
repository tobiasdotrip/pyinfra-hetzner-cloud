"""Teardown: delete all resources created by deploy.py.

Run with:
    HCLOUD_TOKEN=your-token pyinfra @local examples/teardown.py
"""

from pyinfra_hetzner_cloud.operations.firewalls import firewall
from pyinfra_hetzner_cloud.operations.servers import server
from pyinfra_hetzner_cloud.operations.ssh_keys import ssh_key

server(
    name="Delete VPS tobias-vps",
    server_name="tobias-vps",
    present=False,
)

firewall(
    name="Delete default firewall",
    firewall_name="default-fw",
    present=False,
)

ssh_key(
    name="Delete deploy SSH key",
    key_name="tobias-deploy",
    present=False,
)
