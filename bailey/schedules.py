"""Keep legacy automatic briefings paused; briefings are now requested in chat."""
import json

JOBS = ({"name": "Bailey morning briefing"}, {"name": "Bailey evening briefing"})


def reconcile(api):
    def call(**kwargs):
        response = api(**kwargs)
        result = json.loads(response) if isinstance(response, str) else response
        if not result.get("success"):
            raise RuntimeError("Hermes cron API failed; inspect native cron status privately")
        return result

    jobs = call(action="list", include_disabled=True).get("jobs")
    if not isinstance(jobs, list):
        raise RuntimeError("Unsupported Hermes cron list response")
    names = {job["name"] for job in JOBS}
    for job in jobs:
        if job.get("name") not in names or job.get("enabled") is False:
            continue
        job_id = job.get("id") or job.get("job_id")
        if not job_id:
            raise RuntimeError("Unsupported Hermes job identifier")
        call(action="pause", job_id=job_id, reason="Owner requested on-demand briefings in either chat")
    # Never create/resume a job, including on a fresh installation.


def main():
    from tools.cronjob_tools import cronjob
    import fcntl
    import os
    from pathlib import Path
    with (Path(os.environ["HERMES_HOME"]) / "bailey-schedules.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        reconcile(cronjob)
    print("Automatic Bailey briefings paused; request a briefing in iMessage or Slack")


if __name__ == "__main__":
    main()
