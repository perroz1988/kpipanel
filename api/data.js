// GET /api/data?client=rs-italia|optimedia
//
// Emette JavaScript (const RS_DATA = ...;) leggendo i JSON dal bucket kpi-data.
// Le dashboard lo caricano con <script src="/api/data?client=..."></script>
// al posto dei vecchi blocchi embedded — i dati non vivono più nel repo.

import { createClient } from '@supabase/supabase-js';
import { jwtVerify } from 'jose';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);
const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET);

const CLIENTS = {
  'rs-italia': [
    ['RS_DATA',       'rs_data.json'],
    ['CREATIVE_DATA', 'creative_data.json'],
    ['CAMP_DATA',     'camp_data.json'],
    ['KEYE_DATA',     'keye_data.json'],
  ],
  'optimedia': [
    ['OPTIMEDIA_DATA', 'optimedia_data.json'],
  ],
};

function parseCookies(cookieHeader = '') {
  return Object.fromEntries(
    cookieHeader.split(';').map(c => {
      const idx = c.indexOf('=');
      return idx < 0 ? [c.trim(), ''] : [c.slice(0, idx).trim(), c.slice(idx + 1).trim()];
    })
  );
}

export default async function handler(req, res) {
  res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');

  const client = req.query.client;
  if (!CLIENTS[client]) {
    return res.status(400).send(`console.error('client non valido');`);
  }

  // auth: stesso cookie della dashboard; se non valido → redirect al login
  let user = null;
  const token = parseCookies(req.headers.cookie)['kpi_session'];
  if (token) {
    try {
      ({ payload: user } = await jwtVerify(token, JWT_SECRET));
    } catch { /* sessione scaduta */ }
  }
  if (!user || (user.role !== 'admin' && (user.dashboard ?? 'rs-italia') !== client)) {
    return res.status(200).send(`location.replace('/login');`);
  }

  const parts = [];
  for (const [name, file] of CLIENTS[client]) {
    const { data, error } = await supabase.storage.from('kpi-data').download(file);
    if (error) {
      return res.status(500).send(
        `console.error('Dati non disponibili: ${file} — ${(error.message ?? '').replace(/'/g, '')}');`
      );
    }
    parts.push(`const ${name} = ${await data.text()};`);
  }

  res.status(200).send(parts.join('\n\n'));
}
