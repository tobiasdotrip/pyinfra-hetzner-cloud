# pyinfra-hetzner-cloud

![Python](https://img.shields.io/badge/Python-≥3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![pyinfra](https://img.shields.io/badge/pyinfra-≥3.0-blue?style=flat-square)
![hcloud](https://img.shields.io/badge/hcloud-≥2.0-D50C2D?style=flat-square&logo=hetzner&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

Hetzner Cloud operations and facts for [pyinfra](https://pyinfra.com). Manage SSH keys, servers, and firewalls declaratively.

## Install

```bash
pip install pyinfra-hetzner-cloud
```

## Usage

```bash
export HCLOUD_TOKEN="your-api-token"
```

```python
from pyinfra_hetzner_cloud.operations.ssh_keys import ssh_key
from pyinfra_hetzner_cloud.operations.servers import server
from pyinfra_hetzner_cloud.operations.firewalls import firewall, firewall_apply

ssh_key(
    name="Ensure deploy key",
    key_name="deploy-key",
    public_key="ssh-ed25519 AAAA...",
)

firewall(
    name="Ensure default firewall",
    firewall_name="default-fw",
    rules=[
        {"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0", "::/0"]},
        {"direction": "in", "protocol": "tcp", "port": "443", "source_ips": ["0.0.0.0/0", "::/0"]},
    ],
)

server(
    name="Ensure web server",
    server_name="web-1",
    server_type="cx22",
    image="debian-12",
    location="fsn1",
    ssh_keys=["deploy-key"],
    firewalls=["default-fw"],
)

firewall_apply(
    name="Apply firewall",
    firewall_name="default-fw",
    server_names=["web-1"],
)
```

All operations are idempotent — they check current state before making changes.

## License

MIT
