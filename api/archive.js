// /api/archive — consultazione dei bucket (solo admin).
//
//   GET    /api/archive?bucket=kpi-archive            lista ricorsiva dei file
//   GET    /api/archive?bucket=kpi-archive&download=<path>
//                                                     → { url } (signed URL 5 min)
//   DELETE /api/archive?bucket=kpi-inbox&path=<path>  elimina un file (solo kpi-inbox)

import { createClient } from '@supabase/supabase-js';
import { jwtVerify } from 'jose';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);
const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET);

const BUCKETS = ['kpi-inbox', 'kpi-archive', 'kpi-data'];

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

async function listRecursive(bucket, prefix = '') {
  const out = [];
  let offset = 0;
  for (;;) {
    const { data, error } = await supabase.storage.from(bucket)
      .list(prefix, { limit: 100, offset, sortBy: { column: 'name', order: 'asc' } });
    if (error) throw new Error(error.message);
    for (const item of data) {
      const full = prefix ? `${prefix}/${item.name}` : item.name;
      if (item.id === null) {
        out.push(...await listRecursive(bucket, full));
      } else {
        out.push({
          path: full,
          size: item.metadata?.size ?? 0,
          updated: item.updated_at ?? item.created_at ?? null,
        });
      }
    }
    if (data.length < 100) break;
    offset += 100;
  }
  return out;
}

export default async function handler(req, res) {
  const user = await requireAdmin(req);
  if (!user) return res.status(401).json({ error: 'Non autorizzato' });

  const bucket = req.query.bucket ?? 'kpi-archive';
  if (!BUCKETS.includes(bucket)) return res.status(400).json({ error: 'Bucket non valido' });

  try {
    if (req.method === 'GET' && req.query.download) {
      const { data, error } = await supabase.storage.from(bucket)
        .createSignedUrl(req.query.download, 300, { download: true });
      if (error) return res.status(404).json({ error: error.message });
      return res.status(200).json({ url: data.signedUrl });
    }

    if (req.method === 'GET') {
      const files = await listRecursive(bucket);
      return res.status(200).json({ bucket, files });
    }

    if (req.method === 'DELETE') {
      if (bucket !== 'kpi-inbox') {
        return res.status(403).json({ error: 'Eliminazione consentita solo su kpi-inbox' });
      }
      const path = req.query.path;
      if (!path) return res.status(400).json({ error: 'path mancante' });
      const { error } = await supabase.storage.from(bucket).remove([path]);
      if (error) return res.status(500).json({ error: error.message });
      return res.status(200).json({ ok: true });
    }

    res.status(405).end();
  } catch (e) {
    res.status(500).json({ error: String(e.message ?? e) });
  }
}
