"""Tests for minimum-permission validation responses."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/validation.py"
)
SPEC = importlib.util.spec_from_file_location("validation", MODULE_PATH)
validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation)


class ValidationTests(unittest.TestCase):
    def test_empty_pve_nodes_fail_validation(self):
        self.assertFalse(validation.minimum_endpoint_has_resources("nodes", []))

    def test_empty_pbs_datastores_fail_validation(self):
        self.assertFalse(
            validation.minimum_endpoint_has_resources("admin/datastore", [])
        )

    def test_visible_pbs_datastore_passes_validation(self):
        self.assertTrue(
            validation.minimum_endpoint_has_resources(
                "admin/datastore", [{"store": "backup"}]
            )
        )


if __name__ == "__main__":
    unittest.main()
