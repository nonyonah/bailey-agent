"""Apply reviewed Phase 2 policy after the rollout script validates/archives the old release."""
import os
from pathlib import Path
from bailey.profile import ROOT, profile_phase, read_env, validate
from bailey.upgrade_channel import migrate, replace_private

home=Path(os.environ['HERMES_HOME'])
if profile_phase(home)!=2:
    raise ValueError('Use initial Phase 2 onboarding for a Phase 1 profile')
env=read_env(home/'.env')
migrate(home,env['PHOTON_ALLOWED_USERS'],enable_whatsapp=False,enable_slack=True,phase=2)
replace_private(home/'SOUL.md',(ROOT/'config/identity/SOUL-phase2.md').read_text())
for name,destination in [('daily-briefing-phase2','daily-briefing'),('commitment-tracker','commitment-tracker'),
                         ('email-assistant','email-assistant'),('calendar-assistant','calendar-assistant')]:
    target=home/'skills'/destination
    target.mkdir(mode=0o700,parents=True,exist_ok=True)
    replace_private(target/'SKILL.md',(ROOT/'config/skills'/name/'SKILL.md').read_text())
validate(home,require_credentials=True)
print('Phase 2 proposal tools applied; no proposals approved or executed')
