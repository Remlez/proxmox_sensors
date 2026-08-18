"""Regression tests for backup job/task correlation."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/backup_jobs.py"
)
SPEC = importlib.util.spec_from_file_location("backup_jobs", MODULE_PATH)
backup_jobs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup_jobs)


class BackupJobsTests(unittest.TestCase):
    def test_each_job_uses_its_own_latest_task(self):
        jobs = [
            {"id": "job-100", "node": "pve1", "vmid": "100"},
            {"id": "job-200", "node": "pve1", "vmid": "200"},
        ]
        tasks = [
            {
                "type": "vzdump",
                "node": "pve1",
                "id": "200",
                "starttime": 190,
                "endtime": 200,
                "status": "ERROR",
            },
            {
                "type": "vzdump",
                "node": "pve1",
                "id": "100",
                "starttime": 90,
                "endtime": 100,
                "status": "OK",
            },
        ]

        payload = backup_jobs.build_backup_jobs_payload(jobs, tasks, now_ts=210)

        self.assertEqual("OK", payload["jobs"][0]["last_status"])
        self.assertEqual("error", payload["jobs"][1]["last_status"])
        self.assertEqual(1, payload["failed_jobs"])

    def test_vmid_is_parsed_from_upid(self):
        task = {"upid": "UPID:pve1:1:2:3:vzdump:101:user@pve:"}
        self.assertEqual("101", backup_jobs.vzdump_task_vmid(task))

    def test_node_wide_job_does_not_take_other_nodes_task(self):
        job = {"id": "all-pve1", "node": "pve1", "vmid": "all"}
        task = {"type": "vzdump", "node": "pve2", "id": "100"}
        self.assertFalse(backup_jobs.task_matches_backup_job(task, job))

    def test_non_dictionary_tasks_are_ignored(self):
        payload = backup_jobs.build_backup_jobs_payload(
            [{"id": "job-100", "vmid": "100"}],
            [None, "invalid"],
        )
        self.assertEqual("unknown", payload["jobs"][0]["last_status"])


if __name__ == "__main__":
    unittest.main()
