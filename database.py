# =========================================================
# database.py
# Database Manager
# Python 3.10+
# SQLite
# =========================================================

import sqlite3
import threading
from datetime import datetime

from config import DATABASE_NAME


# =========================================================
# DATABASE LOCK
# =========================================================

_db_lock = threading.RLock()


# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INIT DATABASE
# =========================================================

def init_database():

    with _db_lock:

        conn = get_connection()

        try:

            # -------------------------------------------------
            # USERS
            # -------------------------------------------------

            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    diamonds INTEGER NOT NULL DEFAULT 0,
                    coins INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # -------------------------------------------------
            # BOT SETTINGS
            # -------------------------------------------------

            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)

            # -------------------------------------------------
            # TRANSACTIONS
            # -------------------------------------------------

            conn.execute("""
                CREATE TABLE IF NOT EXISTS diamond_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # -------------------------------------------------
            # DEFAULT BOT STATUS
            # -------------------------------------------------

            now = datetime.utcnow().isoformat()

            conn.execute("""
                INSERT OR IGNORE INTO bot_settings
                (id, enabled, updated_at)
                VALUES (1, 1, ?)
            """, (now,))

            conn.commit()

        finally:

            conn.close()


# =========================================================
# USER
# =========================================================

def create_user(
    user_id: int,
    username: str = "",
    first_name: str = ""
):

    init_database()

    now = datetime.utcnow().isoformat()

    with _db_lock:

        conn = get_connection()

        try:

            conn.execute("""
                INSERT OR IGNORE INTO users
                (
                    user_id,
                    username,
                    first_name,
                    diamonds,
                    coins,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, 0, 0, ?, ?)
            """, (
                user_id,
                username or "",
                first_name or "",
                now,
                now
            ))

            conn.execute("""
                UPDATE users
                SET
                    username = ?,
                    first_name = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                username or "",
                first_name or "",
                now,
                user_id
            ))

            conn.commit()

        finally:

            conn.close()


# =========================================================
# GET USER
# =========================================================

def get_user(user_id: int):

    init_database()

    with _db_lock:

        conn = get_connection()

        try:

            return conn.execute("""
                SELECT *
                FROM users
                WHERE user_id = ?
            """, (user_id,)).fetchone()

        finally:

            conn.close()


# =========================================================
# DIAMONDS
# =========================================================

def get_diamonds(user_id: int) -> int:

    user = get_user(user_id)

    if user is None:
        return 0

    return int(user["diamonds"])


def add_diamonds(
    user_id: int,
    amount: int,
    action: str = "admin_charge"
):

    if amount <= 0:
        raise ValueError(
            "Diamond amount must be greater than zero."
        )

    create_user(user_id)

    now = datetime.utcnow().isoformat()

    with _db_lock:

        conn = get_connection()

        try:

            conn.execute("""
                UPDATE users
                SET
                    diamonds = diamonds + ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                amount,
                now,
                user_id
            ))

            row = conn.execute("""
                SELECT diamonds
                FROM users
                WHERE user_id = ?
            """, (user_id,)).fetchone()

            balance = int(row["diamonds"])

            conn.execute("""
                INSERT INTO diamond_transactions
                (
                    user_id,
                    amount,
                    balance_after,
                    action,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                amount,
                balance,
                action,
                now
            ))

            conn.commit()

            return balance

        finally:

            conn.close()


def remove_diamonds(
    user_id: int,
    amount: int,
    action: str = "spend"
):

    if amount <= 0:
        raise ValueError(
            "Diamond amount must be greater than zero."
        )

    create_user(user_id)

    now = datetime.utcnow().isoformat()

    with _db_lock:

        conn = get_connection()

        try:

            row = conn.execute("""
                SELECT diamonds
                FROM users
                WHERE user_id = ?
            """, (user_id,)).fetchone()

            balance = int(row["diamonds"])

            if balance < amount:
                return False, balance

            new_balance = balance - amount

            conn.execute("""
                UPDATE users
                SET
                    diamonds = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                new_balance,
                now,
                user_id
            ))

            conn.execute("""
                INSERT INTO diamond_transactions
                (
                    user_id,
                    amount,
                    balance_after,
                    action,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                -amount,
                new_balance,
                action,
                now
            ))

            conn.commit()

            return True, new_balance

        finally:

            conn.close()


# =========================================================
# COINS
# =========================================================

def get_coins(user_id: int) -> int:

    user = get_user(user_id)

    if user is None:
        return 0

    return int(user["coins"])


def add_coins(
    user_id: int,
    amount: int
):

    if amount <= 0:
        raise ValueError(
            "Coin amount must be greater than zero."
        )

    create_user(user_id)

    now = datetime.utcnow().isoformat()

    with _db_lock:

        conn = get_connection()

        try:

            conn.execute("""
                UPDATE users
                SET
                    coins = coins + ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                amount,
                now,
                user_id
            ))

            conn.commit()

            return get_coins(user_id)

        finally:

            conn.close()


def remove_coins(
    user_id: int,
    amount: int
):

    if amount <= 0:
        raise ValueError(
            "Coin amount must be greater than zero."
        )

    create_user(user_id)

    now = datetime.utcnow().isoformat()

    with _db_lock:

        conn = get_connection()

        try:

            row = conn.execute("""
                SELECT coins
                FROM users
                WHERE user_id = ?
            """, (user_id,)).fetchone()

            balance = int(row["coins"])

            if balance < amount:
                return False, balance

            new_balance = balance - amount

            conn.execute("""
                UPDATE users
                SET
                    coins = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                new_balance,
                now,
                user_id
            ))

            conn.commit()

            return True, new_balance

        finally:

            conn.close()


# =========================================================
# BOT STATUS
# =========================================================

def is_bot_enabled() -> bool:

    init_database()

    with _db_lock:

        conn = get_connection()

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


def set_bot_enabled(enabled: bool):

    init_database()

    now = datetime.utcnow().isoformat()

    with _db_lock:

        conn = get_connection()

        try:

            conn.execute("""
                UPDATE bot_settings
                SET
                    enabled = ?,
                    updated_at = ?
                WHERE id = 1
            """, (
                1 if enabled else 0,
                now
            ))

            conn.commit()

        finally:

            conn.close()


# =========================================================
# TRANSACTIONS
# =========================================================

def get_diamond_transactions(
    user_id: int,
    limit: int = 20
):

    init_database()

    limit = max(
        1,
        min(int(limit), 100)
    )

    with _db_lock:

        conn = get_connection()

        try:

            return conn.execute("""
                SELECT *
                FROM diamond_transactions
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (
                user_id,
                limit
            )).fetchall()

        finally:

            conn.close()


# =========================================================
# STATISTICS
# =========================================================

def get_user_count() -> int:

    init_database()

    with _db_lock:

        conn = get_connection()

        try:

            row = conn.execute("""
                SELECT COUNT(*) AS count
                FROM users
            """).fetchone()

            return int(row["count"])

        finally:

            conn.close()


def get_total_diamonds() -> int:

    init_database()

    with _db_lock:

        conn = get_connection()

        try:

            row = conn.execute("""
                SELECT COALESCE(
                    SUM(diamonds),
                    0
                ) AS total
                FROM users
            """).fetchone()

            return int(row["total"])

        finally:

            conn.close()


# =========================================================
# STARTUP
# =========================================================

init_database()
