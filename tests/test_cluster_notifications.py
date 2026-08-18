"""Regression tests for cluster notification normalization."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/cluster_notifications.py"
)
SPEC = importlib.util.spec_from_file_location("cluster_notifications", MODULE_PATH)
cluster_notifications = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cluster_notifications)


class ClusterNotificationTests(unittest.TestCase):
    def test_missing_configuration_is_reported_explicitly(self):
        data = cluster_notifications.build_cluster_notifications_data({}, [])
        self.assertFalse(data["notifications_configured"])
        self.assertEqual("not_configured", data["package_updates"])

    def test_configured_target_is_resolved(self):
        data = cluster_notifications.build_cluster_notifications_data(
            {"notify": "package-updates=always,target-package-updates=gotify1"},
            [{"name": "gotify1", "type": "gotify", "server": "alerts"}],
        )
        self.assertTrue(data["notifications_configured"])
        self.assertEqual("alerts", data["target_package_updates_server"])


if __name__ == "__main__":
    unittest.main()
