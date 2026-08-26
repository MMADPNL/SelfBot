import os
import re
import sqlite3
import random
import logging
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

DB_FILE = "bot.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER NOT NULL DEFAULT 0,
            referred_by INTEGER,
            referral_rewarded INTEGER NOT NULL DEFAULT 0,
            service_until TEXT
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            message_id INTEGER,
            owner_id INTEGER NOT NULL,
            opponent_id INTEGER,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()


def ensure_user(user):
    con = get_db()

    con.execute("""
        INSERT INTO users(user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    con.commit()
    con.close()


def get_balance(user_id):
    con = get_db()

    row = con.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    con.close()

    return row["balance"] if row else 0


def add_balance(user_id, amount):
    con = get_db()

    con.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, user_id)
    )

    con.commit()
    con.close()


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔌 فعالسازی سلف",
                callback_data="activate"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 موجودی",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "🔄 انتقال",
                callback_data="transfer"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 زیرمجموعه گیری",
                callback_data="referral"
            )
        ],

        [
            InlineKeyboardButton(
                "🔴 خاموش سلف",
                callback_data="self_off"
            ),
            InlineKeyboardButton(
                "🟢 روشن سلف",
                callback_data="self_on"
            )
        ],

    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    ensure_user(user)

    # referral
    if context.args:

        try:
            referrer_id = int(context.args[0])

            if referrer_id != user.id:

                con = get_db()

                current = con.execute(
                    "SELECT referred_by FROM users WHERE user_id=?",
                    (user.id,)
                ).fetchone()

                referrer = con.execute(
                    "SELECT user_id FROM users WHERE user_id=?",
                    (referrer_id,)
                ).fetchone()

                if (
                    referrer
                    and current
                    and current["referred_by"] is None
                ):

                    con.execute(
                        "UPDATE users SET referred_by=? WHERE user_id=?",
                        (referrer_id, user.id)
                    )

                    con.execute(
                        "UPDATE users SET balance=balance+70 WHERE user_id=?",
                        (referrer_id,)
                    )

                    con.commit()

                con.close()

        except Exception:
            pass

    await update.message.reply_text(
        "🤖 منوی اصلی\n\n"
        "یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# PANEL
# =========================================================

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    ensure_user(update.effective_user)

    await update.effective_message.reply_text(
        "👑 پنل",
        reply_markup=main_menu()
    )


# =========================================================
# CALLBACK MENU
# =========================================================

async def menu_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    ensure_user(user)

    data = query.data

    # -----------------------------------------------------
    # BALANCE
    # -----------------------------------------------------

    if data == "balance":

        balance = get_balance(user.id)

        await query.message.reply_text(
            f"💰 موجودی شما:\n\n"
            f"💎 {balance} الماس"
        )

    # -----------------------------------------------------
    # TRANSFER
    # -----------------------------------------------------

    elif data == "transfer":

        await query.message.reply_text(
            "🔄 انتقال الماس\n\n"
            "در گروه روی پیام شخص ریپلای کن:\n\n"
            "انتقال 100\n"
            "یا\n"
            "انتقال ۱۰۰\n\n"
            "با آیدی هم می‌توانی:\n"
            "انتقال 100 @username"
        )

    # -----------------------------------------------------
    # REFERRAL
    # -----------------------------------------------------

    elif data == "referral":

        bot = await context.bot.get_me()

        link = (
            f"https://t.me/{bot.username}"
            f"?start={user.id}"
        )

        await query.message.reply_text(
            "👥 زیرمجموعه‌گیری\n\n"
            "لینک اختصاصی شما:\n"
            f"{link}\n\n"
            "🎁 پاداش هر زیرمجموعه:\n"
            "💎 ۷۰ الماس"
        )

    # -----------------------------------------------------
    # ACTIVATION
    # -----------------------------------------------------

    elif data == "activate":

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "۱۵ روزه — ۵۰۰ 💎",
                    callback_data="buy:15:500"
                )
            ],

            [
                InlineKeyboardButton(
                    "۳۰ روزه — ۱۰۲۰ 💎",
                    callback_data="buy:30:1020"
                )
            ],

            [
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="close"
                )
            ]

        ])

        await query.message.reply_text(
            "🔌 انتخاب سرویس:",
            reply_markup=keyboard
        )

    # -----------------------------------------------------
    # BUY
    # -----------------------------------------------------

    elif data.startswith("buy:"):

        _, days, price = data.split(":")

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "✅ بله",
                    callback_data=f"confirm:{days}:{price}"
                ),

                InlineKeyboardButton(
                    "❌ نه",
                    callback_data="close"
                )
            ]

        ])

        await query.message.reply_text(
            f"آیا از خرید سلف {days} روزه "
            f"به مبلغ {price} 💎 مطمئنید؟",
            reply_markup=keyboard
        )

    # -----------------------------------------------------
    # CONFIRM
    # -----------------------------------------------------

    elif data.startswith("confirm:"):

        _, days, price = data.split(":")

        days = int(days)
        price = int(price)

        balance = get_balance(user.id)

        if balance < price:

            await query.message.reply_text(
                "❌ موجودی الماس کافی نیست."
            )

        else:

            con = get_db()

            row = con.execute(
                "SELECT service_until FROM users WHERE user_id=?",
                (user.id,)
            ).fetchone()

            now = datetime.now(timezone.utc)

            if row and row["service_until"]:

                try:
                    old_until = datetime.fromisoformat(
                        row["service_until"]
                    )

                    if old_until > now:
                        start_from = old_until
                    else:
                        start_from = now

                except Exception:
                    start_from = now

            else:
                start_from = now

            until = start_from + timedelta(days=days)

            con.execute(
                """
                UPDATE users
                SET balance=balance-?,
                    service_until=?
                WHERE user_id=?
                """,
                (
                    price,
                    until.isoformat(),
                    user.id
                )
            )

            con.commit()
            con.close()

            await query.message.reply_text(
                f"✅ خرید با موفقیت انجام شد.\n\n"
                f"📅 مدت: {days} روز\n"
                f"💎 مبلغ: {price}\n"
                f"⏰ پایان سرویس:\n"
                f"{until.strftime('%Y-%m-%d %H:%M UTC')}"
            )

    # -----------------------------------------------------
    # SELF OFF
    # -----------------------------------------------------

    elif data == "self_off":

        await query.message.reply_text(
            "🔴 سرویس برای این کاربر خاموش شد."
        )

    # -----------------------------------------------------
    # SELF ON
    # -----------------------------------------------------

    elif data == "self_on":

        await query.message.reply_text(
            "🟢 سرویس برای این کاربر روشن شد."
        )

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    elif data == "close":

        try:
            await query.message.delete()
        except Exception:
            pass


# =========================================================
# PERSIAN NUMBER
# =========================================================

def normalize_number(value):

    return value.translate(
        str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹",
            "0123456789"
        )
    )


# =========================================================
# BET
# =========================================================

async def handle_group_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return

    if message.chat.type not in (
        "group",
        "supergroup"
    ):
        return

    user = message.from_user

    ensure_user(user)

    text = (message.text or "").strip()

    # =====================================================
    # شرط 100
    # =====================================================

    match = re.fullmatch(
        r"شرط\s+([0-9۰-۹]+)",
        text
    )

    if match:

        amount = int(
            normalize_number(match.group(1))
        )

        if amount <= 0:
            return

        balance = get_balance(user.id)

        if balance < amount:

            await message.reply_text(
                "❌ موجودی شما برای این شرط کافی نیست."
            )

            return

        con = get_db()

        # رزرو مبلغ سازنده
        con.execute(
            "UPDATE users SET balance=balance-? WHERE user_id=?",
            (
                amount,
                user.id
            )
        )

        cur = con.execute(
            """
            INSERT INTO bets
            (chat_id, message_id, owner_id, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.chat.id,
                message.message_id,
                user.id,
                amount,
                "open",
                datetime.now(timezone.utc).isoformat()
            )
        )

        bet_id = cur.lastrowid

        con.commit()
        con.close()

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🎮 بازی با دوستان",
                    callback_data=f"join:{bet_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "❌ لغو بازی با دوستان",
                    callback_data=f"cancel:{bet_id}"
                )
            ]

        ])

        await message.reply_text(
            f"🎮 بازی آماده شد\n\n"
            f"💎 شرط: {amount}\n"
            f"👤 سازنده: {user.first_name}\n\n"
            "یک نفر روی «بازی با دوستان» بزند.",
            reply_markup=keyboard
        )

        return

    # =====================================================
    # انتقال
    # =====================================================

    match = re.fullmatch(
        r"انتقال\s+([0-9۰-۹]+)(?:\s+@([A-Za-z0-9_]{5,32}))?",
        text
    )

    if match:

        amount = int(
            normalize_number(match.group(1))
        )

        username = match.group(2)

        if amount <= 0:
            return

        target_id = None

        # انتقال با ریپلای
        if message.reply_to_message:

            target_id = (
                message.reply_to_message
                .from_user
                .id
            )

            ensure_user(
                message.reply_to_message.from_user
            )

        # انتقال با username
        elif username:

            try:

                member = await context.bot.get_chat_member(
                    message.chat.id,
                    username
                )

                target_id = member.user.id

                ensure_user(member.user)

            except Exception:

                await message.reply_text(
                    "❌ کاربر با این آیدی پیدا نشد."
                )

                return

        if not target_id:

            await message.reply_text(
                "❌ برای انتقال باید روی پیام شخص ریپلای کنی "
                "یا @username بدهی."
            )

            return

        if target_id == user.id:

            await message.reply_text(
                "❌ نمی‌توانی به خودت انتقال بدهی."
            )

            return

        balance = get_balance(user.id)

        if balance < amount:

            await message.reply_text(
                "❌ موجودی کافی نیست."
            )

            return

        con = get_db()

        receiver = con.execute(
            "SELECT user_id FROM users WHERE user_id=?",
            (target_id,)
        ).fetchone()

        if not receiver:

            await message.reply_text(
                "❌ گیرنده هنوز ربات را شروع نکرده است."
            )

            con.close()
            return

        con.execute(
            "UPDATE users SET balance=balance-? WHERE user_id=?",
            (
                amount,
                user.id
            )
        )

        con.execute(
            "UPDATE users SET balance=balance+? WHERE user_id=?",
            (
                amount,
                target_id
            )
        )

        con.commit()
        con.close()

        await message.reply_text(
            f"✅ انتقال انجام شد.\n\n"
            f"💎 مبلغ: {amount}"
        )


