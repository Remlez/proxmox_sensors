"""Pure helpers for correlating Proxmox backup jobs and vzdump tasks."""

from __future__ import annotations

import re
from datetime import datetime, timezone


def _to_iso_timestamp(value):
    """Convert Proxmox epoch timestamps to ISO-8601 strings."""
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def vzdump_task_vmid(task):
    """Return the guest ID associated with a vzdump task, when available."""
    task_id = task.get("id")
    if task_id not in (None, ""):
        return str(task_id)
    match = re.search(r":vzdump:([^:]+):", str(task.get("upid", "")))
    return match.group(1) if match else None


def job_vmids(job):
    """Normalize a backup job's VM selection into individual IDs."""
    raw_vmids = job.get("vmid")
    if raw_vmids in (None, "", "all"):
        return set()
    values = (
        raw_vmids
        if isinstance(raw_vmids, (list, tuple, set))
        else re.split(r"[;,\s]+", str(raw_vmids))
    )
    return {str(value) for value in values if str(value)}


def task_matches_backup_job(task, job):
    """Match a vzdump task to the backup job that could have produced it."""
    if not isinstance(task, dict):
        return False
    upid = str(task.get("upid", ""))
    if task.get("type") != "vzdump" and ":vzdump:" not in upid:
        return False

    job_node = job.get("node")
    task_node = task.get("node")
    if job_node and task_node and str(job_node) != str(task_node):
        return False

    vmids = job_vmids(job)
    task_vmid = vzdump_task_vmid(task)
    if vmids:
        return task_vmid in vmids
    return not job_node or not task_node or str(job_node) == str(task_node)


def build_backup_jobs_payload(jobs, tasks, now_ts=None):
    """Build a backup-job summary using each job's own latest task."""
    jobs = jobs if isinstance(jobs, list) else []
    tasks = tasks if isinstance(tasks, list) else []
    tasks = sorted(
        (task for task in tasks if isinstance(task, dict)),
        key=lambda item: item.get("endtime") or item.get("starttime") or 0,
        reverse=True,
    )[:20]

    normalized_jobs = []
    failed_jobs = 0
    last_run_ts = None
    recent_failed_ts = None
    current_ts = (
        datetime.now(tz=timezone.utc).timestamp() if now_ts is None else now_ts
    )

    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            continue
        matched_task = next(
            (task for task in tasks if task_matches_backup_job(task, job)), {}
        )
        starttime = matched_task.get("starttime")
        endtime = matched_task.get("endtime")
        run_ts = endtime or starttime

        duration = None
        if starttime is not None and endtime is not None:
            try:
                duration = max(int(endtime - starttime), 0)
            except (TypeError, ValueError):
                pass

        raw_status = matched_task.get("status")
        if isinstance(raw_status, str) and raw_status.lower() == "ok":
            last_status = "OK"
        elif raw_status:
            last_status = "error"
        else:
            last_status = "unknown"

        if last_status == "error":
            failed_jobs += 1
            if run_ts is not None and (
                recent_failed_ts is None or run_ts > recent_failed_ts
            ):
                recent_failed_ts = run_ts
        if run_ts is not None and (last_run_ts is None or run_ts > last_run_ts):
            last_run_ts = run_ts

        job_id = (
            job.get("id")
            or job.get("vmid")
            or job.get("job_id")
            or f"backup_job_{index}"
        )
        normalized_jobs.append(
            {
                "id": str(job_id),
                "node": job.get("node") or "cluster",
                "storage": job.get("storage") or job.get("dumpdir") or "unknown",
                "schedule": job.get("schedule") or "unknown",
                "last_status": last_status,
                "last_run": _to_iso_timestamp(run_ts),
                "duration": duration,
            }
        )

    state = "unknown"
    if normalized_jobs:
        if failed_jobs == 0 and all(
            job["last_status"] == "OK" for job in normalized_jobs
        ):
            state = "ok"
        elif failed_jobs > 1 or (
            failed_jobs == 1
            and recent_failed_ts is not None
            and (current_ts - recent_failed_ts) <= 86400
        ):
            state = "error"
        elif failed_jobs >= 1:
            state = "warning"

    return {
        "state": state,
        "total_jobs": len(normalized_jobs),
        "failed_jobs": failed_jobs,
        "last_run": _to_iso_timestamp(last_run_ts),
        "jobs": normalized_jobs,
    }
