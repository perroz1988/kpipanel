#!/usr/bin/env python3
"""
migrate_to_supabase.py — Migrazione una tantum dell'archivio locale su Supabase Storage.

Carica:
  archive/**            → bucket kpi-archive (stessa struttura)
  inbox/** (file dati)  → bucket kpi-inbox
  rs_history.json       → bucket kpi-data (stato del motore)

Uso:  python3 scripts/migrate_to_supabase.py
"""

import os
import sys
import json
import mimetypes
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── .env ─────────────────────────────────────────────────────────────────────
def load_env():
    env = {}
    with open(os.path.join(BASE, '.env')) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

ENV = load_env()
SUPABASE_URL = ENV['SUPABASE_URL'].rstrip('/')
SERVICE_KEY  = ENV['SUPABASE_SERVICE_KEY']

SKIP_NAMES = {'.DS_Store', 'Icon\r', '.dropbox', 'LEGGI_QUI.txt'}
SKIP_EXT   = {'.png'}


def upload(bucket, remote_path, local_path):
    with open(local_path, 'rb') as f:
        body = f.read()
    ctype = mimetypes.guess_type(local_path)[0] or 'application/octet-stream'
    url = f'{SUPABASE_URL}/storage/v1/object/{bucket}/{urllib.request.quote(remote_path)}'
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'Authorization': f'Bearer {SERVICE_KEY}',
        'apikey': SERVICE_KEY,
        'Content-Type': ctype,
        'x-upsert': 'true',
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
        return True, len(body)
    except urllib.error.HTTPError as e:
        return False, e.read().decode()[:200]


def walk_upload(local_dir, bucket, prefix=''):
    n_ok = n_err = total = 0
    for root, dirs, files in os.walk(local_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in sorted(files):
            if name in SKIP_NAMES or os.path.splitext(name)[1].lower() in SKIP_EXT:
                continue
            lp = os.path.join(root, name)
            rel = os.path.relpath(lp, local_dir).replace(os.sep, '/')
            rp = f'{prefix}{rel}' if prefix else rel
            ok, info = upload(bucket, rp, lp)
            if ok:
                n_ok += 1; total += info
                print(f'  ✓ {bucket}/{rp}  ({info//1024} KB)')
            else:
                n_err += 1
                print(f'  ✗ {bucket}/{rp}  → {info}')
    return n_ok, n_err, total


def main():
    print('═' * 60)
    print('MIGRAZIONE ARCHIVIO → SUPABASE STORAGE')
    print('═' * 60)

    print('\n─ archive/ → kpi-archive')
    ok1, err1, tot1 = walk_upload(os.path.join(BASE, 'archive'), 'kpi-archive')

    print('\n─ inbox/ → kpi-inbox')
    ok2, err2, tot2 = walk_upload(os.path.join(BASE, 'inbox'), 'kpi-inbox')

    print('\n─ stato motore → kpi-data')
    ok3 = err3 = 0
    for state in ('rs_history.json', 'camp_history.json'):
        sp = os.path.join(BASE, state)
        if os.path.exists(sp):
            ok, info = upload('kpi-data', f'state/{state}', sp)
            if ok:
                ok3 += 1; print(f'  ✓ kpi-data/state/{state}')
            else:
                err3 += 1; print(f'  ✗ kpi-data/state/{state} → {info}')

    print('\n' + '═' * 60)
    print(f'Totale: {ok1+ok2+ok3} file caricati ({(tot1+tot2)//1024} KB), {err1+err2+err3} errori')
    if err1 + err2 + err3:
        sys.exit(1)


if __name__ == '__main__':
    main()
