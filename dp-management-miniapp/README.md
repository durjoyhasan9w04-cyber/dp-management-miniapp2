# DP Management Mini App

Admin-only Telegram Mini App starter for DP and bonus tracking.

## Included
- Telegram Web App HMAC authentication restricted to `ADMIN_ID`
- Mobile-first dashboard and navigation
- User creation and directory
- Daily DP entry with a hard limit of five entries per user per day
- Bonus entry and history
- Monthly DP/bonus dashboard totals
- Monthly no-DP / activity list
- Contact history endpoint and audit log foundation
- SQLite database outside source control

## Setup
1. Copy `.env.example` to `.env`.
2. Set a freshly rotated Telegram bot token, admin ID, and public HTTPS Mini App URL.
3. Install: `pip install -r requirements.txt`
4. Run: `python main.py`
5. Configure the Telegram bot's Mini App URL using BotFather.

## HOKAS
Set the startup command to `python main.py`. Use port `80` if required by the host, or the provided `PORT` environment variable. Configure secrets in the host environment panel. Store `DATABASE_PATH` on persistent storage.

## Security and scope
Never commit `.env`, database files, backups, or customer exports. This is a clean first implementation, not yet the complete production feature set: editing/deleting records, Excel exports, archive workflows, richer inactivity categories, and comprehensive audit views still need to be implemented and tested before replacing a live system. No existing database is imported automatically.
