import os

# اطلاعات Telegram API را از GitHub Secrets می‌خوانیم
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# شماره اکانت فقط برای ورود اولیه استفاده می‌شود
PHONE = os.getenv("PHONE", "")

# نام فایل Session
SESSION_NAME = os.getenv("SESSION_NAME", "selfbot")

# تنظیمات عمومی
PREFIX = "."
