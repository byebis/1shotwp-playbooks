# Contributing a playbook to the registry

Thank you for building playbooks for the 1ShotWP agent ecosystem! A playbook is a
**JSON document, never executable code**: guided steps that name the exact tools to
call, their parameters and the guardrails the agent must respect. The agent executes
every step through the normal WordPress safety stack (capabilities, approval queue,
paranoid mode, undo journal) — your job is to design the *path*, the platform enforces
the *brakes*.

## The happy path (author on a live site)

The whole flow can run without touching a JSON editor:

1. **Author** it on a real WordPress site with 1ShotWP ≥ 1.6.1:
   `wp_playbook_author` takes your complete `.playbook.json` v1 document and validates
   it against the schema AND every referenced tool against that live site.
2. **Test** it: the authored playbook is immediately visible via `wp_list_skills` /
   `wp_get_skill` — run it once on a throwaway task before submitting.
3. **Package** the submission: `wp_playbook_submit id=<your-id>` returns
   - the exact `.playbook.json` to save **byte-for-byte** (the registry pins its sha256),
   - a ready-to-append `registry.json` entry,
   - the PR title and body, and a pre-filled GitHub "new file" URL.
4. **Open the PR** on this repository: add the file under `playbooks/` **and** append the
   registry entry to `registry.json` (both come straight from the submit bundle).
5. CI validates structure, pins and signatures. Humans review the *content*: are the
   steps safe, ordered sensibly, guarded where they mutate?
6. After merge the playbook is installable on every 1ShotWP site on the next
   `wp_playbook_list_remote`, and the /playbooks catalog page regenerates automatically.

## Hand-written submissions are welcome too

1. Fork the repo, add `playbooks/<id>.playbook.json` and the matching `registry.json`
   entry (`"signed": false` for community submissions — compute the sha256 of the exact
   file bytes you are adding, e.g. `sha256sum playbooks/<id>.playbook.json`).
2. Validate locally: `python3 ci/validate.py`.
3. Open the PR using the template checklist.

## Document rules (schema v1)

| Field | Rule |
|---|---|
| `format` / `format_version` | `1shotwp-playbook` / `1` |
| `id` | `^[a-z0-9][a-z0-9-]{1,62}$`, unique in the registry |
| `version` | semver `major.minor.patch` |
| `name` / `description` | 3–120 / 3–600 chars, honest and specific |
| `license` | SPDX id (MIT for official ones) |
| `steps` | 1–64; each has `title`, `detail`, `tools` (≤ 32, must exist on target sites) |
| `params` | ≤ 32; `^[a-z][a-z0-9_]{0,63}$`, each with a description |
| `guardrails` | ≤ 32 strings; **mandatory when any referenced tool mutates the site** |
| `tags` | ≤ 10 lowercase slugs |
| document size | ≤ 128 KB |

Rules enforced identically by CI (this repo) and by the plugin at install time — a
playbook that names a tool a site does not have cannot be installed there, whatever CI says.

## Signatures and trust tiers

- **Official playbooks** carry a detached Ed25519 signature over their canonical form,
  verified against the publisher keys pinned in the plugin (the public halves live in
  `keys/` — PUBLIC material only, private keys never touch this repository). They are
  marked `"signed": true` and carry a `key_id` naming the signing generation.
- **Community submissions** land unsigned with `"signed": false` — still sha256-pinned,
  still CI-validated, still installable; the skills channel shows them as
  `verified=false`.
- **Key generations**: `k1` is the launch key (its private half was lost in a
  maintainer-environment reset — the 15 launch playbooks keep their valid signatures
  against the pinned public half); `k2` is the active signing generation since
  1ShotWP 1.6.2 "Zecca" and signs every NEW official playbook.
- **Official promotion flow**: when a well-established community playbook deserves the
  official badge, the maintainer validates it once more and signs it with the active
  generation (`php promote-playbook.php <file> --key k2 --out playbooks/ --registry registry.json`):
  the document must pass full schema + live-tool validation BEFORE anything is signed,
  the result is self-verified against the plugin's own verifier, and the registry entry
  flips to `"signed": true` with `"key_id": "k2"`. A pre-signed submission is refused —
  promotion signs community work, never over someone else's seal.

## Review priorities

- Safety first: mutating steps need explicit guardrails; destructive operations belong
  late in the flow, after a verification step.
- Portability: reference core tools and widely-installed integrations, or state the
  requirement in the description and `compat.requires.plugins`.
- Honesty: the description is what site owners read before installing — no overpromising.
