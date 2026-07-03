#!/usr/bin/env python3
"""
gen_demo_labels.py — Genera in update.py il blocco DEMO_* con la mappa
EN→IT delle etichette demografiche LinkedIn (l'export cambia lingua con
l'interfaccia; lo storico della dashboard è in italiano).

Le coppie sono dichiarate qui in forma "approssimata": lo script risolve
la stringa italiana ESATTA (apostrofi tipografici inclusi) contro un
followers XLS italiano di riferimento, così i refusi sono impossibili.

Uso:  python3 scripts/gen_demo_labels.py
"""

import os
import re
import sys
import xlrd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_XLS = os.path.join(BASE, 'archive', 'rs-italia', 'linkedin', '2026-06-27_followers.xls')
TARGET  = os.path.join(BASE, 'update.py')

MARK_START = '# ── DEMO LABELS EN→IT (GENERATO da scripts/gen_demo_labels.py — non editare) ──'
MARK_END   = '# ── FINE DEMO LABELS ──'

# (EN, IT approssimato) — l'IT viene risolto contro l'XLS di riferimento
ANZIANITA = [
    ('Entry', 'Livello base'), ('Senior', 'Senior'), ('Manager', 'Amministratore'),
    ('Director', 'Direttore'), ('Owner', 'Proprietario'), ('CXO', 'CXO'),
    ('VP', 'Vicepresidente'), ('Training', 'Training'), ('Unpaid', 'Non retribuito'),
    ('Partner', 'Partner'),
]

FUNZIONE = [
    ('Sales', 'Vendite'), ('Operations', 'Operazioni'), ('Engineering', 'Ingegneria'),
    ('Business Development', 'Business Development'), ('Information Technology', 'Informatica'),
    ('Purchasing', 'Acquisti'), ('Marketing', 'Marketing'),
    ('Program and Project Management', 'Program e Project Management'),
    ('Customer Success and Support', 'Assistenza'), ('Administrative', 'Amministrativo'),
    ('Human Resources', 'Risorse umane'), ('Arts and Design', 'Arte e design'),
    ('Media and Communication', 'Media e comunicazione'), ('Research', 'Ricerca'),
    ('Education', 'Formazione'), ('Quality Assurance', 'Controllo qualità'),
    ('Finance', 'Finanza'), ('Accounting', 'Contabilità'),
    ('Community and Social Services', 'Comunità e servizi sociali'),
    ('Product Management', 'Product Management'), ('Real Estate', 'Immobiliare'),
    ('Consulting', 'Consulenza'), ('Entrepreneurship', 'Imprenditorialità'),
    ('Legal', 'Legale'), ('Military and Protective Services', 'Servizio militare e di protezione'),
    ('Healthcare Services', 'Sanità'),
]

