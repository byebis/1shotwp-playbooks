#!/usr/bin/env python3
"""1shotwp-playbooks CI validator: structure + sha256 pins + Ed25519 signatures.

Mirrors the plugin-side policy (schema v1, canonical form) so every PR is
verified before it can change the catalog. Signatures verify via the
OpenSSL CLI against the pinned PUBLIC keys in keys/ (PUBLIC material only —
private keys never touch this repository):

  keys/1shotwp-playbooks.pub     k1 — launch generation (private half lost
                                 in the maintainer-environment reset of
                                 2026-09; its signatures stay valid forever
                                 against the pinned public half)
  keys/1shotwp-playbooks-v2.pub  k2 — active signing generation since
                                 1ShotWP 1.6.2 "Zecca" (used for every NEW
                                 official playbook and promotion)

An entry may declare `key_id` (k1/k2/k-<fingerprint>); when present it must
match the key whose signature verifies. registry.json may declare a
`public_keys` map {key_id: base64-pubkey} for documentation; any key listed
there must decode to 32 raw bytes.
"""
import base64, glob, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBS = {
    'k1': os.path.join(ROOT, 'keys', '1shotwp-playbooks.pub'),
    'k2': os.path.join(ROOT, 'keys', '1shotwp-playbooks-v2.pub'),
}
ID_RE = r'^[a-z0-9][a-z0-9-]{1,62}$'
SEMVER_RE = r'^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?$'
SLUG_RE = r'^[a-z0-9-]{1,30}$'
KEYID_RE = r'^k1$|^k2$|^k-[0-9a-f]{8}$'

def canonical(doc):
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items() if k not in ('signature', 'source')}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    return json.dumps(clean(doc), sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def openssl_verify(msg_path, sig_path, pub_path):
    r = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', pub_path,
                        '-rawin', '-sigfile', sig_path, '-in', msg_path],
                       capture_output=True, text=True)
    return r.returncode == 0

fails = 0
reg = json.load(open(os.path.join(ROOT, 'registry.json')))
assert reg.get('format') == '1shotwp-playbook-registry/1'

# The documented trust map, when present, must hold real 32-byte public keys.
if 'public_keys' in reg:
    if not isinstance(reg['public_keys'], dict) or not reg['public_keys']:
        print("FAIL registry: public_keys must be a non-empty {key_id: base64} map"); fails += 1
    else:
        for kid, b64 in reg['public_keys'].items():
            if not re.match(KEYID_RE, str(kid)):
                print(f"FAIL registry: bad key_id format '{kid}'"); fails += 1
            try:
                raw = base64.b64decode(str(b64), validate=True)
                if len(raw) != 32:
                    raise ValueError
            except Exception:
                print(f"FAIL registry: public_keys['{kid}'] is not a 32-byte base64 key"); fails += 1

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
    kid = entry.get('key_id')
    if kid is not None and not re.match(KEYID_RE, str(kid)):
        print(f"FAIL {pid}: bad key_id '{kid}'"); fails += 1; kid = None
    canon_path, sig_path = '/tmp/ci.canon', '/tmp/ci.sig'
    open(canon_path, 'w').write(canonical(doc))
    sig = doc.get('signature', '')
    if not sig:
        print(f"WARN {pid}: unsigned (registry must set signed=false)")
        if entry.get('signed'):
            print(f"FAIL {pid}: registry claims signed but the file is not"); fails += 1
        if kid is not None:
            print(f"FAIL {pid}: unsigned entry cannot carry a key_id"); fails += 1
    else:
        open(sig_path, 'wb').write(base64.b64decode(sig))
        # Verify against the declared generation when present, else try both.
        candidates = [kid] if kid in PUBS else list(PUBS.values())
        ok_with = None
        for pub in candidates:
            if openssl_verify(canon_path, sig_path, PUBS[pub]):
                ok_with = pub
                break
        if ok_with is None:
            print(f"FAIL {pid}: Ed25519 signature does not verify"); fails += 1
        else:
            if not entry.get('signed'):
                print(f"FAIL {pid}: signed file but registry says signed=false"); fails += 1
            if kid is not None and kid != ok_with:
                print(f"FAIL {pid}: key_id '{kid}' but signature verifies with '{ok_with}'"); fails += 1
for f in glob.glob(os.path.join(ROOT, 'playbooks', '*.playbook.json')):
    pid = os.path.basename(f)[: -len('.playbook.json')]
    if pid not in seen:
        print(f"FAIL {pid}: file not listed in registry.json"); fails += 1
print(f"CI VALIDATE: {len(reg['playbooks'])} entries, {fails} failures")
sys.exit(1 if fails else 0)
