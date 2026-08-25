# =========================================================
# bot.py
# Main Telegram Bot
# =========================================================

import logging
import asyncio

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    validate_config,
)

from database import init_database

from handlers import (
    register_handlers,
)

from admin_panel import (
    admin_callback,
    charge_command,
    custom_diamond_handler,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("BOT")


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    logger.error(
        "Error: %s",
        context.error
    )


# =========================================================
# START BOT
# =========================================================

async def main():

    try:

        validate_config()

    except Exception as error:

        logger.error(
            "Config Error: %s",
            error
        )

        return


    init_database()


    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    # -----------------------------
    # Commands
    # -----------------------------

    register_handlers(
        app
    )


    app.add_handler(
        CommandHandler(
            "charge",
            charge_command
        )
    )


    # -----------------------------
    # Admin Buttons
    # -----------------------------

    app.add_handler(
        CallbackQueryHandler(
            admin_callback
        )
    )


    # -----------------------------
    # Custom diamond input
    # -----------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            custom_diamond_handler
        )
    )


    # -----------------------------
    # Errors
    # -----------------------------

    app.add_error_handler(
        error_handler
    )


    logger.info(
        "🚀 BOT STARTED"
    )


    # -----------------------------
    # Run forever
    # -----------------------------

    await app.run_polling(
        allowed_updates=(
            Update.ALL_TYPES
        )
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "BOT STOPPED"
        )

    except Exception as error:

        logger.exception(
            "Fatal error: %s",
            error
        )
