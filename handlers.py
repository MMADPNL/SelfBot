# =========================================================
# handlers.py
# Telegram Bot Handlers
# =========================================================

from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
)

from config import OWNER_ID
from database import (
    create_user,
    get_diamonds,
    get_coins,
    is_bot_enabled,
)

from admin_panel import admin_panel


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user:
        return

    create_user(
        user.id,
        user.username,
        user.first_name
    )

    await update.message.reply_text(
        "🤖 خوش آمدید\n\n"
        "🎮 ربات بازی آماده است.\n\n"
        "دستورها:\n"
        "/profile - پروفایل\n"
        "/balance - موجودی"
    )


# =========================================================
# PROFILE
# =========================================================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user:
        return

    create_user(
        user.id,
        user.username,
        user.first_name
    )

    diamonds = get_diamonds(user.id)
    coins = get_coins(user.id)

    await update.message.reply_text(
        "👤 پروفایل\n\n"
        f"🆔 ID: {user.id}\n"
        f"👤 نام: {user.first_name}\n\n"
        f"💎 الماس: {diamonds}\n"
        f"🪙 سکه: {coins}"
    )


# =========================================================
# BALANCE
# =========================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user:
        return

    await update.message.reply_text(
        f"💎 الماس: {get_diamonds(user.id)}\n"
        f"🪙 سکه: {get_coins(user.id)}"
    )


# =========================================================
# ADMIN COMMAND
# =========================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user:
        return

    if user.id != OWNER_ID:

        await update.message.reply_text(
            "⛔ دسترسی ندارید."
        )

        return

    await admin_panel(
        update,
        context
    )


# =========================================================
# BOT CHECK
# =========================================================

async def check_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_bot_enabled():

        await update.message.reply_text(
            "🔴 ربات موقتاً خاموش است."
        )

        return False

    return True


# =========================================================
# REGISTER
# =========================================================

def register_handlers(application):

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "profile",
            profile
        )
    )

    application.add_handler(
        CommandHandler(
            "balance",
            balance
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin
        )
  )
