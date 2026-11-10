"""Operator rollout with private configuration rollback; does not connect external accounts."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from bailey.profile import ROOT, read_env, validate
from bailey.upgrade_channel import migrate, replace_private

home = Path(os.environ['HERMES_HOME'])
validate(home, require_credentials=True)
names = ('config.yaml', '.env', 'bailey-profile.json', 'bailey-initial-config.json', 'SOUL.md',
         'skills/daily-briefing/SKILL.md', 'skills/commitment-tracker/SKILL.md')
before = {name:((home/name).read_text() if (home/name).exists() else None) for name in names}
archive = home/'bailey-profile-history'/('phase2-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
archive.mkdir(mode=0o700, parents=True)
for name, content in before.items():
    if content is not None:
        (archive/name).parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        replace_private(archive/name, content)
plugins = home/'plugins'
plugins.mkdir(mode=0o700, exist_ok=True)
link = plugins/'bailey_productivity'
created_link = not link.exists() and not link.is_symlink()
if created_link:
    link.symlink_to(ROOT/'plugins/bailey_productivity', target_is_directory=True)
try:
    # Preserve native OAuth handling. Never expose token contents to the model or logs.
    token_dir = home/'mcp-tokens'
    token_dir.mkdir(mode=0o700,exist_ok=True)
    for source in (home.parent/'composio-onboarding'/'mcp-tokens').glob('composio*'):
        if source.is_symlink() or not source.is_file():
            raise ValueError('Invalid native Composio credential file')
        replace_private(token_dir/source.name,source.read_text())
    env = read_env(home/'.env')
    migrate(home,env['PHOTON_ALLOWED_USERS'],enable_whatsapp=False,enable_slack=True,phase=2)
    replace_private(home/'SOUL.md',(ROOT/'config/identity/SOUL-phase2.md').read_text())
    # Briefing instructions must match the newly available tools.
    for source, destination in [('daily-briefing-phase2','daily-briefing'),('commitment-tracker','commitment-tracker')]:
        target = home/'skills'/destination
        target.mkdir(mode=0o700,parents=True,exist_ok=True)
        replace_private(target/'SKILL.md',(ROOT/'config/skills'/source/'SKILL.md').read_text())
    validate(home,require_credentials=True)
    subprocess.run([os.environ['HERMES_PYTHON'],'-m','bailey.runtime_check'],check=True)
except BaseException:
    for name, content in before.items():
        if content is None:
            (home/name).unlink(missing_ok=True)
        else:
            replace_private(home/name,content)
    if created_link:
        link.unlink()
    print('Phase 2 rollout failed; previous profile restored. Gateway not restarted.')
    raise
print('Reviewed Phase 2 tasks and account reads installed; external mutations remain unavailable.')
