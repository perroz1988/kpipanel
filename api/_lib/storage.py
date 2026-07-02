"""
storage.py — Client minimale Supabase Storage (REST, solo stdlib).

Bucket:
  kpi-inbox    ← file caricati da upload.html, in attesa di elaborazione
  kpi-archive  ← archivio storico (specchio di archive/ locale)
  kpi-data     ← output del motore (rs_data.json, ...) + state/ (rs_history.json)
"""

import os
import json
import mimetypes
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor

SUPABASE_URL = os.environ['SUPABASE_URL'].rstrip('/')
SERVICE_KEY  = os.environ['SUPABASE_SERVICE_KEY']

_WORKERS = 8


def _req(method, path, body=None, headers=None):
    url = f'{SUPABASE_URL}{path}'
    h = {'Authorization': f'Bearer {SERVICE_KEY}', 'apikey': SERVICE_KEY}
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode('utf-8')
            h['Content-Type'] = 'application/json'
        else:
            data = body
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _quote(path):
    return urllib.parse.quote(path)


def list_files(bucket, prefix=''):
    """Lista ricorsiva: ritorna i path (relativi al bucket) di tutti i file sotto prefix."""
    out = []
    offset = 0
    while True:
        raw = _req('POST', f'/storage/v1/object/list/{bucket}', {
            'prefix': prefix,
            'limit': 100,
            'offset': offset,
            'sortBy': {'column': 'name', 'order': 'asc'},
        })
        items = json.loads(raw)
        for it in items:
            full = f"{prefix}/{it['name']}" if prefix else it['name']
            if it.get('id') is None:          # cartella → ricorsione
                out.extend(list_files(bucket, full))
            else:
                out.append(full)
        if len(items) < 100:
            break
        offset += 100
    return out


def download(bucket, path):
    return _req('GET', f'/storage/v1/object/{bucket}/{_quote(path)}')


def upload(bucket, path, data, content_type=None):
    ctype = content_type or mimetypes.guess_type(path)[0] or 'application/octet-stream'
    _req('POST', f'/storage/v1/object/{bucket}/{_quote(path)}', body=data,
         headers={'Content-Type': ctype, 'x-upsert': 'true'})


def delete(bucket, paths):
    if paths:
        _req('DELETE', f'/storage/v1/object/{bucket}', {'prefixes': paths})


def download_tree(bucket, prefixes, dest_dir):
    """Scarica in parallelo tutti i file sotto i prefix indicati dentro dest_dir.
    Ritorna l'insieme dei path remoti scaricati."""
    remote = []
    for p in prefixes:
        remote.extend(list_files(bucket, p))

    def _one(rp):
        lp = os.path.join(dest_dir, rp)
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        with open(lp, 'wb') as f:
            f.write(download(bucket, rp))

    with ThreadPoolExecutor(_WORKERS) as ex:
        list(ex.map(_one, remote))
    return set(remote)


def upload_tree(bucket, pairs):
    """Carica in parallelo. pairs = [(local_path, remote_path), ...]"""
    def _one(pair):
        lp, rp = pair
        with open(lp, 'rb') as f:
            upload(bucket, rp, f.read())

    with ThreadPoolExecutor(_WORKERS) as ex:
        list(ex.map(_one, pairs))