SETTORE = [
    ('Appliances, Electrical, and Electronics Manufacturing', 'Fabbricazione di apparecchi elettrici, materiali elettrici e componenti elettronici'),
    ('Industrial Machinery Manufacturing', 'Fabbricazione di macchinari industriali'),
    ('Machinery Manufacturing', 'Produzione di macchinari'),
    ('Automation Machinery Manufacturing', 'Fabbricazione di macchinari di automazione'),
    ('IT Services and IT Consulting', 'Servizi IT e consulenza IT'),
    ('Transportation, Logistics, Supply Chain and Storage', 'Trasporti, logistica, supply chain e stoccaggio'),
    ('Business Consulting and Services', 'Consulenza e servizi aziendali'),
    ('Motor Vehicle Manufacturing', 'Fabbricazione di autoveicoli'),
    ('Wholesale', "Vendita all'ingrosso"),
    ('Utilities', 'Servizi pubblici'),
    ('Construction', 'Edilizia'),
    ('Manufacturing', 'Industria manifatturiera'),
    ('Oil and Gas', 'Petrolio e gas'),
    ('Pharmaceutical Manufacturing', 'Fabbricazione di prodotti farmaceutici'),
    ('Software Development', 'Sviluppo di software'),
    ('Medical Equipment Manufacturing', 'Fabbricazione di apparecchiature medicali'),
    ('Retail', 'Vendita al dettaglio'),
    ('Food and Beverage Manufacturing', 'Fabbricazione di prodotti alimentari e bevande'),
    ('Defense and Space Manufacturing', 'Fabbricazione di apparecchiature per il settore spaziale e della difesa'),
    ('Telecommunications', 'Telecomunicazioni'),
    ('Advertising Services', 'Servizi pubblicitari'),
    ('Truck Transportation', 'Trasporto su strada'),
    ('Chemical Manufacturing', 'Fabbricazione di prodotti chimici'),
    ('Electrical Equipment Manufacturing', 'Fabbricazione di apparecchiature elettriche'),
    ('Higher Education', 'Istruzione superiore'),
    ('Retail Office Equipment', 'Vendita al dettaglio di attrezzature per ufficio'),
    ('Plastics Manufacturing', 'Fabbricazione di materie plastiche'),
    ('Aviation and Aerospace Component Manufacturing', 'Fabbricazione di componenti per il settore aeronautico e aerospaziale'),
    ('Government Administration', 'Pubblica amministrazione'),
    ('Semiconductor Manufacturing', 'Fabbricazione di semiconduttori'),
    ('Research Services', 'Servizi di ricerca'),
    ('Computers and Electronics Manufacturing', 'Fabbricazione di computer e apparecchiature elettroniche'),
    ('Environmental Services', 'Servizi ambientali'),
    ('International Trade and Development', 'Commercio internazionale e sviluppo'),
    ('Mining', 'Attività minerarie'),
    ('Packaging and Containers Manufacturing', 'Fabbricazione di materiali da imballaggio e contenitori'),
    ('Renewable Energy Equipment Manufacturing', 'Produzione attrezzature energie rinnovabili'),
    ('Human Resources Services', 'Servizi risorse umane'),
    ('Engineering Services', 'Servizi ingegneristici'),
    ('Hospitals and Health Care', 'Ospedali e strutture sanitarie'),
    ('Facilities Services', 'Servizi infrastrutturali'),
    ('Railroad Equipment Manufacturing', 'Fabbricazione di attrezzature ferroviarie'),
    ('Financial Services', 'Servizi finanziari'),
    ('Food and Beverage Services', 'Servizi per la ristorazione'),
    ('Civil Engineering', 'Ingegneria civile'),
    ('Staffing and Recruiting', 'Selezione e ricerca di personale'),
    ('Wholesale Building Materials', "Vendita all'ingrosso di materiali da costruzione"),
    ('Banking', 'Settore bancario'),
    ('Technology, Information and Internet', 'Tecnologia, informazioni e internet'),
    ('Textile Manufacturing', 'Produzione tessile'),
    ('Furniture and Home Furnishings Manufacturing', 'Fabbricazione di mobili e arredi per la casa'),
    ('Design Services', 'Servizi di progettazione'),
    ('Motor Vehicle Parts Manufacturing', 'Fabbricazione di parti per autoveicoli'),
    ('Professional Training and Coaching', 'Coaching e formazione professionale'),
    ('Metalworking Machinery Manufacturing', 'Fabbricazione di macchinari per la lavorazione dei metalli'),
    ('Engines and Power Transmission Equipment Manufacturing', 'Fabbricazione di motori e apparecchiature per la trasmissione di potenza'),
    ('Book and Periodical Publishing', 'Editoria: libri e pubblicazioni periodiche'),
    ('Printing Services', 'Servizi di stampa'),
    ('Airlines and Aviation', 'Linee aeree e aviazione'),
    ('Accounting', 'Contabilità'),
    ('Freight and Package Transportation', 'Trasporto di merci e pacchi'),
    ('Retail Apparel and Fashion', 'Vendita al dettaglio di abbigliamento e moda'),
    ('Shipbuilding', 'Cantieri navali'),
    ('Wholesale Machinery', "Vendita all'ingrosso di macchinari"),
    ('Maritime Transportation', 'Trasporto marittimo'),
    ('Security and Investigations', 'Sicurezza e investigazioni'),
    ('Real Estate', 'Immobiliare'),
    ('Rail Transportation', 'Trasporto ferroviario'),
    ('Architecture and Planning', 'Architettura e pianificazione'),
    ('Measuring and Control Instrument Manufacturing', 'Fabbricazione di strumenti di misurazione e controllo'),
    ('Wholesale Motor Vehicles and Parts', "Vendita all'ingrosso di autoveicoli e relative parti"),
    ('Insurance', 'Assicurazioni'),
    ('Marketing Services', 'Servizi di marketing'),
    ('Computer and Network Security', 'Sicurezza informatica e delle reti'),
    ('Non-profit Organizations', 'Organizzazioni senza scopo di lucro'),
    ('Hospitality', 'Settore alberghiero'),
    ('Internet Marketplace Platforms', 'Piattaforme di e-commerce'),
    ('Metal Valve, Ball, and Roller Manufacturing', 'Fabbricazione di valvole metalliche, sfere e rulli'),
    ('Consumer Services', 'Servizi ai consumatori'),
    ('Restaurants', 'Ristoranti'),
    ('Travel Arrangements', 'Organizzazione di viaggi'),
    ('Steam and Air-Conditioning Supply', 'Fornitura di vapore e aria condizionata'),
    ('Wellness and Fitness Services', 'Servizi benessere e fitness'),
    ('Biotechnology Research', 'Ricerca biotecnologica'),
    ('Paint, Coating, and Adhesive Manufacturing', 'Fabbricazione di vernici, rivestimenti e adesivi'),
    ('Events Services', 'Servizi per eventi'),
    ('Services for Renewable Energy', 'Servizi per energie rinnovabili'),
    ('Law Practice', 'Studio legale'),
    ('Computer Hardware Manufacturing', 'Fabbricazione di hardware per computer'),
    ('Beverage Manufacturing', 'Produzione di bevande'),
    ('Personal Care Product Manufacturing', 'Fabbricazione di prodotti per la cura personale'),
    ('Solar Electric Power Generation', 'Produzione di energia elettrica solare'),
    ('Medical Practices', 'Studi medici'),
    ('Public Relations and Communications Services', 'Pubbliche Relazioni e servizi di comunicazione'),
    ('Credit Intermediation', 'Intermediazione creditizia'),
    ('Retail Art Supplies', 'Vendita al dettaglio di materiali artistici'),
    ('Agriculture, Construction, Mining Machinery Manufacturing', "Fabbricazione di macchinari per l'agricoltura, l'edilizia e l'industria mineraria"),
    ('Wholesale Import and Export', "Importazione ed esportazione all'ingrosso"),
    ('Spectator Sports', 'Sport professionistici'),
    ('Farming', 'Agricoltura'),
]


