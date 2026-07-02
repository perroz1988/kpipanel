#!/usr/bin/env python3
"""
extract_embedded.py — Estrae i blocchi dati embedded dagli HTML e li carica
sul bucket kpi-data (seed iniziale per /api/data).

Uso:  python3 scripts/extract_embedded.py
"""

import os
import json
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


def extract_block(html, name):
    """Estrae il JSON di `const NAME = {...};` usando il bilanciamento del parser JSON."""
    marker = f'const {name} = '
    idx = html.find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    obj, _ = json.JSONDecoder().raw_decode(html[start:start + 3_000_000])
    return obj


def upload_json(remote_path, obj):
    body = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    url = f'{SUPABASE_URL}/storage/v1/object/kpi-data/{remote_path}'
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'Authorization': f'Bearer {SERVICE_KEY}',
        'apikey': SERVICE_KEY,
        'Content-Type': 'application/json',
        'x-upsert': 'true',
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        resp.read()
    print(f'  ✓ kpi-data/{remote_path}  ({len(body)//1024} KB)')


def main():
    with open(os.path.join(BASE, 'dashboard.html'), encoding='utf-8') as f:
        dash = f.read()
    with open(os.path.join(BASE, 'optimedia.html'), encoding='utf-8') as f:
        opt = f.read()

    print('Estrazione blocchi da dashboard.html...')
    for name, path in [('RS_DATA', 'rs_data.json'),
                       ('CREATIVE_DATA', 'creative_data.json'),
                       ('CAMP_DATA', 'camp_data.json'),
                       ('KEYE_DATA', 'keye_data.json')]:
        obj = extract_block(dash, name)
        if obj is None:
            print(f'  ✗ {name} non trovato')
        else:
            upload_json(path, obj)

    print('Estrazione blocchi da optimedia.html...')
    obj = extract_block(opt, 'OPTIMEDIA_DATA')
    if obj is None:
        print('  ✗ OPTIMEDIA_DATA non trovato')
    else:
        upload_json('optimedia_data.json', obj)


if __name__ == '__main__':
    main()
