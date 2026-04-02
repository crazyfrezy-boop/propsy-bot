import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SHEET_ID = os.getenv('SHEET_ID')
CALENDAR_EMAIL = os.getenv('CALENDAR_EMAIL')
PAYMENT_LINK = os.getenv('PAYMENT_LINK')

SUBSCRIPTION_PRICE = 20
TRIAL_DAYS = 14

WHITELIST = [
    123456789,  # Замени на Telegram ID Маргариты
]

def has_access(user_id: int) -> bool:
    return user_id in WHITELIST or db_check_subscription(user_id)