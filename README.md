# pyinfra-hetzner-cloud

![Python](https://img.shields.io/badge/Python-≥3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![pyinfra](https://img.shields.io/badge/pyinfra-≥3.10-blue?style=flat-square)
![hcloud](https://img.shields.io/badge/hcloud-≥2.23-D50C2D?style=flat-square&logo=hetzner&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

Hetzner Cloud operations and facts for [pyinfra](https://pyinfra.com). Manage SSH keys,
servers, server protection, and firewalls declaratively.

## Compatibility

- Python 3.10+
- pyinfra 3.10+
- hcloud 2.23+

## Install

```bash
pip install pyinfra-hetzner-cloud
```

## Usage

```bash
export HCLOUD_TOKEN="your-api-token"
# Optional: per-request network timeout in seconds (default: 30)
export HCLOUD_TIMEOUT="30"
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
    delete_protection=True,
    rebuild_protection=True,
)

firewall_apply(
    name="Apply firewall",
    firewall_name="default-fw",
    label_selectors=["role=web"],
)
```

All operations are idempotent — they check current state before making changes. Firewall
assignments accept explicit server names, label selectors, or both.

## License

MIT
