# 1ShotWP Playbooks — the official registry

The public, zero-server marketplace registry for [1ShotWP](https://github.com/byebis/1shotwp) playbooks: guided, agent-run jobs for WordPress, distributed as **signed JSON documents** (never executable code).

- **Format**: `1shotwp-playbook` v1 — params, steps (with the exact tools to call), guardrails, license.
- **Integrity**: every file is sha256-pinned in [`registry.json`](registry.json); official playbooks carry a detached **Ed25519 signature** over their canonical form (keys/).
- **Runtime**: the 1ShotWP plugin (≥ 1.6.0) reads this registry, verifies pins + signatures, checks every referenced tool against YOUR site, and hands the playbook to the agent — which executes it step by step through the normal safety stack (capabilities, approval queue, paranoid mode, undo journal). **Install ≠ run.**
- **No server of ours**: this is a static Git repository. No accounts, no telemetry, no phone-home.

## Install from any 1ShotWP agent

```
wp_playbook_list_remote          # browse the catalog
wp_playbook_install  id=seo-audit-pro
wp_list_skills                   # the playbook now appears with source=marketplace
wp_get_skill         id=seo-audit-pro
```

## Contribute a playbook

1. Fork, add `playbooks/<id>.playbook.json` (validate locally: `python3 ci/validate.py`).
2. Sign it with your own key if you like — unsigned submissions install flagged `verified=false`.
3. Open a PR: CI validates schema, sha256 pins and signatures. The community reviews the STEPS (tools, guardrails, ordering).
4. After merge, the catalog updates for every 1ShotWP site on the next `wp_playbook_list_remote`.

License: each playbook carries its own SPDX license id (official ones: MIT).
