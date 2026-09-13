<!--
Thanks for contributing a playbook! Both artifacts come straight from
`wp_playbook_submit` on your site (file + registry entry). Keep them byte-for-byte.
-->
## New playbook submission

**Playbook id:** <!-- e.g. my-awesome-flow -->
**Version:** <!-- e.g. 1.0.0 -->
**Submission kind:** community (unsigned) <!-- or: promotion of an existing community playbook -->

## What it does

<!-- Two or three sentences a site owner would understand. -->

## Contributor checklist

- [ ] File added at `playbooks/<id>.playbook.json` — saved **byte-for-byte** from `wp_playbook_submit` (or sha256 recomputed by hand)
- [ ] `registry.json` entry appended, `"signed": false`, sha256 matching the exact file bytes
- [ ] `python3 ci/validate.py` green locally
- [ ] Steps reference only tools that exist on a standard target site (or the requirement is stated in the description)
- [ ] Every mutating step carries guardrails
- [ ] Tested at least once on a real site (author → run → observe)

## Maintainer use

- [ ] CI green (structure, pins, signatures)
- [ ] Steps reviewed for safety and ordering
- [ ] Merged → catalog regenerates via Actions
