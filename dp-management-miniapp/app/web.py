from datetime import date
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.db import init_db, db_session
from app.auth import admin_auth
from app.config import settings

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title='DP Management Mini App')
app.mount('/assets', StaticFiles(directory=ROOT / 'web' / 'assets'), name='assets')

@app.on_event('startup')
def startup(): init_db()

@app.get('/')
def index(): return FileResponse(ROOT / 'web' / 'index.html')

@app.get('/api/me')
def me(admin=Depends(admin_auth)):
    return {'admin': admin, 'currency': settings.currency_symbol, 'currency_code': settings.currency_code}

class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    telegram_username: str = ''
    phone: str = ''
    notes: str = ''

class EntryIn(BaseModel):
    user_id: int
    amount: float = Field(gt=0)
    entry_date: str = Field(default_factory=lambda: date.today().isoformat())
    note: str = ''

@app.get('/api/dashboard')
def dashboard(admin=Depends(admin_auth)):
    today = date.today().isoformat(); month = today[:7]
    with db_session() as db:
        users = db.execute('SELECT COUNT(*) n FROM users WHERE is_active=1').fetchone()['n']
        today_dp = db.execute('SELECT COALESCE(SUM(amount),0) n FROM dp_entries WHERE entry_date=?',(today,)).fetchone()['n']
        month_dp = db.execute("SELECT COALESCE(SUM(amount),0) n FROM dp_entries WHERE substr(entry_date,1,7)=?",(month,)).fetchone()['n']
        month_bonus = db.execute("SELECT COALESCE(SUM(amount),0) n FROM bonuses WHERE substr(bonus_date,1,7)=?",(month,)).fetchone()['n']
    return {'users':users,'today_dp':today_dp,'month_dp':month_dp,'month_bonus':month_bonus}

@app.get('/api/users')
def users(admin=Depends(admin_auth)):
    with db_session() as db: return [dict(r) for r in db.execute('SELECT * FROM users ORDER BY name COLLATE NOCASE')]

@app.post('/api/users')
def add_user(data: UserIn, admin=Depends(admin_auth)):
    with db_session() as db:
        cur=db.execute('INSERT INTO users(name,telegram_username,phone,notes) VALUES(?,?,?,?)',(data.name.strip(),data.telegram_username,data.phone,data.notes))
        db.execute("INSERT INTO audit_logs(action,entity,entity_id) VALUES('create','user',?)",(cur.lastrowid,))
        return {'id':cur.lastrowid}

@app.post('/api/dp')
def add_dp(data: EntryIn, admin=Depends(admin_auth)):
    with db_session() as db:
        if not db.execute('SELECT id FROM users WHERE id=? AND is_active=1',(data.user_id,)).fetchone(): raise HTTPException(404,'User not found.')
        count=db.execute('SELECT COUNT(*) n FROM dp_entries WHERE user_id=? AND entry_date=?',(data.user_id,data.entry_date)).fetchone()['n']
        if count >= 5: raise HTTPException(400,'Maximum 5 DP transactions per user per day.')
        cur=db.execute('INSERT INTO dp_entries(user_id,amount,entry_date,note) VALUES(?,?,?,?)',(data.user_id,data.amount,data.entry_date,data.note))
        db.execute("INSERT INTO audit_logs(action,entity,entity_id,details) VALUES('create','dp_entry',?,?)",(cur.lastrowid,f'user={data.user_id}; amount={data.amount}'))
        return {'id':cur.lastrowid}

@app.get('/api/dp')
def dp_entries(month: str='', admin=Depends(admin_auth)):
    with db_session() as db:
        rows=db.execute("SELECT d.*,u.name FROM dp_entries d JOIN users u ON u.id=d.user_id WHERE (?='' OR substr(d.entry_date,1,7)=?) ORDER BY d.entry_date DESC,d.id DESC",(month,month))
        return [dict(r) for r in rows]

@app.post('/api/bonuses')
def add_bonus(data: EntryIn, admin=Depends(admin_auth)):
    with db_session() as db:
        if not db.execute('SELECT id FROM users WHERE id=?',(data.user_id,)).fetchone(): raise HTTPException(404,'User not found.')
        cur=db.execute('INSERT INTO bonuses(user_id,amount,bonus_date,note) VALUES(?,?,?,?)',(data.user_id,data.amount,data.entry_date,data.note))
        db.execute("INSERT INTO audit_logs(action,entity,entity_id,details) VALUES('create','bonus',?,?)",(cur.lastrowid,f'user={data.user_id}; amount={data.amount}'))
        return {'id':cur.lastrowid}

@app.get('/api/bonuses')
def bonuses(month: str='', admin=Depends(admin_auth)):
    with db_session() as db:
        rows=db.execute("SELECT b.*,u.name FROM bonuses b JOIN users u ON u.id=b.user_id WHERE (?='' OR substr(b.bonus_date,1,7)=?) ORDER BY b.bonus_date DESC,b.id DESC",(month,month))
        return [dict(r) for r in rows]

@app.get('/api/inactive')
def inactive(admin=Depends(admin_auth)):
    month=date.today().strftime('%Y-%m')
    with db_session() as db:
        rows=db.execute("SELECT u.id,u.name,COALESCE(SUM(d.amount),0) month_dp,MAX(d.entry_date) last_dp FROM users u LEFT JOIN dp_entries d ON d.user_id=u.id AND substr(d.entry_date,1,7)=? WHERE u.is_active=1 GROUP BY u.id ORDER BY month_dp ASC,u.name",(month,))
        return [dict(r) for r in rows]

@app.post('/api/contact')
def add_contact(data: dict, admin=Depends(admin_auth)):
    with db_session() as db:
        db.execute('INSERT INTO contact_logs(user_id,contact_date,status,note) VALUES(?,?,?,?)',(int(data['user_id']),data.get('contact_date',date.today().isoformat()),data.get('status','contacted'),data.get('note','')))
    return {'ok':True}

@app.get('/api/contacts')
def contacts(admin=Depends(admin_auth)):
    with db_session() as db:
        rows=db.execute('SELECT c.*,u.name FROM contact_logs c JOIN users u ON u.id=c.user_id ORDER BY c.contact_date DESC,c.id DESC')
        return [dict(r) for r in rows]

@app.get('/api/audit')
def audit(admin=Depends(admin_auth)):
    with db_session() as db: return [dict(r) for r in db.execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200')]
