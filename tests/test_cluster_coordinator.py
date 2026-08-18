"""Regression test for cluster task data exposed to failed-task sensors."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest


PACKAGE = "cluster_coordinator_testpkg"
package = types.ModuleType(PACKAGE)
package.__path__ = []
sys.modules[PACKAGE] = package

homeassistant = types.ModuleType("homeassistant")
helpers = types.ModuleType("homeassistant.helpers")
update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")


class FakeDataUpdateCoordinator:
    def __init__(self, *_args, update_method, **_kwargs):
        self.update_method = update_method


update_coordinator.DataUpdateCoordinator = FakeDataUpdateCoordinator
update_coordinator.UpdateFailed = RuntimeError
sys.modules.update(
    {
        "homeassistant": homeassistant,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.update_coordinator": update_coordinator,
    }
)

constants = types.ModuleType(f"{PACKAGE}.const")
constants.CONF_NODE = "node"
constants.CONF_PLATFORM_TYPE = "platform_type"
sys.modules[f"{PACKAGE}.const"] = constants

logic = types.ModuleType(f"{PACKAGE}.logic")
logic.__path__ = []
sys.modules[f"{PACKAGE}.logic"] = logic

backup_jobs = types.ModuleType(f"{PACKAGE}.logic.backup_jobs")
backup_jobs.build_backup_jobs_payload = lambda jobs, tasks: {
    "jobs": jobs,
    "task_count": len(tasks),
}
sys.modules[f"{PACKAGE}.logic.backup_jobs"] = backup_jobs

guest_keys = types.ModuleType(f"{PACKAGE}.logic.guest_keys")
guest_keys.make_guest_key = lambda node, vmid: f"{node}:{vmid}"
guest_keys.matches_selected_guest = lambda *_args: True
sys.modules[f"{PACKAGE}.logic.guest_keys"] = guest_keys

node_metrics = types.ModuleType(f"{PACKAGE}.logic.node_metrics")
node_metrics.merge_node_status_with_cluster_resource = (
    lambda node_status, _resources, _node: node_status
)
sys.modules[f"{PACKAGE}.logic.node_metrics"] = node_metrics

MODULE_PATH = Path(__file__).parents[1] / "custom_components/proxmox_sensors/coordinator.py"
SPEC = importlib.util.spec_from_file_location(f"{PACKAGE}.coordinator", MODULE_PATH)
coordinator_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coordinator_module)


class FakeClient:
    async def get_cluster_resources(self, _hass):
        return []

    async def get_cluster_status(self, _hass):
        return {}

    async def get_cluster_ha_status(self, _hass):
        return {}

    async def get_cluster_firewall_options(self, _hass):
        return {}

    async def get_backup_jobs(self, _hass):
        return []

    async def get_cluster_tasks(self, _hass):
        return [{"status": "ERROR", "type": "vzdump"}]


class ClusterCoordinatorTests(unittest.TestCase):
    def test_cluster_tasks_are_kept_for_failed_task_sensor(self):
        entry = types.SimpleNamespace(
            data={"cluster_name": "lab"},
        )

        coordinator = asyncio.run(
            coordinator_module.create_cluster_coordinator(None, entry, FakeClient())
        )
        payload = asyncio.run(coordinator.update_method())

        self.assertEqual(
            [{"status": "ERROR", "type": "vzdump"}], payload["cluster_tasks"]
        )


if __name__ == "__main__":
    unittest.main()
