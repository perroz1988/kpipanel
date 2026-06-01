// Uso: node --env-file=.env scripts/add_user.js email@example.com "Nome Cognome" password [role]
// role: admin (default) | viewer
import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';

const [,, email, name, password, role = 'admin'] = process.argv;

if (!email || !name || !password) {
  console.error('Uso: node --env-file=.env scripts/add_user.js <email> "<nome>" <password> [role]');
  process.exit(1);
}

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);
const password_hash = await bcrypt.hash(password, 12);

const { error } = await supabase.from('kpi_users').insert({
  email: email.toLowerCase().trim(),
  name: name.trim(),
  password_hash,
  role: role.trim()
});

if (error) {
  console.error('Errore:', error.message);
  process.exit(1);
}

console.log(`✓ Utente creato: ${name} <${email}> [role: ${role}]`);
