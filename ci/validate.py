#!/usr/bin/env python3
"""1shotwp-playbooks CI validator: structure + sha256 pins + Ed25519 signatures.

Mirrors the plugin-side policy (schema v1, canonical form) so every PR is
verified before it can change the catalog. Signatures verify via the
OpenSSL CLI against keys/publisher.pem.
"""
import base64, glob, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'keys', '1shotwp-playbooks.pub')
ID_RE = r'^[a-z0-9][a-z0-9-]{1,62}$'
SEMVER_RE = r'^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?$'
SLUG_RE = r'^[a-z0-9-]{1,30}$'

def canonical(doc):
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items() if k not in ('signature', 'source')}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    return json.dumps(clean(doc), sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def openssl_verify(msg_path, sig_path):
    r = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', PUB,
                        '-rawin', '-sigfile', sig_path, '-in', msg_path],
                       capture_output=True, text=True)
    return r.returncode == 0

fails = 0
reg = json.load(open(os.path.join(ROOT, 'registry.json')))
assert reg.get('format') == '1shotwp-playbook-registry/1'
seen = set()
for entry in reg['playbooks']:
    pid = entry['id']
    if pid in seen:
        print(f"FAIL {pid}: duplicate registry id"); fails += 1; continue
    seen.add(pid)
    path = os.path.join(ROOT, 'playbooks', pid + '.playbook.json')
    if not os.path.exists(path):
        print(f"FAIL {pid}: file missing"); fails += 1; continue
    raw = open(path, 'rb').read()
    if len(raw) > 131072:
        print(f"FAIL {pid}: exceeds 128 KB"); fails += 1; continue
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        print(f"FAIL {pid}: registry sha256 pin mismatch"); fails += 1; continue
    doc = json.loads(raw)
    for key, rx in (('id', ID_RE), ('version', SEMVER_RE)):
        import re
        if not re.match(rx, str(doc.get(key, ''))):
            print(f"FAIL {pid}: bad {key}"); fails += 1
    if doc.get('id') != pid:
        print(f"FAIL {pid}: document id mismatch"); fails += 1
    steps = doc.get('steps')
    if not isinstance(steps, list) or not (1 <= len(steps) <= 64):
        print(f"FAIL {pid}: bad steps"); fails += 1
    tags = doc.get('tags', [])
    if any(not re.match(SLUG_RE, t) for t in tags):
        print(f"FAIL {pid}: bad tags"); fails += 1
    canon_path, sig_path = '/tmp/ci.canon', '/tmp/ci.sig'
    open(canon_path, 'w').write(canonical(doc))
    sig = doc.get('signature', '')
    if not sig:
        print(f"WARN {pid}: unsigned (registry must set signed=false)")
        if entry.get('signed'):
            print(f"FAIL {pid}: registry claims signed but the file is not"); fails += 1
    else:
        open(sig_path, 'wb').write(base64.b64decode(sig))
        if not openssl_verify(canon_path, sig_path):
            print(f"FAIL {pid}: Ed25519 signature does not verify"); fails += 1
        elif not entry.get('signed'):
            print(f"FAIL {pid}: signed file but registry says signed=false"); fails += 1
for f in glob.glob(os.path.join(ROOT, 'playbooks', '*.playbook.json')):
    pid = os.path.basename(f)[: -len('.playbook.json')]
    if pid not in seen:
        print(f"FAIL {pid}: file not listed in registry.json"); fails += 1
print(f"CI VALIDATE: {len(reg['playbooks'])} entries, {fails} failures")
sys.exit(1 if fails else 0)