def norm(s):
    """Chiave di confronto: minuscole, apostrofi unificati, spazi compressi."""
    return re.sub(r'\s+', ' ', s.replace('’', "'").strip().lower())


def load_it_labels():
    wb = xlrd.open_workbook(REF_XLS)
    out = {}
    for cat, sheet in [('anzianita', 'Anzianità'), ('funzione', 'Funzione lavorativa'),
                       ('settore', 'Settore'), ('localita', 'Località')]:
        s = wb.sheet_by_name(sheet)
        out[cat] = [str(s.row_values(r)[0]).strip() for r in range(1, s.nrows) if s.row_values(r)[0]]
    return out


def resolve(pairs, it_labels, cat):
    """Risolve gli IT approssimati contro le stringhe esatte dell'XLS di riferimento."""
    exact = {norm(l): l for l in it_labels}
    resolved, errors, used = {}, [], set()
    for en, it_approx in pairs:
        key = norm(it_approx)
        if key not in exact:
            errors.append(f'  {cat}: IT non trovato per {en!r} → {it_approx!r}')
            continue
        if key in used:
            errors.append(f'  {cat}: IT duplicato {it_approx!r}')
            continue
        used.add(key)
        resolved[en] = exact[key]
    missing_it = [l for l in it_labels if norm(l) not in used]
    return resolved, errors, missing_it


def main():
    it = load_it_labels()
    all_maps, all_errors = {}, []

    for cat, pairs in [('anzianita', ANZIANITA), ('funzione', FUNZIONE), ('settore', SETTORE)]:
        resolved, errors, missing = resolve(pairs, it[cat], cat)
        all_maps[cat] = resolved
        all_errors += errors
        print(f'{cat}: {len(resolved)}/{len(pairs)} coppie risolte · IT non coperti: {len(missing)}')
        for m in missing[:6]:
            print(f'    (senza EN) {m!r}')

    if all_errors:
        print('\nERRORI:')
        print('\n'.join(all_errors))
        sys.exit(1)

    # dict unico: le etichette sono disgiunte tra categorie tranne pochi casi
    # identici in entrambe le lingue (Senior, CXO, Marketing…) che mappano su sé stessi
    merged = {}
    for cat in ('anzianita', 'funzione', 'settore'):
        for en, itl in all_maps[cat].items():
            if en in merged and merged[en] != itl:
                print(f'CONFLITTO: {en!r} → {merged[en]!r} vs {itl!r}')
                sys.exit(1)
            merged[en] = itl

    lines = [MARK_START]
    lines.append('DEMO_LABELS_EN_IT = {')
    for en, itl in merged.items():
        if en != itl:  # identiche → inutile mapparle
            lines.append(f'    {en!r}: {itl!r},')
    lines.append('}')
    lines.append(MARK_END)
    block = '\n'.join(lines)

    with open(TARGET, encoding='utf-8') as f:
        code = f.read()

    if MARK_START in code:
        pre  = code[:code.find(MARK_START)]
        post = code[code.find(MARK_END) + len(MARK_END):]
        code = pre + block + post
    else:
        anchor = '# ─── PARSER XLS ─'
        i = code.find(anchor)
        assert i > 0, 'anchor PARSER XLS non trovato'
        code = code[:i] + block + '\n\n\n' + code[i:]

    with open(TARGET, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f'\n✓ Blocco DEMO_LABELS_EN_IT ({len([1 for k,v in merged.items() if k!=v])} voci) scritto in update.py')


if __name__ == '__main__':
    main()
