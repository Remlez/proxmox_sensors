"""Tests for derived guest utilization metrics."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/guest_metrics.py"
)
SPEC = importlib.util.spec_from_file_location("guest_metrics", MODULE_PATH)
guest_metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guest_metrics)


class GuestMetricsTests(unittest.TestCase):
    def test_calculates_percentage(self):
        self.assertEqual(25.0, guest_metrics.calculate_usage_percentage(256, 1024))

    def test_accepts_numeric_strings(self):
        self.assertEqual(50.0, guest_metrics.calculate_usage_percentage("5", "10"))

    def test_rejects_missing_or_zero_total(self):
        self.assertIsNone(guest_metrics.calculate_usage_percentage(1, 0))
        self.assertIsNone(guest_metrics.calculate_usage_percentage(None, 10))

    def test_rejects_negative_values(self):
        self.assertIsNone(guest_metrics.calculate_usage_percentage(-1, 10))


if __name__ == "__main__":
    unittest.main()
