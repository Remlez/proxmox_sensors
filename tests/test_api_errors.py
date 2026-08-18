"""Regression tests for expected optional Proxmox API errors."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest


requests = types.ModuleType("requests")
requests.exceptions = types.SimpleNamespace(
    RequestException=Exception,
    ConnectionError=ConnectionError,
    ConnectTimeout=TimeoutError,
    Timeout=TimeoutError,
)
sys.modules.setdefault("requests", requests)

urllib3 = types.ModuleType("urllib3")
urllib3.exceptions = types.SimpleNamespace(InsecureRequestWarning=Warning)
urllib3.disable_warnings = lambda *_args, **_kwargs: None
sys.modules.setdefault("urllib3", urllib3)

proxmoxer = types.ModuleType("proxmoxer")
proxmoxer.ProxmoxAPI = object
sys.modules.setdefault("proxmoxer", proxmoxer)

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components/proxmox_sensors/api.py"
)
SPEC = importlib.util.spec_from_file_location("proxmox_api", MODULE_PATH)
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)


class ApiErrorTests(unittest.TestCase):
    def test_no_zfs_pool_error_is_expected(self):
        err = RuntimeError("zpool list failed: exit code 1")
        self.assertTrue(api._is_expected_no_zfs_pools_error(err))

    def test_unrelated_zfs_error_is_not_hidden(self):
        err = RuntimeError("disk controller timed out")
        self.assertFalse(api._is_expected_no_zfs_pools_error(err))

    def test_sys_modify_403_is_expected_for_optional_update_check(self):
        err = RuntimeError("403 Forbidden: Permission check failed (Sys.Modify)")
        self.assertTrue(api._is_expected_updates_permission_error(err))


if __name__ == "__main__":
    unittest.main()
