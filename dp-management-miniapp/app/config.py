import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    bot_token = os.getenv("BOT_TOKEN", "")
    admin_id = int(os.getenv("ADMIN_ID", "0"))
    database_path = os.getenv("DATABASE_PATH", "./data/dp_management.db")
    timezone = os.getenv("TIMEZONE", "Asia/Dhaka")
    currency_code = os.getenv("CURRENCY_CODE", "BDT")
    currency_symbol = os.getenv("CURRENCY_SYMBOL", "৳")
    webapp_url = os.getenv("WEBAPP_URL", "")

settings = Settings()
