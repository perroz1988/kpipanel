"""
auth.py — Verifica del JWT di sessione (cookie kpi_session, HS256).
Controparte Python di api/auth/verify.js.
"""

import os
import json
import hmac
import base64
import hashlib
import time


def _b64d(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def verify_session(cookie_header):
    """Ritorna il payload del JWT se il cookie kpi_session è valido, altrimenti None."""
    cookies = {}
    for part in (cookie_header or '').split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            cookies[k.strip()] = v.strip()
    token = cookies.get('kpi_session')
    if not token or token.count('.') != 2:
        return None
    try:
        head, payload_b64, sig = token.split('.')
        expected = hmac.new(
            os.environ['JWT_SECRET'].encode('utf-8'),
            f'{head}.{payload_b64}'.encode('utf-8'),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _b64d(sig)):
            return None
        payload = json.loads(_b64d(payload_b64))
        if payload.get('exp') and payload['exp'] < time.time():
            return None
        return payload
    except Exception:
        return None
