# Guida Aggiornamento Settimanale — Optimedia KPI Dashboard

**Frequenza**: ogni lunedì mattina  
**Tempo stimato**: 15–20 minuti  
**Prerequisiti**: accesso a Meta Business Suite, LinkedIn Analytics, Meta Ads Manager

---

## 1. SCARICA I FILE

### Instagram (Meta Business Suite)
Vai su [business.facebook.com](https://business.facebook.com) → Account Instagram Optimedia → Insights → Export

Scarica i seguenti CSV (periodo: ultimi 28 giorni o settimana corrente):

| File da scaricare | Nome atteso | Dove salvare |
|---|---|---|
| Reach giornaliera | `Reach.csv` | `inbox/optimedia/Instagram/` |
| Visualizzazioni | `Views.csv` | `inbox/optimedia/Instagram/` |
| Interazioni | `Interactions.csv` | `inbox/optimedia/Instagram/` |
| Nuovi follower | `Follows.csv` | `inbox/optimedia/Instagram/` |
| Commenti | `Comments.csv` | `inbox/optimedia/Instagram/` |
| Salvataggi | `Saves.csv` | `inbox/optimedia/Instagram/` |
| Audience | `Audience IG.csv` | `inbox/optimedia/Instagram/` |

### Facebook (Meta Business Suite)
Stesso account → Insights Facebook → Export

| File da scaricare | Nome atteso | Dove salvare |
|---|---|---|
| Views | `Views.csv` | `inbox/optimedia/Facebook/` |
| Viewers (reach) | `Viewers.csv` | `inbox/optimedia/Facebook/` |
| Interazioni | `Interactions.csv` | `inbox/optimedia/Facebook/` |
| Clic sul link | `Link clicks.csv` | `inbox/optimedia/Facebook/` |
| Visite pagina | `Visits.csv` | `inbox/optimedia/Facebook/` |
| Nuovi follower | `Follows.csv` | `inbox/optimedia/Facebook/` |
| Audience | `Audience FB.csv` | `inbox/optimedia/Facebook/` |

### LinkedIn
Vai su LinkedIn Company Admin → Analytics → Contenuti / Follower / Visitatori → Export XLS

| File da scaricare | Dove salvare |
|---|---|
| Metriche contenuti (XLS) | `inbox/optimedia/LinkedIn/` |
| Follower analytics (XLS) | `inbox/optimedia/LinkedIn/` |
| Visite pagina (XLS, opzionale) | `inbox/optimedia/LinkedIn/` |

### Meta Ads Manager — Campagne Paid (quando attive)
> **Importante**: scarica SOLO se ci sono campagne attive (Target Building, Engagement Boost, etc.)

Vai su Ads Manager → Reports → Tabella giorno per giorno → Export CSV

Requisiti del CSV:
- **Breakdown**: Giorno
- **Colonne obbligatorie**: Giorno, Copertura, Impression, Importo speso (EUR), Clic sul link, Interazione con la Pagina, Follower di Instagram, Reazioni al post, Salvataggi del post, Condivisioni del post, ThruPlay

| Nome file (qualsiasi) | Dove salvare |
|---|---|
| `Meta-Ads-Performance-*.csv` | `inbox/optimedia/Instagram/` |

> Il file viene rilevato automaticamente perché ha un nome diverso dai CSV standard di Instagram.  
> Puoi caricare file cumulativi che coprono più settimane: l'ultimo file caricato sovrascrive i dati per data.

---

## 2. STRUTTURA INBOX (riepilogo)

```
inbox/optimedia/
├── Instagram/
│   ├── Reach.csv
│   ├── Views.csv
│   ├── Interactions.csv
│   ├── Follows.csv
│   ├── Comments.csv
│   ├── Saves.csv
│   ├── Audience IG.csv
│   └── Meta-Ads-Performance-*.csv   ← Ads Manager (opzionale, quando attivo)
├── Facebook/
│   ├── Views.csv
│   ├── Viewers.csv
│   ├── Interactions.csv
│   ├── Link clicks.csv
│   ├── Visits.csv
│   ├── Follows.csv
│   └── Audience FB.csv
└── LinkedIn/
    ├── *_metrics.xls (o xlsx)
    ├── *_followers.xls
    └── *_visits.xls (opzionale)
```

---

## 3. ESEGUI L'UPDATE

```bash
cd '/Users/francescoperrotta/Dropbox/Fannel_Design/ClaudePrj/KPI Dashboard'
python3 update.py --no-keye
```

> Ometti `--no-keye` se vuoi aggiornare anche i dati brand monitoring (RS Italia).

**Output atteso:**

```
══════════════════════════════════════════════════
OPTIMEDIA
══════════════════════════════════════════════════

Inbox Optimedia...
  Facebook/Reach.csv → 2026-06-10_reach.csv
  Instagram/Reach.csv → 2026-06-10_reach.csv
  Instagram Ads/Meta-Ads-Performance-*.csv → 2026-06-10_Meta-Ads-Performance-*.csv
  LinkedIn/...xls → 2026-06-10_...xls

Aggiornamento optimedia.html...
  Periodo:   2026-02-12 → 2026-06-10
  Facebook:  123,000 views · 400 int · ER 0.32%
  Instagram: 90,000 reach · 650 int · ER 0.72%
  LinkedIn:  14,000 impressioni · 4500 clicks · ER full 76% · ER react 8.5%
  OPTIMEDIA_DATA ✓

✓ Fatto.
Deploy automatico...
  Deploy ✓ → Update dati: 2026-06-10
```

Se vedi `OPTIMEDIA WARN: ...` — qualcosa è andato storto. Vedi sezione **Troubleshooting**.

---

## 4. VERIFICA LA DASHBOARD

Apri [optimedia.html su Vercel](https://kpipanel.vercel.app/optimedia) oppure `optimedia.html` in locale.

### Tab Overview
- [ ] Spike callout mostra "Campagna Paid W21" (non "organico virale")
- [ ] La data "Ultimo aggiornamento" è quella di oggi
- [ ] KPI cross-platform mostrano numeri > 0

### Tab Analisi Settimanale
- [ ] W21 (18–23 mag) ha il flag ⚡ paid
- [ ] W23 (1–7 giu) ha il flag 🌱+⚡ misto
- [ ] I dati delle settimane recenti sono aggiornati

### Tab LinkedIn
- [ ] Metriche aggregate (impressioni, reactions, clicks) aggiornate
- [ ] Grafico crescita follower mostra barre
- [ ] Demographics (paesi, funzioni, seniority) mostrano dati

### Tab KPI Tracker
- [ ] Intestazione mostra "Mese 4/12" (o il mese corretto)
- [ ] Instagram: Reach Organica usa target CAGM progressivo (~3.358 per giu '26), NON 5.200
- [ ] LinkedIn: due card ER — "ER Full (LinkedIn)" e "ER Reactions (organico)"
- [ ] Facebook: ER Organica esclude W21 (nota "⚡ ER calcolata escludendo W21")
- [ ] Tutti i target mostrano il mese corrente, non il target finale Feb 2027

---

## 5. COME FUNZIONA IL SISTEMA (per riferimento)

### Archiviazione
Ogni file in `inbox/` viene copiato in `archive/optimedia/[platform]/` con prefisso data (`YYYY-MM-DD_`).  
Dopo la copia, il file originale viene **eliminato** dall'inbox.

```
archive/optimedia/
├── facebook/   ← CSV metriche FB (una serie per metrica)
├── instagram/  ← CSV metriche IG (una serie per metrica)
├── linkedin/   ← XLS LinkedIn (tutti i file dello stesso caricamento)
└── ads/        ← CSV Meta Ads Manager (aggregati ITA+FR per data)
```

### Logica "ultimo file vince"
Per ogni data, se ci sono più file che coprono la stessa data (es. carichi la stessa settimana due volte), **l'ultimo file caricato vince**.  
Questo evita il doppio conteggio. Se noti dati duplicati, rimuovi i file in `archive/` con la data problematica e ricarica.

### Split organico/paid
Le metriche Instagram da Business Suite includono tutto (organico + paid).  
Il CSV di Meta Ads Manager contiene solo il contributo paid.  
Il KPI Tracker calcola: **organico = totale − paid**.

### CAGM targets (Feb 2026 → Feb 2027)
I target nel KPI Tracker **non** sono i valori finali (Feb 2027), ma il milestone mensile progressivo:

| Mese | IG Reach target | IG Follower target |
|------|----------------|--------------------|
| Mar '26 (n=1) | 2.851 | 17 |
| Apr '26 (n=2) | 3.011 | 20 |
| Mag '26 (n=3) | 3.179 | 23 |
| **Giu '26 (n=4)** | **3.358** | **26** |
| … | … | … |
| Feb '27 (n=12) | 5.200 | 80 |

---

## 6. TROUBLESHOOTING

### "OPTIMEDIA WARN: name 'csv' is not defined"
**Causa**: Manca import. **Fix**: Verifica che `import csv` sia presente in cima a `update.py`.

### "OPTIMEDIA WARN: [Errno 2] No such file or directory"
**Causa**: La cartella archive non esiste. **Fix**: Esegui `python3 update.py` una volta — crea le cartelle automaticamente.

### Spike callout mostra ancora "organico virale"
**Causa**: Cache browser. **Fix**: Hard refresh (Cmd+Shift+R).

### KPI Tracker mostra target troppo alti (prossimi a Feb 2027)
**Causa**: La funzione `getMonthlyTarget()` non trova i dati CAGM nel JSON.  
**Diagnostica**: Apri DevTools console → `OPTIMEDIA_DATA.meta.cagm_monthly.instagram.reach_organica[3]` → deve mostrare ~3358.  
**Fix**: Riesegui `python3 update.py --no-keye` per rigenerare il JSON.

### LinkedIn demographics mostrano "undefined"
**Causa**: Campo `name` non trovato nell'XLS. Verifica che il file XLS LinkedIn sia il "Follower analytics" corretto (non il CSV).

### Ads CSV non viene archiviato
**Causa**: Il nome del file coincide con uno dei nomi standard di Instagram (`Reach.csv`, `Views.csv`, etc.).  
**Fix**: Rinomina il file Ads Manager con un nome distinto (es. `Meta-Ads-Performance-GIU26.csv`) prima di metterlo nell'inbox.

### Dati ads non appaiono nel KPI Tracker
**Causa**: Nessun file in `archive/optimedia/ads/`.  
**Check**: `ls archive/optimedia/ads/` — deve avere file `.csv`.  
**Fix**: Metti il CSV Ads Manager in `inbox/optimedia/Instagram/` e riesegui `update.py`.

### Doppio conteggio in una settimana
**Causa**: Due file con dati sovrapposti in archive.  
**Fix**: Elimina il file più vecchio da `archive/optimedia/[platform]/` e riesegui.

---

## 7. COMANDI UTILI

```bash
# Aggiornamento standard
python3 update.py --no-keye

# Aggiornamento completo (include brand monitoring RS Italia)
python3 update.py

# Verifica cosa c'è negli archivi
ls -la archive/optimedia/ads/
ls -la archive/optimedia/instagram/

# Guarda le ultime modifiche
git log --oneline -5

# In caso di errore — vedi l'output completo
python3 update.py --no-keye 2>&1 | tee /tmp/update_log.txt
```

---

**Versione**: 2.0 — Giugno 2026  
**Aggiornata per**: split organico/paid, CAGM targets, LinkedIn ER doppio, flag settimane paid
