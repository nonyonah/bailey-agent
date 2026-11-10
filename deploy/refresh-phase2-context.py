"""Replace superseded setup notes; preserve unrelated memory and private originals."""
from datetime import datetime, timezone
import os
from pathlib import Path
from bailey.upgrade_channel import replace_private

home=Path(os.environ['HERMES_HOME'])
archive=home/'bailey-profile-history'/('phase2-context-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
archive.mkdir(mode=0o700,parents=True)
for name in ('USER.md','MEMORY.md'):
    path=home/'memories'/name
    old=path.read_text()
    replace_private(archive/name,old)
    lines=old.splitlines()
    stale=('Current verified setup, 2026-11-10:', 'Latest confirmed preference, 2026-11-10:',
           'Phase 1 only.', 'No email, calendar, financial, shopping, or payment integration is connected.',
           'User asked about meeting - no calendar integration available to check schedule',
           'Verified 2026-11-10:', 'Composio Gmail/Calendar are connected read-only')
    lines=[line for line in lines if not any(line.startswith(prefix) for prefix in stale)]
    lines=[line.replace("Owner's name, occupation, projects, and calendar are not yet known.",
                        "Occupation and projects have not yet been established.") for line in lines]
    # This sentence was the explicitly requested non-sensitive voice acceptance fixture.
    lines=[line.replace('User has meeting tomorrow at 10:00 AM (Africa/Lagos) - information provided directly, not from calendar integration',
                        'Voice acceptance used a test meeting sentence; it is not a real calendar commitment.') for line in lines]
    if name=='USER.md':
        lines.append('Verified 2026-11-10: iMessage primary; Slack manual fallback, both connected. Briefings on demand in requesting chat; automatic jobs paused. Gmail/Calendar use bailey_accounts for reads and bailey_writes for approval-gated proposals; the owner approves/executes with the operator CLI. bailey_tasks stores tasks. No payments.')
    replace_private(path,'\n'.join(lines).strip()+'\n')
    print(f'{name}: {len(old)} -> {len(path.read_text())} characters; original archived privately')
