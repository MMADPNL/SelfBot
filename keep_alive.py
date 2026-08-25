# =========================================================
# keep_alive.py
# Auto Restart / Keep Alive System
# =========================================================

import time
import subprocess
import sys
import logging
import os


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("KEEP_ALIVE")


# =========================================================
# SETTINGS
# =========================================================

BOT_FILE = "bot.py"

RESTART_DELAY = 5


# =========================================================
# RUN BOT FOREVER
# =========================================================

def run_bot():

    while True:

        try:

            logger.info(
                "🚀 Starting bot..."
            )

            process = subprocess.Popen(
                [
                    sys.executable,
                    BOT_FILE
                ]
            )

            exit_code = process.wait()


            logger.warning(
                "Bot stopped. Exit code: %s",
                exit_code
            )


        except Exception as error:

            logger.exception(
                "Keep alive error: %s",
                error
            )


        logger.info(
            "Restarting in %s seconds...",
            RESTART_DELAY
        )

        time.sleep(
            RESTART_DELAY
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    run_bot()
