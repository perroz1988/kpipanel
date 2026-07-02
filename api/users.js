// /api/users — gestione utenze (solo admin).
//
//   GET             lista utenti (senza hash password)
//   POST            crea utente        { email, name, password, role, dashboard }
//   PATCH           modifica utente    { id, name?, role?, dashboard?, is_active?, password? }
//   DELETE ?id=...  elimina utente (i log accessi restano, scollegati)

import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';
import { jwtVerify } from 'jose';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);
const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET);

const ROLES      = ['admin', 'viewer'];
const DASHBOARDS = ['rs-italia', 'optimedia'];
const FIELDS     = 'id,email,name,role,dashboard,is_active,created_at,last_login';

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
  const admin = await requireAdmin(req);
  if (!admin) return res.status(401).json({ error: 'Non autorizzato' });

  try {
    if (req.method === 'GET') {
      const { data, error } = await supabase.from('kpi_users')
        .select(FIELDS)
        .order('created_at', { ascending: true });
      if (error) throw new Error(error.message);
      return res.status(200).json({ users: data, me: admin.sub });
    }

    if (req.method === 'POST') {
      const { email, name, password, role = 'viewer', dashboard = 'rs-italia' } = req.body ?? {};
      if (!email?.trim() || !name?.trim() || !password)
        return res.status(400).json({ error: 'Email, nome e password sono obbligatori' });
      if (password.length < 8)
        return res.status(400).json({ error: 'Password: minimo 8 caratteri' });
      if (!ROLES.includes(role) || !DASHBOARDS.includes(dashboard))
        return res.status(400).json({ error: 'Ruolo o dashboard non validi' });

      const password_hash = await bcrypt.hash(password, 10);
      const { data, error } = await supabase.from('kpi_users')
        .insert({ email: email.toLowerCase().trim(), name: name.trim(), password_hash, role, dashboard })
        .select(FIELDS)
        .single();
      if (error) {
        const msg = error.message.includes('duplicate') ? 'Email già registrata' : error.message;
        return res.status(400).json({ error: msg });
      }
      return res.status(201).json({ user: data });
    }

    if (req.method === 'PATCH') {
      const { id, name, role, dashboard, is_active, password } = req.body ?? {};
      if (!id) return res.status(400).json({ error: 'id mancante' });
      if (id === admin.sub && (is_active === false || (role && role !== 'admin')))
        return res.status(400).json({ error: 'Non puoi disattivare o declassare il tuo account' });

      const patch = {};
      if (name?.trim()) patch.name = name.trim();
      if (role) {
        if (!ROLES.includes(role)) return res.status(400).json({ error: 'Ruolo non valido' });
        patch.role = role;
      }
      if (dashboard) {
        if (!DASHBOARDS.includes(dashboard)) return res.status(400).json({ error: 'Dashboard non valida' });
        patch.dashboard = dashboard;
      }
      if (typeof is_active === 'boolean') patch.is_active = is_active;
      if (password) {
        if (password.length < 8) return res.status(400).json({ error: 'Password: minimo 8 caratteri' });
        patch.password_hash = await bcrypt.hash(password, 10);
      }
      if (!Object.keys(patch).length) return res.status(400).json({ error: 'Nessuna modifica indicata' });

      const { data, error } = await supabase.from('kpi_users')
        .update(patch).eq('id', id).select(FIELDS).single();
      if (error) throw new Error(error.message);
      return res.status(200).json({ user: data });
    }

    if (req.method === 'DELETE') {
      const id = req.query.id;
      if (!id) return res.status(400).json({ error: 'id mancante' });
      if (id === admin.sub) return res.status(400).json({ error: 'Non puoi eliminare il tuo account' });

      // i log restano per audit (c'è la colonna email), ma vanno scollegati dalla FK
      await supabase.from('kpi_access_logs').update({ user_id: null }).eq('user_id', id);
      const { error } = await supabase.from('kpi_users').delete().eq('id', id);
      if (error) throw new Error(error.message);
      return res.status(200).json({ ok: true });
    }

    res.status(405).end();
  } catch (e) {
    res.status(500).json({ error: String(e.message ?? e) });
  }
}
