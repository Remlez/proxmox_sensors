"""Tests for entity-registry cleanup scoping."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/entity_registry.py"
)
SPEC = importlib.util.spec_from_file_location("entity_registry", MODULE_PATH)
entity_registry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entity_registry)


class EntityRegistryCleanupTests(unittest.TestCase):
    def test_marks_only_missing_sensor_as_obsolete(self):
        known = {"sensor-still-present"}

        self.assertTrue(
            entity_registry.is_obsolete_sensor_entity(
                SimpleNamespace(domain="sensor", unique_id="old-sensor"), known
            )
        )
        self.assertFalse(
            entity_registry.is_obsolete_sensor_entity(
                SimpleNamespace(domain="sensor", unique_id="sensor-still-present"),
                known,
            )
        )

    def test_never_prunes_other_platforms(self):
        known = set()

        self.assertFalse(
            entity_registry.is_obsolete_sensor_entity(
                SimpleNamespace(domain="button", unique_id="old-button"), known
            )
        )
        self.assertFalse(
            entity_registry.is_obsolete_sensor_entity(
                SimpleNamespace(domain="binary_sensor", unique_id="old-problem"),
                known,
            )
        )
