"""Example deploy: provision a VPS with SSH key, firewall, and server.

Run with:
    HCLOUD_TOKEN=your-token pyinfra @local examples/deploy.py
"""

from pyinfra_hetzner_cloud.operations.firewalls import firewall, firewall_apply
from pyinfra_hetzner_cloud.operations.servers import server
from pyinfra_hetzner_cloud.operations.ssh_keys import ssh_key

ssh_key(
    name="Ensure deploy SSH key",
    key_name="my-deploy-key",
    public_key="ssh-ed25519 AAAA... user@example.com",
    labels={"managed-by": "pyinfra"},
)

firewall(
    name="Ensure default firewall",
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
            "port": "80",
            "source_ips": ["0.0.0.0/0", "::/0"],
            "description": "HTTP",
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
    labels={"managed-by": "pyinfra"},
)

server(
    name="Ensure VPS my-server",
    server_name="my-server",
    server_type="cx23",
    image="debian-12",
    location="hel1",
    ssh_keys=["my-deploy-key"],
    firewalls=["default-fw"],
    labels={
        "managed-by": "pyinfra",
        "role": "vps",
    },
)

firewall_apply(
    name="Apply default-fw to VPS",
    firewall_name="default-fw",
    server_names=["my-server"],
)
