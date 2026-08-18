"""Tests for global service target selection."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/service_targets.py"
)
SPEC = importlib.util.spec_from_file_location("service_targets", MODULE_PATH)
service_targets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(service_targets)


def _entry(server_type, node, cluster_nodes=()):
    return {
        "server_type": server_type,
        "node": node,
        "client": object(),
        "coordinator": SimpleNamespace(data={"cluster_nodes": list(cluster_nodes)}),
    }


class ServiceTargetTests(unittest.TestCase):
    def test_selects_entry_by_cluster_node(self):
        first = _entry("PVE", "pve-a", ("pve-a", "pve-b"))
        second = _entry("PVE", "other", ("other",))

        selected = service_targets.resolve_pve_service_target(
            {"first": first, "second": second}, node="pve-b"
        )

        self.assertIs(selected, first)

    def test_rejects_ambiguous_node(self):
        entries = {
            "first": _entry("PVE", "pve"),
            "second": _entry("PVE", "pve"),
        }

        with self.assertRaisesRegex(ValueError, "Multiple PVE"):
            service_targets.resolve_pve_service_target(entries, node="pve")

    def test_entry_id_disambiguates(self):
        first = _entry("PVE", "pve")
        second = _entry("PVE", "pve")

        selected = service_targets.resolve_pve_service_target(
            {"first": first, "second": second}, node="pve", entry_id="second"
        )

        self.assertIs(selected, second)

    def test_does_not_select_pbs(self):
        with self.assertRaisesRegex(ValueError, "No loaded PVE"):
            service_targets.resolve_pve_service_target(
                {"pbs": _entry("PBS", "backup")}, node="backup"
            )
