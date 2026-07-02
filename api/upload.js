// POST /api/upload — genera una signed upload URL per il bucket kpi-inbox.
// Il browser carica poi il file direttamente su Supabase Storage (nessun
// limite di body Vercel). Solo admin.
//
// Body JSON: { dest: 'rs-italia' | 'rs-creative' | 'optimedia/Facebook' |
//                    'optimedia/Instagram' | 'optimedia/LinkedIn',
//              filename: 'nome originale.xls' }
// Risposta:  { url, path }

import { createClient } from '@supabase/supabase-js';
import { jwtVerify } from 'jose';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);
const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET);

const DESTS = {
  'rs-italia':           f => `rs-italia/${f}`,
  'rs-creative':         f => f,                       // root inbox (creative performance)
  'optimedia/Facebook':  f => `optimedia/Facebook/${f}`,
  'optimedia/Instagram': f => `optimedia/Instagram/${f}`,
  'optimedia/LinkedIn':  f => `optimedia/LinkedIn/${f}`,
};

function parseCookies(cookieHeader = '') {
  return Object.fromEntries(
    cookieHeader.split(';').map(c => {
      const idx = c.indexOf('=');
      return idx < 0 ? [c.trim(), ''] : [c.slice(0, idx).trim(), c.slice(idx + 1).trim()];
    })
  );
}

async function requireAdmin(req) {
  const token = parseCookies(req.headers.cookie)['kpi_session'];
  if (!token) return null;
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return payload.role === 'admin' ? payload : null;
  } catch {
    return null;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const user = await requireAdmin(req);
  if (!user) return res.status(401).json({ error: 'Non autorizzato' });

  const { dest, filename } = req.body ?? {};
  if (!DESTS[dest]) return res.status(400).json({ error: `Destinazione non valida: ${dest}` });

  // niente path traversal / caratteri strani
  const safe = String(filename ?? '').replace(/[/\\]/g, '').trim();
  if (!safe || safe.startsWith('.')) return res.status(400).json({ error: 'Nome file non valido' });

  const path = DESTS[dest](safe);

  // se esiste già, rimuovilo (upsert non è supportato dalle signed upload URL)
  await supabase.storage.from('kpi-inbox').remove([path]);

  const { data, error } = await supabase.storage
    .from('kpi-inbox')
    .createSignedUploadUrl(path);

  if (error) return res.status(500).json({ error: error.message });

  res.status(200).json({ url: data.signedUrl, path: data.path });
}
