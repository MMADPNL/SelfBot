# =========================================================
# admin_panel.py
# پنل مدیریت مالک ربات
# Python 3.10+
# python-telegram-bot 20+
# =========================================================

import sqlite3
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
)

from config import (
    OWNER_ID,
    DATABASE_NAME,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def create_admin_tables():
    conn = get_db()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 1
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO bot_settings
            (id, enabled)
            VALUES (1, 1)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                diamonds INTEGER NOT NULL DEFAULT 0
            )
        """)

        conn.commit()

    finally:
        conn.close()


# =========================================================
# BOT STATUS
# =========================================================

def get_bot_status():
    create_admin_tables()

    conn = get_db()

    try:
        row = conn.execute("""
            SELECT enabled
            FROM bot_settings
            WHERE id = 1
        """).fetchone()

        if row is None:
            return True

        return bool(row["enabled"])

    finally:
        conn.close()


def set_bot_status(enabled: bool):
    create_admin_tables()

    conn = get_db()

    try:
        conn.execute("""
            UPDATE bot_settings
            SET enabled = ?
            WHERE id = 1
        """, (1 if enabled else 0,))

        conn.commit()

    finally:
        conn.close()


# =========================================================
# DIAMONDS
# =========================================================

def add_diamonds(user_id: int, amount: int):
    create_admin_tables()

    conn = get_db()

    try:
        conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, diamonds)
            VALUES (?, 0)
        """, (user_id,))

        conn.execute("""
            UPDATE users
            SET diamonds = diamonds + ?
            WHERE user_id = ?
        """, (amount, user_id))

        conn.commit()

    finally:
        conn.close()