# =========================================================
# BET BUTTONS
# =========================================================

async def bet_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    action, bet_id_text = query.data.split(":")

    bet_id = int(bet_id_text)

    user = query.from_user

    ensure_user(user)

    con = get_db()

    bet = con.execute(
        "SELECT * FROM bets WHERE bet_id=?",
        (bet_id,)
    ).fetchone()

    if not bet or bet["status"] != "open":

        await query.answer(
            "❌ این شرط دیگر فعال نیست.",
            show_alert=True
        )

        con.close()
        return

    # =====================================================
    # CANCEL
    # =====================================================

    if action == "cancel":

        if user.id != bet["owner_id"]:

            await query.answer(
                "❌ فقط سازنده شرط می‌تواند آن را لغو کند.",
                show_alert=True
            )

            con.close()
            return

        con.execute(
            """
            UPDATE users
            SET balance=balance+?
            WHERE user_id=?
            """,
            (
                bet["amount"],
                bet["owner_id"]
            )
        )

        con.execute(
            """
            UPDATE bets
            SET status='cancelled'
            WHERE bet_id=?
            """,
            (bet_id,)
        )

        con.commit()
        con.close()

        await query.message.edit_text(
            "❌ بازی لغو شد.\n\n"
            "💎 مبلغ شرط به سازنده برگشت."
        )

        return

    # =====================================================
    # JOIN
    # =====================================================

    if action == "join":

        if user.id == bet["owner_id"]:

            await query.answer(
                "❌ نمی‌توانی وارد شرط خودت شوی.",
                show_alert=True
            )

            con.close()
            return

        balance = get_balance(user.id)

        if balance < bet["amount"]:

            await query.answer(
                "❌ موجودی کافی نیست.",
                show_alert=True
            )

            con.close()
            return

        amount = bet["amount"]

        # کسر مبلغ نفر دوم
        con.execute(
            """
            UPDATE users
            SET balance=balance-?
            WHERE user_id=?
            """,
            (
                amount,
                user.id
            )
        )

        # =================================================
        # انتخاب برنده
        # =================================================

        winner_id = random.choice([
            bet["owner_id"],
            user.id
        ])

        total = amount * 2

        # 90 درصد برای برنده
        prize = total * 90 // 100

        system_share = total - prize

        con.execute(
            """
            UPDATE users
            SET balance=balance+?
            WHERE user_id=?
            """,
            (
                prize,
                winner_id
            )
        )

        con.execute(
            """
            UPDATE bets
            SET opponent_id=?,
                status='finished'
            WHERE bet_id=?
            """,
            (
                user.id,
                bet_id
            )
        )

        con.commit()
        con.close()

        await query.message.edit_text(
            f"🏁 بازی تمام شد!\n\n"
            f"🏆 برنده: {winner_id}\n"
            f"💎 جایزه: {prize}\n"
            f"🤖 سهم سیستم: {system_share}"
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logging.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    init_db()

    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "panel",
            panel
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            bet_callback,
            pattern=r"^(join|cancel):"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_callback
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_group_message
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("🚀 BOT STARTED")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
