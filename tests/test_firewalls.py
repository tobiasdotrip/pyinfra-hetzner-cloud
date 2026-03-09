"""Tests for firewall operations internal helpers."""

from __future__ import annotations

from pyinfra_hetzner_cloud.operations.firewalls import _normalize_rule, _rules_match


class TestNormalizeRule:
    def test_basic_normalization(self) -> None:
        rule = {
            "direction": "in",
            "protocol": "tcp",
            "port": "22",
            "source_ips": ["::/0", "0.0.0.0/0"],
            "description": "SSH",
        }
        result = _normalize_rule(rule)
        assert result["source_ips"] == ["0.0.0.0/0", "::/0"]  # sorted
        assert result["destination_ips"] == []  # default

    def test_missing_optional_fields(self) -> None:
        rule = {"direction": "in", "protocol": "icmp"}
        result = _normalize_rule(rule)
        assert result["port"] is None
        assert result["description"] is None


class TestRulesMatch:
    def test_identical_rules(self) -> None:
        rules = [
            {"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0"]},
        ]
        assert _rules_match(rules, rules) is True

    def test_different_order_same_rules(self) -> None:
        a = [
            {"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0"]},
            {"direction": "in", "protocol": "icmp", "source_ips": ["0.0.0.0/0"]},
        ]
        b = [
            {"direction": "in", "protocol": "icmp", "source_ips": ["0.0.0.0/0"]},
            {"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0"]},
        ]
        assert _rules_match(a, b) is True

    def test_different_rules(self) -> None:
        a = [{"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0"]}]
        b = [{"direction": "in", "protocol": "tcp", "port": "443", "source_ips": ["0.0.0.0/0"]}]
        assert _rules_match(a, b) is False

    def test_different_count(self) -> None:
        a = [{"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0"]}]
        b: list[dict] = []
        assert _rules_match(a, b) is False

    def test_source_ips_order_irrelevant(self) -> None:
        a = [{
            "direction": "in", "protocol": "tcp",
            "port": "22", "source_ips": ["::/0", "0.0.0.0/0"],
        }]
        b = [{
            "direction": "in", "protocol": "tcp",
            "port": "22", "source_ips": ["0.0.0.0/0", "::/0"],
        }]
        assert _rules_match(a, b) is True
