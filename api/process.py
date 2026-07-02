"""
process.py — Endpoint POST /api/process: esegue il motore KPI su Vercel.

Flusso:
  1. auth: cookie kpi_session con role=admin
  2. sync giù:   kpi-inbox → /tmp/kpi/inbox, kpi-archive → /tmp/kpi/archive,
                 kpi-data/state/* → /tmp/kpi/
  3. engine.run(...)  (porting di update.py — vedi scripts/build_engine.py)
  4. sync su:    nuovi file archivio → kpi-archive, file inbox processati
                 rimossi da kpi-inbox, out/*.json → kpi-data,
                 rs_history/camp_history → kpi-data/state/

Query string:
  ?client=rs-italia | optimedia | all   (default all)
  ?no_keye=1                            salta il fetch Keye
"""

import io
import os
import sys
import json
import shutil
import traceback
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import storage                      # noqa: E402
from _lib.auth import verify_session          # noqa: E402

KPI_BASE = '/tmp/kpi'

STATE_FILES = ('rs_history.json', 'camp_history.json')


def _walk(root):
    """Set di path relativi (con /) di tutti i file sotto root."""
    out = set()
    for r, _dirs, files in os.walk(root):
        for name in files:
            out.add(os.path.relpath(os.path.join(r, name), root).replace(os.sep, '/'))
    return out


def _run(client, skip_keye):
    only_rs  = client == 'rs-italia'
    only_opt = client == 'optimedia'

    # ── reset workspace ──────────────────────────────────────────
    shutil.rmtree(KPI_BASE, ignore_errors=True)
    os.makedirs(KPI_BASE, exist_ok=True)

    # ── sync giù ─────────────────────────────────────────────────
    if only_rs:
        inbox_prefixes, archive_prefixes = ['rs-italia', ''], ['rs-italia']
    elif only_opt:
        inbox_prefixes, archive_prefixes = ['optimedia'], ['optimedia']
    else:
        inbox_prefixes, archive_prefixes = [''], ['rs-italia', 'optimedia']

    print('Sync da Supabase Storage...')
    # nota: prefix '' scarica tutto il bucket (i CSV creative stanno nella root inbox)
    if '' in inbox_prefixes:
        inbox_prefixes = ['']
    remote_inbox = storage.download_tree('kpi-inbox', inbox_prefixes,
                                         os.path.join(KPI_BASE, 'inbox'))
    remote_archive = storage.download_tree('kpi-archive', archive_prefixes,
                                           os.path.join(KPI_BASE, 'archive'))
    for state in STATE_FILES:
        try:
            data = storage.download('kpi-data', f'state/{state}')
            with open(os.path.join(KPI_BASE, state), 'wb') as f:
                f.write(data)
        except Exception:
            pass  # primo run: stato assente
    print(f'  inbox: {len(remote_inbox)} file · archivio: {len(remote_archive)} file')

    # ── motore ───────────────────────────────────────────────────
    from _lib import engine
    engine.run(skip_keye=skip_keye, only_rs=only_rs, only_opt=only_opt)

    # ── sync su ──────────────────────────────────────────────────
    print('\nSync verso Supabase Storage...')

    # 1. nuovi file in archivio
    local_archive = _walk(os.path.join(KPI_BASE, 'archive'))
    new_archive = sorted(local_archive - remote_archive)
    storage.upload_tree('kpi-archive',
                        [(os.path.join(KPI_BASE, 'archive', p), p) for p in new_archive])
    for p in new_archive:
        print(f'  + kpi-archive/{p}')

    # 2. file finiti in _trash → conservati in kpi-archive/_trash/
    trash_dir = os.path.join(KPI_BASE, '_trash')
    if os.path.isdir(trash_dir):
        trash = sorted(_walk(trash_dir))
        storage.upload_tree('kpi-archive',
                            [(os.path.join(trash_dir, p), f'_trash/{p}') for p in trash])

    # 3. file inbox processati (spostati via dal motore) → rimossi dal bucket
    local_inbox = _walk(os.path.join(KPI_BASE, 'inbox'))
    consumed = sorted(remote_inbox - local_inbox)
    storage.delete('kpi-inbox', consumed)
    for p in consumed:
        print(f'  − kpi-inbox/{p}')

    # 4. output → kpi-data
    out_dir = os.path.join(KPI_BASE, 'out')
    outputs = sorted(_walk(out_dir)) if os.path.isdir(out_dir) else []
    storage.upload_tree('kpi-data',
                        [(os.path.join(out_dir, p), p) for p in outputs])
    for p in outputs:
        print(f'  ↑ kpi-data/{p}')

    # 5. stato motore → kpi-data/state/
    state_pairs = [(os.path.join(KPI_BASE, s), f'state/{s}') for s in STATE_FILES
                   if os.path.exists(os.path.join(KPI_BASE, s))]
    storage.upload_tree('kpi-data', state_pairs)

    return {
        'archived': new_archive,
        'consumed': consumed,
        'outputs': outputs,
    }


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        user = verify_session(self.headers.get('Cookie'))
        if not user or user.get('role') != 'admin':
            return self._json(401, {'ok': False, 'error': 'Non autorizzato'})

        qs = parse_qs(urlparse(self.path).query)
        client    = (qs.get('client') or ['all'])[0]
        skip_keye = (qs.get('no_keye') or ['0'])[0] == '1'

        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                result = _run(client, skip_keye)
            self._json(200, {'ok': True, 'log': buf.getvalue(), **result})
        except Exception as e:
            self._json(500, {
                'ok': False,
                'error': str(e),
                'log': buf.getvalue(),
                'trace': traceback.format_exc()[-3000:],
            })

    def do_GET(self):
        self._json(405, {'ok': False, 'error': 'Usa POST'})

    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)
