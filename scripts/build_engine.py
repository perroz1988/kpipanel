#!/usr/bin/env python3
"""
build_engine.py — Genera api/_lib/engine.py a partire da update.py.

update.py resta la fonte unica di verità (e continua a funzionare in locale).
Questo script applica le trasformazioni per l'ambiente Vercel:
  - BASE su /tmp/kpi (filesystem effimero, scrivibile)
  - le funzioni che iniettano JSON negli HTML scrivono invece
    file JSON in BASE/out/ (poi caricati sul bucket kpi-data)
  - niente argv/sys.exit/git: main() diventa run(...)

Rilanciare dopo ogni modifica a update.py:
  python3 scripts/build_engine.py
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(BASE, 'update.py')
DST  = os.path.join(BASE, 'api', '_lib', 'engine.py')

REPLACEMENTS = [

# ── header ───────────────────────────────────────────────────────────────────
(
'''update.py — Aggiorna le dashboard KPI (RS Italia + Optimedia).''',
'''engine.py — Motore KPI per Vercel (GENERATO da update.py — non modificare a mano).

Rigenerare con:  python3 scripts/build_engine.py

Differenze rispetto a update.py locale:
  - BASE = /tmp/kpi (popolato da api/process.py con il sync dai bucket)
  - output → JSON in BASE/out/ invece di iniezione negli HTML
  - entry point: run(skip_keye=..., only_rs=..., only_opt=...)''',
),

# ── BASE su /tmp + helper output ────────────────────────────────────────────
(
'''BASE = os.path.dirname(os.path.abspath(__file__))''',
'''BASE = os.environ.get('KPI_BASE') or '/tmp/kpi'
OUT  = os.path.join(BASE, 'out')


def _write_out(name, obj):
    """Scrive un output JSON in BASE/out/ (poi caricato sul bucket kpi-data)."""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))''',
),

# ── update_dashboard → JSON ──────────────────────────────────────────────────
(
'''def update_dashboard(rs_data):
    """Sostituisce il blocco const RS_DATA = {...}; nel dashboard.html."""
    with open(DASHBOARD, 'r', encoding='utf-8') as f:
        html = f.read()

    start_marker = 'const RS_DATA = '
    end_marker   = '\\n\\nconst KEYE_DATA'

    start_idx = html.find(start_marker)
    end_idx   = html.find(end_marker, start_idx)

    if start_idx == -1 or end_idx == -1:
        print('ERRORE: marcatori RS_DATA / KEYE_DATA non trovati in dashboard.html')
        return False

    new_json = json.dumps(rs_data, ensure_ascii=False)
    new_html = html[:start_idx] + start_marker + new_json + ';' + html[end_idx:]

    with open(DASHBOARD, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return True''',
'''def update_dashboard(rs_data):
    """Salva RS_DATA in out/rs_data.json (servito da /api/data)."""
    _write_out('rs_data.json', rs_data)
    return True''',
),

# ── update_keye_data: coda → JSON ───────────────────────────────────────────
(
'''    keye_data = keye_from_export(raw)
    keye_json = json.dumps(keye_data, ensure_ascii=False)

    with open(DASHBOARD, 'r', encoding='utf-8') as f:
        html = f.read()

    start_marker = '\\n\\nconst KEYE_DATA = '
    end_marker   = ';\\n\\n/* ============ FORMATTERS'


    start_idx = html.find(start_marker)
    end_idx   = html.find(end_marker, start_idx)

    if start_idx == -1 or end_idx == -1:
        print('  ERRORE: marcatori KEYE_DATA non trovati.')
        return False

    new_html = html[:start_idx] + '\\n\\nconst KEYE_DATA = ' + keye_json + html[end_idx:]

    with open(DASHBOARD, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return True''',
'''    keye_data = keye_from_export(raw)
    _write_out('keye_data.json', keye_data)
    return True''',
),

# ── update_creative_data → JSON ──────────────────────────────────────────────
(
'''def update_creative_data(creatives):
    """Sostituisce il blocco CREATIVE_DATA nel dashboard.html."""
    with open(DASHBOARD, 'r', encoding='utf-8') as f:
        html = f.read()
    marker = 'const CREATIVE_DATA = '
    idx = html.find(marker)
    if idx < 0:
        return False

    # Trova il ; che chiude il blocco CREATIVE_DATA
    semi_idx = html.find(';', idx + len(marker))
    if semi_idx < 0:
        return False

    # Verifica che sia seguito da const CAMP_DATA (con newline variabili)
    after_semi = html[semi_idx+1:semi_idx+100]
    if 'const CAMP_DATA' not in after_semi:
        return False

    # Trova dove inizia const CAMP_DATA
    camp_idx = html.find('const CAMP_DATA', semi_idx)
    if camp_idx < 0:
        return False

    # Sostituisci il contenuto di CREATIVE_DATA (tra marker e ;)
    # Mantieni tutto fino al ; e poi fino a const CAMP_DATA
    new_html = (html[:idx] +
                marker +
                json.dumps(creatives, ensure_ascii=False) +
                html[semi_idx:camp_idx])  # Il ; più i newline
    new_html += html[camp_idx:]  # const CAMP_DATA in poi

    with open(DASHBOARD, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return True''',
'''def update_creative_data(creatives):
    """Salva CREATIVE_DATA in out/creative_data.json."""
    _write_out('creative_data.json', creatives)
    return True''',
),

# ── update_camp_data → JSON ──────────────────────────────────────────────────
(
'''def update_camp_data(camp_data):
    """Aggiunge / sostituisce il blocco CAMP_DATA nel dashboard.html."""
    with open(DASHBOARD, 'r', encoding='utf-8') as f:
        html = f.read()

    new_json     = json.dumps(camp_data, ensure_ascii=False)
    start_marker = '\\n\\nconst CAMP_DATA = '
    end_marker   = ';\\n\\nconst KEYE_DATA'

    if start_marker in html:
        # Aggiorna il blocco esistente
        s = html.find(start_marker)
        e = html.find(end_marker, s)
        if e == -1:
            print('  ERRORE: fine CAMP_DATA non trovata.')
            return False
        new_html = html[:s] + start_marker + new_json + html[e:]
    else:
        # Prima volta: inserisce prima di KEYE_DATA
        keye_marker = '\\n\\nconst KEYE_DATA'
        idx = html.find(keye_marker)
        if idx == -1:
            print('  ERRORE: KEYE_DATA non trovato nel dashboard.')
            return False
        # Assicura che CREATIVE_DATA sia inserito prima di CAMP_DATA
        creative_marker = '\\n\\nconst CREATIVE_DATA = '
        if creative_marker not in html[:idx]:
            html = html[:idx] + creative_marker + '[];\\n' + html[idx:]
            idx = html.find(keye_marker)
        new_html = html[:idx] + start_marker + new_json + ';' + html[idx:]

    with open(DASHBOARD, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return True''',
'''def update_camp_data(camp_data):
    """Salva CAMP_DATA in out/camp_data.json."""
    _write_out('camp_data.json', camp_data)
    return True''',
),

# ── update_optimedia_dashboard → JSON ────────────────────────────────────────
(
'''def update_optimedia_dashboard(data):
    """Sostituisce OPTIMEDIA_DATA in optimedia.html."""
    with open(DASHBOARD_OPT, 'r', encoding='utf-8') as f:
        html = f.read()
    marker = 'const OPTIMEDIA_DATA = '
    end    = ';\\n'
    idx = html.find(marker)
    if idx < 0:
        print('  ERRORE: OPTIMEDIA_DATA non trovato in optimedia.html')
        return False
    end_idx = html.find(end, idx + len(marker))
    if end_idx < 0:
        print('  ERRORE: fine OPTIMEDIA_DATA non trovata')
        return False
    new_block = marker + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + end
    html = html[:idx] + new_block + html[end_idx + len(end):]
    with open(DASHBOARD_OPT, 'w', encoding='utf-8') as f:
        f.write(html)
    return True''',
'''def update_optimedia_dashboard(data):
    """Salva OPTIMEDIA_DATA in out/optimedia_data.json."""
    _write_out('optimedia_data.json', data)
    return True''',
),

# ── segreti Keye → env var (il repo è pubblico!) ─────────────────────────────
(
'''KEYE_API_KEY     = '3bf7abb472ff1acf31e3e10a19a8779184bc22ba59de91e2'  # legacy
KEYE_COOKIE      = 'kpi6-session=kpi6-secret-2026\'''',
'''KEYE_API_KEY     = os.environ.get('KEYE_API_KEY', '')
KEYE_COOKIE      = os.environ.get('KEYE_COOKIE', '')''',
),

# ── main() → run(...) senza argv ─────────────────────────────────────────────
(
'''def main():
    for d in [ARCHIVE, ARCHIVE_KEYE, INBOX_RS, INBOX_OPT_FB, INBOX_OPT_IG,
              ARCHIVE_OPT_FB, ARCHIVE_OPT_IG, ARCHIVE_OPT_ADS]:
        os.makedirs(d, exist_ok=True)

    args         = sys.argv[1:]
    skip_keye    = '--no-keye'   in args
    skip_inbox   = '--no-inbox'  in args
    only_rs      = '--rs-only'   in args
    only_opt     = '--opt-only'  in args
    args = [a for a in args if a not in ('--no-keye','--no-inbox','--keye','--rs-only','--opt-only')]

    if args:
        print('Uso: python3 update.py [--no-keye] [--no-inbox] [--rs-only] [--opt-only]')
        sys.exit(1)

    run_rs  = not only_opt
    run_opt = not only_rs''',
'''def run(skip_keye=False, skip_inbox=False, only_rs=False, only_opt=False):
    for d in [ARCHIVE, ARCHIVE_KEYE, INBOX_RS, INBOX_OPT_FB, INBOX_OPT_IG,
              ARCHIVE_OPT_FB, ARCHIVE_OPT_IG, ARCHIVE_OPT_ADS, OUT]:
        os.makedirs(d, exist_ok=True)

    run_rs  = not only_opt
    run_opt = not only_rs''',
),

# ── niente sys.exit dentro il flusso RS ──────────────────────────────────────
(
'''            if not run_opt:
                sys.exit(1)''',
'''            if not run_opt:
                return''',
),

# ── niente deploy git ────────────────────────────────────────────────────────
(
'''    print(f'\\n✓ Fatto.')
    data_max = datetime.now().strftime('%Y-%m-%d')
    if run_rs and 'rs_data' in dir():
        data_max = rs_data['meta'].get('data_max', data_max)

    commit_msg = f'Update dati: {data_max}'
    print(f'\\nDeploy automatico...')
    try:
        files_to_add = ['dashboard.html', 'rs_history.json', 'optimedia.html']
        subprocess.run(['git', 'add'] + files_to_add, cwd=BASE, check=True)
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE)
        if result.returncode != 0:
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=BASE, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE, check=True)
            print(f'  Deploy ✓  →  {commit_msg}')
        else:
            print('  Nessuna modifica da deployare.')
    except subprocess.CalledProcessError as e:
        print(f'  Deploy WARN: {e}')


if __name__ == '__main__':
    main()''',
'''    print(f'\\n✓ Fatto.')


if __name__ == '__main__':
    run()''',
),
]


def main():
    with open(SRC, encoding='utf-8') as f:
        code = f.read()

    for i, (old, new) in enumerate(REPLACEMENTS):
        n = code.count(old)
        if n != 1:
            print(f'✗ Trasformazione #{i+1}: trovate {n} occorrenze (attesa 1).')
            print(f'  update.py è cambiato in un punto critico — aggiorna build_engine.py.')
            print(f'  Inizio blocco: {old[:80]!r}')
            sys.exit(1)
        code = code.replace(old, new)

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f'✓ Generato {os.path.relpath(DST, BASE)} ({len(code)//1024} KB)')


if __name__ == '__main__':
    main()
