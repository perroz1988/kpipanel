# Product

## Register

product

## Clienti Attivi

| Cliente | Dashboard | URL | Fonti dati |
|---|---|---|---|
| RS Italia | `dashboard.html` | `/rs-italia` | LinkedIn XLS + Campaign Manager CSV + Keye API |
| Optimedia | `optimedia.html` | `/optimedia` | Meta Business Suite (Facebook + Instagram CSV) |

## Users

**RS Italia** — Team marketing e comunicazione (1–3 persone). Review settimanale KPI LinkedIn: impressioni, engagement, crescita follower, campagne Krein, brand listening Keye. Contesto: scrivania, schermo normale, luce diurna. Obiettivo: capire in meno di 2 minuti cosa è successo e se la settimana è andata meglio o peggio della precedente.

**Optimedia** — Team social media (1–2 persone). Monitoraggio mensile/settimanale performance Facebook e Instagram. Focus su reach, interazioni, ER cross-platform, crescita follower, spike virali.

## Product Purpose

Piattaforma multi-tenant di reportistica social. Aggrega dati da export manuali (LinkedIn XLS, Meta CSV) e API (Keye brand listening) in dashboard HTML standalone, aggiornabili con `python3 update.py`. Zero infrastruttura: gira in localhost, si deploya su Vercel, l'accesso è protetto da autenticazione JWT su Supabase.

**Successo:** ogni team legge i KPI in meno di 2 minuti e sa se il periodo è andato meglio o peggio del precedente.

## Auth & Multi-tenant

- Login: `/login` → redirect automatico alla dashboard del cliente basato sul campo `dashboard` nel JWT
- RS Italia users → `/rs-italia`
- Optimedia users → `/optimedia`
- Gestione utenti: `node --env-file=.env scripts/add_user.js <email> <nome> <password> <role> <dashboard>`

## Brand Personality

Preciso, affidabile, discreto. Il tool scompare dietro i dati — non attira attenzione su sé stesso.

## Anti-references

- Glassmorphism e blur decorativi
- Gradiente sul testo
- UI che clona l'estetica dei social network (LinkedIn blue, Instagram gradient come brand del tool)
- SaaS dashboard generiche con hero-metric template
- Dark mode: il contesto è diurno, light è la scelta giusta

## Design Principles

1. **I dati parlano, il chrome tace.** Ogni elemento di interfaccia deve guadagnarsi il posto. Se rimuovendolo i dati diventano più leggibili, va rimosso.
2. **Confronto al primo sguardo.** Il delta vs periodo precedente deve essere percepibile senza leggere — colore, freccia, posizione; non solo testo.
3. **Densità senza claustrofobia.** Dashboard pro: tante informazioni, ma con ritmo visivo che permette di respirare.
4. **Consistenza operativa.** Ogni KPI si comporta allo stesso modo: stesso pattern label / valore / prev / delta.
5. **Standalone senza infrastruttura.** Il file gira in localhost senza build step. Le scelte di design devono restare implementabili in HTML/CSS vanilla.

## Accessibility & Inclusion

WCAG AA come target minimo. Colore non è l'unico indicatore di stato (frecce ↑↓ affiancano sempre pos/neg). Testo body 14px minimo, label 11–12px.
