import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException
from app.config import settings

def verify_init_data(init_data: str):
    if not settings.bot_token:
        raise HTTPException(503, 'Bot token is not configured on the server.')
    if not init_data:
        raise HTTPException(401, 'Open this app from your private Telegram bot chat.')
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop('hash', None)
    if not received_hash:
        raise HTTPException(401, 'Telegram authentication data is missing.')
    check = '\n'.join(f'{k}={v}' for k, v in sorted(values.items()))
    secret = hmac.new(b'WebAppData', settings.bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(401, 'Telegram authentication could not be verified.')
    try:
        if time.time() - int(values.get('auth_date', '0')) > 86400:
            raise HTTPException(401, 'Telegram session expired. Reopen the Mini App.')
        user = json.loads(values['user'])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, 'Invalid Telegram authentication data.')
    if int(user.get('id', 0)) != settings.admin_id:
        raise HTTPException(403, 'This dashboard is restricted to the administrator.')
    return user

def admin_auth(x_telegram_init_data: str = Header(default='', alias='X-Telegram-Init-Data')):
    return verify_init_data(x_telegram_init_data)
