"""The fake native API is used only in tests; production imports real Hermes."""
import unittest
from bailey.schedules import JOBS, reconcile


class NativeCronFixture:
    def __init__(self, jobs=()):
        self.jobs = list(jobs)
        self.calls = []

    def __call__(self, **args):
        self.calls.append(args)
        if args["action"] == "list":
            assert args.get("include_disabled")
            return {"success": True, "jobs": self.jobs}
        if args["action"] != "pause":
            raise AssertionError("On-demand briefings must not create/resume schedules")
        next(j for j in self.jobs if j["id"] == args["job_id"])["enabled"] = False
        return {"success": True}


class ScheduleTests(unittest.TestCase):
    def test_existing_briefings_pause_once_without_touching_other_jobs(self):
        api = NativeCronFixture([
            {"id": "morning", "name": JOBS[0]["name"], "enabled": True},
            {"id": "evening", "name": JOBS[1]["name"], "enabled": True},
            {"id": "other", "name": "Owner's unrelated reminder", "enabled": True}])
        reconcile(api)
        reconcile(api)
        self.assertEqual([j["enabled"] for j in api.jobs], [False, False, True])
        self.assertEqual(len([c for c in api.calls if c["action"] == "pause"]), 2)

    def test_fresh_install_has_no_automatic_jobs(self):
        api = NativeCronFixture()
        reconcile(api)
        self.assertEqual(api.jobs, [])
        self.assertEqual([c["action"] for c in api.calls], ["list"])

    def test_duplicate_legacy_jobs_are_all_paused(self):
        api = NativeCronFixture([{"id": str(i), "name": JOBS[0]["name"], "enabled": True} for i in range(2)])
        reconcile(api)
        self.assertTrue(all(j["enabled"] is False for j in api.jobs))

    def test_native_failure_is_not_reported_as_success_or_leaked(self):
        with self.assertRaisesRegex(RuntimeError, "Hermes cron API failed") as error:
            reconcile(lambda **args: {"success": False, "error": "secret=do-not-print"})
        self.assertNotIn("do-not-print", str(error.exception))
