"""Tests for node metrics recovered from cluster resources."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/node_metrics.py"
)
SPEC = importlib.util.spec_from_file_location("node_metrics_fallback_test", MODULE_PATH)
node_metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(node_metrics)


class NodeResourceFallbackTests(unittest.TestCase):
    def test_builds_core_usage_structures_when_status_request_failed(self):
        resources = [
            {
                "type": "node",
                "node": "atlas",
                "status": "online",
                "cpu": 0.25,
                "mem": 6 * 1024**3,
                "maxmem": 8 * 1024**3,
                "disk": 40 * 1024**3,
                "maxdisk": 100 * 1024**3,
                "uptime": 3600,
            }
        ]

        result = node_metrics.merge_node_status_with_cluster_resource(
            {}, resources, "atlas"
        )

        self.assertEqual(0.25, result["cpu"])
        self.assertEqual("online", result["status"])
        self.assertEqual(3600, result["uptime"])
        self.assertEqual(
            {"used": 6 * 1024**3, "total": 8 * 1024**3}, result["memory"]
        )
        self.assertEqual(
            {"used": 40 * 1024**3, "total": 100 * 1024**3},
            result["rootfs"],
        )

    def test_detailed_status_values_win_over_cluster_fallback(self):
        status = {
            "cpu": 0.1,
            "memory": {"used": 2, "total": 10, "free": 8},
            "rootfs": {"used": 3, "total": 10},
        }
        resources = [
            {
                "type": "node",
                "node": "atlas",
                "cpu": 0.9,
                "mem": 8,
                "maxmem": 10,
                "disk": 9,
                "maxdisk": 10,
            }
        ]

        result = node_metrics.merge_node_status_with_cluster_resource(
            status, resources, "atlas"
        )

        self.assertEqual(0.1, result["cpu"])
        self.assertEqual({"used": 2, "total": 10, "free": 8}, result["memory"])
        self.assertEqual({"used": 3, "total": 10}, result["rootfs"])

    def test_does_not_use_another_nodes_resource(self):
        result = node_metrics.merge_node_status_with_cluster_resource(
            {}, [{"type": "node", "node": "pvesec", "cpu": 0.5}], "atlas"
        )

        self.assertEqual({}, result)


if __name__ == "__main__":
    unittest.main()