def get_diamonds(user_id: int):
    create_admin_tables()

    conn = get_db()

    try:
        row = conn.execute("""
            SELECT diamonds
            FROM users
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if row is None:
            return 0

        return int(row["diamonds"])

    finally:
        conn.close()


# =========================================================
# OWNER CHECK
# =========================================================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# =========================================================
# ADMIN MENU
# =========================================================

def admin_keyboard():

    enabled = get_bot_status()

    if enabled:
        status_button = InlineKeyboardButton(
            "🔴 خاموش کردن ربات",
            callback_data="admin_bot_off"
        )
    else:
        status_button = InlineKeyboardButton(
            "🟢 روشن کردن ربات",
            callback_data="admin_bot_on"
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "💎 شارژ الماس",
                callback_data="admin_diamonds"
            )
        ],
        [
            status_button
        ],
        [
            InlineKeyboardButton(
                "📊 وضعیت ربات",
                callback_data="admin_status"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 بروزرسانی",
                callback_data="admin_refresh"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user is None:
        return

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ شما اجازه دسترسی به پنل مدیریت را ندارید."
        )
        return

    create_admin_tables()

    status = get_bot_status()

    status_text = (
        "🟢 روشن"
        if status
        else "🔴 خاموش"
    )

    text = (
        "👑 پنل مدیریت مالک\n\n"
        f"🤖 وضعیت ربات: {status_text}\n\n"
        "از منوی زیر انتخاب کنید:"
    )

    await update.message.reply_text(
        text,
        reply_markup=admin_keyboard()
    )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query is None:
        return

    user = query.from_user

    if not is_owner(user.id):

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )

        return

    await query.answer()

    data = query.data

    # -----------------------------------------------------
    # REFRESH
    # -----------------------------------------------------

    if data == "admin_refresh":

        status = get_bot_status()

        status_text = (
            "🟢 روشن"
            if status
            else "🔴 خاموش"
        )

        text = (
            "👑 پنل مدیریت مالک\n\n"
            f"🤖 وضعیت ربات: {status_text}\n\n"
            "پنل بروزرسانی شد."
        )

        await query.edit_message_text(
            text,
            reply_markup=admin_keyboard()
        )

        return

    # -----------------------------------------------------
    # BOT ON
    # -----------------------------------------------------

    if data == "admin_bot_on":

        set_bot_status(True)

        await query.edit_message_text(
            "🟢 ربات روشن شد.\n\n"
            "♻️ وضعیت در دیتابیس ذخیره شد.",
            reply_markup=admin_keyboard()
        )

        logger.info(
            "Bot enabled by owner: %s",
            user.id
        )

        return

    # -----------------------------------------------------
    # BOT OFF
    # -----------------------------------------------------

    if data == "admin_bot_off":

        set_bot_status(False)

        await query.edit_message_text(
            "🔴 ربات خاموش شد.\n\n"
            "♻️ وضعیت در دیتابیس ذخیره شد.",
            reply_markup=admin_keyboard()
        )

        logger.info(
            "Bot disabled by owner: %s",
            user.id
        )

        return

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if data == "admin_status":

        status = get_bot_status()

        status_text = (
            "🟢 روشن"
            if status
            else "🔴 خاموش"
        )

        text = (
            "📊 وضعیت ربات\n\n"
            f"🤖 وضعیت: {status_text}\n"
            f"👑 مالک: `{OWNER_ID}`\n\n"
            "💎 سیستم الماس: فعال"
        )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )

        return

    # -----------------------------------------------------
    # DIAMONDS MENU
    # -----------------------------------------------------

    if data == "admin_diamonds":

        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 +100",
                    callback_data="diamond_100"
                ),
                InlineKeyboardButton(
                    "💎 +500",
                    callback_data="diamond_500"
                ),
            ],
            [
                InlineKeyboardButton(
                    "💎 +1000",
                    callback_data="diamond_1000"
                ),
                InlineKeyboardButton(
                    "💎 +5000",
                    callback_data="diamond_5000"
                ),
            ],
            [
                InlineKeyboardButton(
                    "✏️ شارژ دلخواه",
                    callback_data="diamond_custom"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="admin_back"
                )
            ]
        ]

        await query.edit_message_text(
            "💎 مدیریت الماس\n\n"
            "ابتدا کاربر را با ریپلای مشخص کن، "
            "سپس مقدار شارژ را انتخاب کن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # -----------------------------------------------------
    # BACK
    # -----------------------------------------------------

    if data == "admin_back":

        status = get_bot_status()

        status_text = (
            "🟢 روشن"
            if status
            else "🔴 خاموش"
        )

        await query.edit_message_text(
            "👑 پنل مدیریت مالک\n\n"
            f"🤖 وضعیت ربات: {status_text}",
            reply_markup=admin_keyboard()
        )

        return

    # -----------------------------------------------------
    # DIAMOND AMOUNT
    # -----------------------------------------------------

    if data.startswith("diamond_"):

        amount_text = data.replace(
            "diamond_",
            ""
        )

        if amount_text == "custom":

            context.user_data[
                "waiting_custom_diamond"
            ] = True

            await query.edit_message_text(
                "✏️ مقدار الماس را به صورت عددی بفرست.\n\n"
                "مثال:\n"
                "`10000`",
                parse_mode="Markdown"
            )

            return

        try:
            amount = int(amount_text)

        except ValueError:

            await query.answer(
                "❌ مقدار نامعتبر است.",
                show_alert=True
            )

            return

        context.user_data[
            "diamond_amount"
        ] = amount

        await query.edit_message_text(
            f"💎 مقدار انتخاب شده: {amount}\n\n"
            "حالا پیام کاربر را ریپلای کن و دستور زیر را بفرست:\n\n"
            f"`/charge {amount}`",
            parse_mode="Markdown"
        )

        return


# =========================================================
# CHARGE COMMAND
# =========================================================

async def charge_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if user is None or not is_owner(user.id):

        await update.message.reply_text(
            "⛔ فقط مالک می‌تواند الماس شارژ کند."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "❌ باید روی پیام کاربر ریپلای کنی.\n\n"
            "مثال:\n"
            "/charge 1000"
        )

        return

    if not context.args:

        await update.message.reply_text(
            "❌ مقدار الماس را وارد کن.\n\n"
            "مثال:\n"
            "/charge 1000"
        )

        return

    try:

        amount = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ مقدار باید عدد باشد."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )

        return

    target = (
        update.message
        .reply_to_message
        .from_user
    )

    if target is None:

        await update.message.reply_text(
            "❌ کاربر پیدا نشد."
        )

        return

    add_diamonds(
        target.id,
        amount
    )

    new_balance = get_diamonds(
        target.id
    )

    await update.message.reply_text(
        "✅ شارژ با موفقیت انجام شد.\n\n"
        f"👤 کاربر: {target.first_name or 'کاربر'}\n"
        f"🆔 ID: `{target.id}`\n"
        f"💎 مقدار شارژ: +{amount}\n"
        f"💰 موجودی جدید: {new_balance}",
        parse_mode="Markdown"
    )

    logger.info(
        "Owner %s charged %s diamonds to %s",
        user.id,
        amount,
        target.id
    )


# =========================================================
# CUSTOM DIAMOND HANDLER
# =========================================================

async def custom_diamond_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if user is None or not is_owner(user.id):
        return

    if not context.user_data.get(
        "waiting_custom_diamond",
        False
    ):
        return

    try:

        amount = int(
            update.message.text.strip()
        )

    except (ValueError, AttributeError):

        await update.message.reply_text(
            "❌ فقط عدد بفرست.\n\n"
            "مثال: 10000"
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )

        return

    context.user_data[
        "waiting_custom_diamond"
    ] = False

    context.user_data[
        "diamond_amount"
    ] = amount

    await update.message.reply_text(
        f"💎 مقدار شارژ: {amount}\n\n"
        "حالا روی پیام کاربر ریپلای کن و بزن:\n\n"
        f"`/charge {amount}`",
        parse_mode="Markdown"
  )
