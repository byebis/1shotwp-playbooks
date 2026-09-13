#!/usr/bin/env python3
"""Build the /playbooks SEO catalog page from registry.json.

Generates docs/index.html: semantic, dependency-free, crawler-friendly HTML
with Open Graph + JSON-LD structured data. The GitHub Actions workflow runs
this on every push to main and commits the result; GitHub Pages serves the
docs/ directory. Zero servers, as always.
"""
import html
import json
import os
import subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'index.html')
CANONICAL = 'https://byebis.github.io/1shotwp-playbooks/'
RAW_BASE = 'https://raw.githubusercontent.com/byebis/1shotwp-playbooks/main/playbooks/'
REPO = 'https://github.com/byebis/1shotwp-playbooks'
PLUGIN = 'https://github.com/byebis/1shotwp'

esc = html.escape

reg = json.load(open(os.path.join(ROOT, 'registry.json')))
entries = sorted(reg.get('playbooks', []), key=lambda e: e.get('id', ''))
updated = reg.get('updated', '')


def git_date():
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%cI'], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def card(e):
    pid = esc(e['id'])
    name = esc(e.get('name', pid))
    desc = esc(e.get('description', ''))
    version = esc(e.get('version', ''))
    author = esc(str(e.get('author', 'community')))
    license_id = esc(e.get('license', 'n/a'))
    tags = ''.join(f'<span class="tag">{esc(t)}</span>' for t in e.get('tags', []))
    signed = ('<span class="badge signed" title="Ed25519 signature verified against the pinned publisher key">signed</span>'
              if e.get('signed') else
              '<span class="badge community" title="Community submission, sha256-pinned">community</span>')
    sha_short = esc((e.get('sha256', '') or '')[:12])
    dl = esc(RAW_BASE + e['id'] + '.playbook.json')
    return f"""    <article class="card" id="{pid}">
      <h2>{name} {signed}</h2>
      <p class="desc">{desc}</p>
      <p class="meta">v{version} · by {author} · license {license_id} · sha256 <code>{sha_short}…</code></p>
      <div class="tags">{tags}</div>
      <details>
        <summary>How to install</summary>
        <pre>wp_playbook_install id={e['id']}</pre>
        <p>Requires the <a href="{esc(PLUGIN)}">1ShotWP</a> plugin (self-hosted MCP for WordPress).</p>
      </details>
      <p class="dl"><a href="{dl}" rel="nofollow">Download the signed JSON document</a></p>
    </article>"""


items_jsonld = []
for e in entries:
    items_jsonld.append({
        '@type': 'ListItem',
        'position': len(items_jsonld) + 1,
        'item': {
            '@type': 'SoftwareSourceCode',
            'name': e.get('name', e['id']),
            'description': e.get('description', ''),
            'version': e.get('version', ''),
            'license': e.get('license', ''),
            'programmingLanguage': 'JSON',
            'author': {'@type': 'Organization' if e.get('signed') else 'Person',
                       'name': str(e.get('author', 'community'))},
            'downloadUrl': RAW_BASE + e['id'] + '.playbook.json',
        },
    })
jsonld = json.dumps({'@context': 'https://schema.org', '@type': 'ItemList',
                     'name': '1ShotWP Playbooks registry',
                     'numberOfItems': len(entries), 'itemListElement': items_jsonld},
                    ensure_ascii=False)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1ShotWP Playbooks — signed, agent-run playbooks for WordPress ({len(entries)} available)</title>
<meta name="description" content="The official registry of {len(entries)} signed JSON playbooks for 1ShotWP, the self-hosted MCP server for WordPress. Every playbook is sha256-pinned, tool-checked at install and executed step by step through the normal safety stack. Install them with one tool call.">
<link rel="canonical" href="{CANONICAL}">
<meta property="og:type" content="website">
<meta property="og:title" content="1ShotWP Playbooks — the signed playbook registry for WordPress AI agents">
<meta property="og:description" content="{len(entries)} signed JSON playbooks (SEO audit, WooCommerce launch, GDPR, speed pass…) for the self-hosted MCP server for WordPress. sha256-pinned, Ed25519-signed, zero servers.">
<meta property="og:url" content="{CANONICAL}">
<script type="application/ld+json">
{jsonld}
</script>
<style>
:root {{ color-scheme: light dark; }}
body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; max-width: 62rem; margin: 0 auto; padding: 1.2rem; line-height: 1.5; }}
header p.lead {{ font-size: 1.05rem; }}
.badge {{ display: inline-block; font-size: .72rem; padding: .1rem .5rem; border-radius: 999px; vertical-align: middle; }}
.badge.signed {{ background: #1a7f37; color: #fff; }}
.badge.community {{ background: #6e7781; color: #fff; }}
.card {{ border: 1px solid #8884; border-radius: 10px; padding: .9rem 1.1rem; margin: 1rem 0; }}
.card h2 {{ margin: .1rem 0 .4rem; font-size: 1.15rem; }}
.desc {{ margin: .2rem 0; }}
.meta {{ color: #77717e; font-size: .86rem; margin: .3rem 0; }}
.tags {{ margin: .4rem 0; }}
.tag {{ display: inline-block; background: #7b68ee22; border-radius: 6px; padding: .05rem .45rem; margin-right: .3rem; font-size: .8rem; }}
pre {{ background: #8881; padding: .5rem .7rem; border-radius: 8px; overflow-x: auto; }}
footer {{ margin-top: 2rem; color: #77717e; font-size: .85rem; }}
a {{ color: #0969da; }}
</style>
</head>
<body>
<header>
  <h1>1ShotWP Playbooks — the signed playbook registry for WordPress AI agents</h1>
  <p class="lead">Guided, agent-run jobs for WordPress distributed as <strong>signed JSON documents, never executable code</strong>: SEO audit, WooCommerce launch, GDPR privacy pass, speed pass, content refresh and more. Every file is sha256-pinned in <a href="{esc(REPO)}/blob/main/registry.json">registry.json</a>, official playbooks carry an Ed25519 signature, and every referenced tool is checked against <em>your</em> site at install. Install ≠ run: the agent executes each step through the normal safety stack (capabilities, approval queue, undo journal).</p>
  <p><strong>{len(entries)} playbooks</strong> available · registry updated <time datetime="{esc(updated or git_date())}">{esc((updated or git_date())[:10])}</time></p>
</header>
<main>
{chr(10).join(card(e) for e in entries)}
</main>
<footer>
  <p>Distributed with a zero-server model: this registry is a static Git repository — no accounts, no telemetry, no phone-home. Contribute your own playbook via the <a href="{esc(REPO)}/blob/main/CONTRIBUTING.md">contributing guide</a> (author it on your site with <code>wp_playbook_author</code>, package it with <code>wp_playbook_submit</code>, open a PR).</p>
  <p><a href="{esc(PLUGIN)}">1ShotWP</a> — self-hosted MCP (Model Context Protocol) server for WordPress · registry format <code>{esc(reg.get('format', ''))}</code></p>
</footer>
</body>
</html>
"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(page)
print(f"catalog: {len(entries)} playbooks -> {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT)} B)")
