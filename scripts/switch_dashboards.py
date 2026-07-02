#!/usr/bin/env python3
"""
switch_dashboards.py — Migrazione una tantum: sostituisce i blocchi dati
embedded in dashboard.html / optimedia.html con uno <script src="/api/data">.

Da quel momento i dati vivono nel bucket kpi-data (aggiornati da /api/process)
e gli HTML non cambiano più a ogni aggiornamento dati.
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def switch_rs():
    path = os.path.join(BASE, 'dashboard.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()

    if '/api/data?client=rs-italia' in html:
        print('dashboard.html: già migrato, skip')
        return

    rs_idx = html.find('const RS_DATA = ')
    assert rs_idx > 0, 'RS_DATA non trovato'
    script_idx = html.rfind('<script>', 0, rs_idx)
    assert script_idx > 0, '<script> di apertura non trovato'

    end_marker = ';\n\n/* ============ FORMATTERS'
    end_idx = html.find(end_marker, rs_idx)
    assert end_idx > 0, 'fine KEYE_DATA non trovata'

    new = ('<script src="/api/data?client=rs-italia"></script>\n'
           '<script>\n'
           '/* ============ DATI: RS_DATA, CREATIVE_DATA, CAMP_DATA, KEYE_DATA\n'
           '   caricati da /api/data (bucket kpi-data, aggiornati da /api/process) */')
    html = html[:script_idx] + new + html[end_idx + 1:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'dashboard.html: migrato ({len(html)//1024} KB)')


def switch_opt():
    path = os.path.join(BASE, 'optimedia.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()

    if '/api/data?client=optimedia' in html:
        print('optimedia.html: già migrato, skip')
        return

    opt_idx = html.find('const OPTIMEDIA_DATA = ')
    assert opt_idx > 0, 'OPTIMEDIA_DATA non trovato'
    script_idx = html.rfind('<script>', 0, opt_idx)
    assert script_idx > 0, '<script> di apertura non trovato'

    end_idx = html.find(';\n', opt_idx)
    assert end_idx > 0, 'fine OPTIMEDIA_DATA non trovata'

    new = ('<script src="/api/data?client=optimedia"></script>\n'
           '<script>\n'
           '/* ============ DATI: OPTIMEDIA_DATA\n'
           '   caricati da /api/data (bucket kpi-data, aggiornati da /api/process) */')
    html = html[:script_idx] + new + html[end_idx + 1:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'optimedia.html: migrato ({len(html)//1024} KB)')


if __name__ == '__main__':
    switch_rs()
    switch_opt()
