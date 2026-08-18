"""Regression tests for VM and CT percentage entities."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).parents[1] / "custom_components/proxmox_sensors"
PACKAGE = "guest_sensor_testpkg"

package = types.ModuleType(PACKAGE)
package.__path__ = []
sensor_package = types.ModuleType(f"{PACKAGE}.sensor")
sensor_package.__path__ = []
logic_package = types.ModuleType(f"{PACKAGE}.logic")
logic_package.__path__ = []
sys.modules.update(
    {
        PACKAGE: package,
        f"{PACKAGE}.sensor": sensor_package,
        f"{PACKAGE}.logic": logic_package,
    }
)

homeassistant = types.ModuleType("homeassistant")
components = types.ModuleType("homeassistant.components")
sensor_component = types.ModuleType("homeassistant.components.sensor")
sensor_component.SensorDeviceClass = types.SimpleNamespace(DATA_SIZE="data_size")
sensor_component.SensorStateClass = types.SimpleNamespace(
    MEASUREMENT="measurement", TOTAL_INCREASING="total_increasing"
)
ha_const = types.ModuleType("homeassistant.const")
ha_const.PERCENTAGE = "%"
ha_const.UnitOfInformation = types.SimpleNamespace(GIBIBYTES="GiB")
ha_const.UnitOfTime = types.SimpleNamespace(HOURS="h")
sys.modules.update(
    {
        "homeassistant": homeassistant,
        "homeassistant.components": components,
        "homeassistant.components.sensor": sensor_component,
        "homeassistant.const": ha_const,
    }
)

constants = types.ModuleType(f"{PACKAGE}.const")
constants.DOMAIN = "proxmox_sensors"
sys.modules[f"{PACKAGE}.const"] = constants


class FakeBaseSensor:
    def __init__(self, coordinator, sensor_id, _name, unit, _unique_id, node=None):
        self.coordinator = coordinator
        self._sensor_id = sensor_id
        self._node = node or "node"
        self._attr_native_unit_of_measurement = unit


base = types.ModuleType(f"{PACKAGE}.sensor.base")
base.ProxmoxBaseSensor = FakeBaseSensor
sys.modules[f"{PACKAGE}.sensor.base"] = base

guest_keys = types.ModuleType(f"{PACKAGE}.logic.guest_keys")
guest_keys.make_guest_key = lambda node, vmid: f"{node}:{vmid}"
sys.modules[f"{PACKAGE}.logic.guest_keys"] = guest_keys


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load(f"{PACKAGE}.logic.guest_metrics", ROOT / "logic/guest_metrics.py")
vm_module = _load(f"{PACKAGE}.sensor.vm", ROOT / "sensor/vm.py")
ct_module = _load(f"{PACKAGE}.sensor.ct", ROOT / "sensor/ct.py")


class GuestPercentageSensorTests(unittest.TestCase):
    def test_vm_memory_and_disk_percentages(self):
        coordinator = types.SimpleNamespace(
            data={
                "vms": {
                    "pve1:100": {
                        "mem": 3 * 1024,
                        "maxmem": 4 * 1024,
                        "disk": 20 * 1024,
                        "maxdisk": 80 * 1024,
                    }
                }
            }
        )

        memory = vm_module.ProxmoxVMAttributeSensor(
            coordinator, 100, "pve1", "VM", "memory_usage", "%", "mdi:memory"
        )
        disk = vm_module.ProxmoxVMAttributeSensor(
            coordinator, 100, "pve1", "VM", "disk_usage", "%", "mdi:harddisk"
        )

        self.assertEqual(75.0, memory._get_value())
        self.assertEqual(25.0, disk._get_value())
        self.assertEqual("measurement", memory._attr_state_class)

    def test_ct_memory_and_disk_percentages(self):
        coordinator = types.SimpleNamespace(
            data={
                "cts": {
                    "pve1:101": {
                        "mem": 512,
                        "maxmem": 1024,
                        "disk": 9,
                        "maxdisk": 12,
                    }
                }
            }
        )

        memory = ct_module.ProxmoxContainerAttributeSensor(
            coordinator, 101, "pve1", "CT", "memory_usage", "%", "mdi:memory"
        )
        disk = ct_module.ProxmoxContainerAttributeSensor(
            coordinator, 101, "pve1", "CT", "disk_usage", "%", "mdi:harddisk"
        )

        self.assertEqual(50.0, memory._get_value())
        self.assertEqual(75.0, disk._get_value())
        self.assertEqual("measurement", disk._attr_state_class)


if __name__ == "__main__":
    unittest.main()
