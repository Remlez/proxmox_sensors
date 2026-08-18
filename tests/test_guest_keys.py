"""Regression tests for explicit empty guest selections."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/guest_keys.py"
)
SPEC = importlib.util.spec_from_file_location("guest_keys", MODULE_PATH)
guest_keys = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guest_keys)


class GuestSelectionTests(unittest.TestCase):
    def test_none_keeps_legacy_show_all_behavior(self):
        self.assertTrue(guest_keys.matches_selected_guest(None, "pve1", 100))

    def test_empty_selection_shows_no_guests(self):
        self.assertFalse(guest_keys.matches_selected_guest([], "pve1", 100))

    def test_node_aware_selection_matches(self):
        self.assertTrue(
            guest_keys.matches_selected_guest(["pve1:100"], "pve1", 100)
        )


if __name__ == "__main__":
    unittest.main()
