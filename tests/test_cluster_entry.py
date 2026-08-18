"""Regression test for automatic cluster config-entry creation."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest


PACKAGE = "cluster_entry_testpkg"
package = types.ModuleType(PACKAGE)
package.__path__ = []
sys.modules[PACKAGE] = package

homeassistant = types.ModuleType("homeassistant")
config_entries = types.ModuleType("homeassistant.config_entries")
config_entries.ConfigEntry = object
core = types.ModuleType("homeassistant.core")
core.HomeAssistant = object
exceptions = types.ModuleType("homeassistant.exceptions")
exceptions.ConfigEntryNotReady = RuntimeError
const = types.ModuleType("homeassistant.const")
const.Platform = types.SimpleNamespace(
    SENSOR="sensor", BUTTON="button", BINARY_SENSOR="binary_sensor"
)
helpers = types.ModuleType("homeassistant.helpers")
entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")

sys.modules.update(
    {
        "homeassistant": homeassistant,
        "homeassistant.config_entries": config_entries,
        "homeassistant.core": core,
        "homeassistant.exceptions": exceptions,
        "homeassistant.const": const,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.entity_registry": entity_registry,
    }
)

constants = types.ModuleType(f"{PACKAGE}.const")
for name, value in {
    "DOMAIN": "proxmox_sensors",
    "CONF_HOST": "host",
    "CONF_USER": "user",
    "CONF_PASSWORD": "password",
    "CONF_TOKEN_ID": "token_id",
    "CONF_TOKEN_SECRET": "token_secret",
    "CONF_NODE": "node",
    "CONF_PLATFORM_TYPE": "platform_type",
    "CONF_VERIFY_SSL": "verify_ssl",
}.items():
    setattr(constants, name, value)
sys.modules[f"{PACKAGE}.const"] = constants

services = types.ModuleType(f"{PACKAGE}.services")
services.register_services = lambda *_args: None
services.unregister_services = lambda *_args: None
sys.modules[f"{PACKAGE}.services"] = services

api_module = types.ModuleType(f"{PACKAGE}.api")
api_module.ProxmoxClient = object
sys.modules[f"{PACKAGE}.api"] = api_module

coordinator = types.ModuleType(f"{PACKAGE}.coordinator")
coordinator.create_proxmox_coordinator = lambda *_args: None
coordinator.create_cluster_coordinator = lambda *_args: None
sys.modules[f"{PACKAGE}.coordinator"] = coordinator

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components/proxmox_sensors/__init__.py"
)
SPEC = importlib.util.spec_from_file_location(
    PACKAGE, MODULE_PATH, submodule_search_locations=[]
)
integration = importlib.util.module_from_spec(SPEC)
sys.modules[PACKAGE] = integration
SPEC.loader.exec_module(integration)


class FakeFlowManager:
    def __init__(self):
        self.calls = []

    async def async_init(self, domain, context, data):
        self.calls.append((domain, context, data))


class FakeConfigEntries:
    def __init__(self):
        self.flow = FakeFlowManager()
        self.entries = []
        self.removed = []

    def async_entries(self, _domain):
        return self.entries

    async def async_remove(self, entry_id):
        self.removed.append(entry_id)


class ClusterEntryTests(unittest.TestCase):
    def test_cluster_flow_is_started_with_reused_credentials(self):
        hass = types.SimpleNamespace(config_entries=FakeConfigEntries())
        entry = types.SimpleNamespace(
            entry_id="parent-id",
            data={
                "host": "192.0.2.1",
                "user": "homeassistant@pve",
                "token_id": "ha-token",
                "token_secret": "secret",
                "platform_type": "PVE",
                "node": "pve1",
            },
        )

        asyncio.run(
            integration._async_manage_cluster_entry(hass, entry, "lab", True)
        )

        self.assertEqual(1, len(hass.config_entries.flow.calls))
        domain, context, data = hass.config_entries.flow.calls[0]
        self.assertEqual("proxmox_sensors", domain)
        self.assertEqual({"source": "import"}, context)
        self.assertEqual("CLUSTER", data["platform_type"])
        self.assertEqual("parent-id", data["parent_entry_id"])

    def test_removing_parent_removes_managed_cluster_child(self):
        config_entries = FakeConfigEntries()
        config_entries.entries = [
            types.SimpleNamespace(
                entry_id="child-id",
                data={
                    "platform_type": "CLUSTER",
                    "parent_entry_id": "parent-id",
                },
            ),
            types.SimpleNamespace(
                entry_id="unrelated-child",
                data={
                    "platform_type": "CLUSTER",
                    "parent_entry_id": "other-parent",
                },
            ),
        ]
        hass = types.SimpleNamespace(config_entries=config_entries)
        parent = types.SimpleNamespace(
            entry_id="parent-id", data={"platform_type": "PVE"}
        )

        asyncio.run(integration.async_remove_entry(hass, parent))

        self.assertEqual(["child-id"], config_entries.removed)


if __name__ == "__main__":
    unittest.main()
