import sqlite3
import random
import time

DB_NAME = "hrishu.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 5-DIGIT HRISHU ID
# =========================

def generate_hrishu_id(cur):
    while True:
        new_id = random.randint(10000, 99999)

        cur.execute(
            "SELECT user_id FROM users WHERE hrishu_id = ?",
            (new_id,)
        )

        if cur.fetchone() is None:
            return new_id


# =========================
# DATABASE SETUP / MIGRATION
# =========================

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            hrishu_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,

            coins INTEGER DEFAULT 1000,
            bank INTEGER DEFAULT 0,

            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,

            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,

            kills INTEGER DEFAULT 0,
            deaths INTEGER DEFAULT 0,
            robs INTEGER DEFAULT 0,

            warns INTEGER DEFAULT 0,

            inventory TEXT DEFAULT '',

            last_daily INTEGER DEFAULT 0,
            last_work INTEGER DEFAULT 0,
            last_rob INTEGER DEFAULT 0,
            last_fight INTEGER DEFAULT 0,
            last_kill INTEGER DEFAULT 0,
            protected_until INTEGER DEFAULT 0,

            sword_durability INTEGER DEFAULT 0,
            shield_durability INTEGER DEFAULT 0,

            staff_role TEXT DEFAULT 'user'
        )
    """)

    # Check existing columns
    cur.execute("PRAGMA table_info(users)")
    columns = {row["name"] for row in cur.fetchall()}

    # Add missing columns to old databases
    migrations = {
        "hrishu_id": "INTEGER",
        "username": "TEXT",
        "first_name": "TEXT",

        "coins": "INTEGER DEFAULT 1000",
        "bank": "INTEGER DEFAULT 0",

        "xp": "INTEGER DEFAULT 0",
        "level": "INTEGER DEFAULT 1",

        "hp": "INTEGER DEFAULT 100",
        "max_hp": "INTEGER DEFAULT 100",

        "kills": "INTEGER DEFAULT 0",
        "deaths": "INTEGER DEFAULT 0",
        "robs": "INTEGER DEFAULT 0",

        "warns": "INTEGER DEFAULT 0",

        "inventory": "TEXT DEFAULT ''",

        "last_daily": "INTEGER DEFAULT 0",
        "last_work": "INTEGER DEFAULT 0",
        "last_rob": "INTEGER DEFAULT 0",
        "last_fight": "INTEGER DEFAULT 0",
        "last_kill": "INTEGER DEFAULT 0",
        "protected_until": "INTEGER DEFAULT 0",

        "sword_durability": "INTEGER DEFAULT 0",
        "shield_durability": "INTEGER DEFAULT 0",

        # =========================
        # POWER SYSTEM
        # =========================
        "power_hp_level": "INTEGER DEFAULT 1",
        "power_hp_upgrades": "INTEGER DEFAULT 0",

        "power_attack_level": "INTEGER DEFAULT 1",
        "power_attack_upgrades": "INTEGER DEFAULT 0",

        "power_sword_level": "INTEGER DEFAULT 1",
        "power_sword_upgrades": "INTEGER DEFAULT 0",

        "power_durability_level": "INTEGER DEFAULT 1",
        "power_durability_upgrades": "INTEGER DEFAULT 0",

        "power_shield_level": "INTEGER DEFAULT 1",
        "power_shield_upgrades": "INTEGER DEFAULT 0",

        "staff_role": "TEXT DEFAULT 'user'"
    }

    for column, definition in migrations.items():
        if column not in columns:
            cur.execute(
                f"ALTER TABLE users ADD COLUMN {column} {definition}"
            )

    # Give old users a 5-digit Hrishu ID
    cur.execute(
        "SELECT user_id FROM users WHERE hrishu_id IS NULL"
    )

    old_users = cur.fetchall()

    for row in old_users:
        hrishu_id = generate_hrishu_id(cur)

        cur.execute(
            """
            UPDATE users
            SET hrishu_id = ?
            WHERE user_id = ?
            """,
            (hrishu_id, row["user_id"])
        )

    # Make sure old users have valid staff roles
    cur.execute("""
        UPDATE users
        SET staff_role = 'user'
        WHERE staff_role IS NULL OR staff_role = ''
    """)

    conn.commit()
    conn.close()


# =========================
# GLOBAL FIGHT SYSTEM
# =========================

def init_global_fight_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_fight_chats (
            chat_id INTEGER PRIMARY KEY,
            chat_type TEXT NOT NULL,
            last_seen INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_fight_users (
            user_id INTEGER PRIMARY KEY,
            last_global_fight INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_fight_private_users (
            user_id INTEGER PRIMARY KEY,
            last_seen INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_fight_matchmaking (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            chat_type TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# USER MANAGEMENT
# =========================

def create_user(user_id, username=None, first_name="User"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE users
            SET username = ?, first_name = ?
            WHERE user_id = ?
            """,
            (username, first_name, user_id)
        )

    else:
        hrishu_id = generate_hrishu_id(cur)

        cur.execute(
            """
            INSERT INTO users (
                user_id,
                hrishu_id,
                username,
                first_name,
                staff_role
            )
            VALUES (?, ?, ?, ?, 'user')
            """,
            (
                user_id,
                hrishu_id,
                username,
                first_name
            )
        )

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cur.fetchone()

    conn.close()

    return user


def update_user(user_id, **fields):
    allowed = {
        "username",
        "first_name",

        "coins",
        "bank",

        "xp",
        "level",

        "hp",
        "max_hp",

        "kills",
        "deaths",
        "robs",

        "warns",

        "inventory",

        "last_daily",
        "last_work",
        "last_rob",
        "last_fight",
        "last_kill",
        "protected_until",
        "sword_durability",
        "shield_durability",
        "sword_upgrade",
        "swords_bought",
        "shields_bought",

        # Power system
        "power_hp_level",
        "power_hp_upgrades",
        "power_attack_level",
        "power_attack_upgrades",
        "power_sword_level",
        "power_sword_upgrades",
        "power_durability_level",
        "power_durability_upgrades",
        "power_shield_level",
        "power_shield_upgrades",

        "staff_role"
    }

    fields = {
        key: value
        for key, value in fields.items()
        if key in allowed
    }

    if not fields:
        return

    conn = get_connection()
    cur = conn.cursor()

    set_clause = ", ".join(
        f"{key} = ?"
        for key in fields
    )

    values = list(fields.values())
    values.append(user_id)

    cur.execute(
        f"""
        UPDATE users
        SET {set_clause}
        WHERE user_id = ?
        """,
        values
    )

    conn.commit()
    conn.close()


# =========================
# ECONOMY
# =========================

def add_coins(user_id, amount):
    user = get_user(user_id)

    if not user:
        return

    update_user(
        user_id,
        coins=user["coins"] + amount
    )


# =========================
# XP / LEVEL
# =========================

def add_xp(user_id, amount):
    """
    Adds XP and automatically updates the player's level.

    Every 100 XP = 1 level.
    """

    user = get_user(user_id)

    if not user or amount <= 0:
        return None

    old_level = user["level"]

    new_xp = user["xp"] + amount

    new_level = (new_xp // 100) + 1

    update_user(
        user_id,
        xp=new_xp,
        level=new_level
    )

    return {
        "old_xp": user["xp"],
        "new_xp": new_xp,
        "old_level": old_level,
        "new_level": new_level,
        "level_up": new_level > old_level
    }


# =========================
# COOLDOWNS
# =========================

def cooldown_remaining(last_time, cooldown):
    remaining = cooldown - (
        int(time.time()) - last_time
    )

    return max(0, remaining)

# =========================
# HRISHU BANK SYSTEM
# =========================

import hashlib
import secrets
import string


BANK_NAMES = (
    "Hrishu Bank",
    "ICICI Bank",
    "Central Bank",
    "SBI Bank",
    "HDFC Bank",
    "Canara Bank",
)


def init_bank_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            account_number TEXT NOT NULL UNIQUE,
            account_code TEXT NOT NULL UNIQUE,
            upi_id TEXT NOT NULL UNIQUE,
            hpin_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            UNIQUE(user_id, bank_name),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            other_user_id INTEGER,
            other_account_number TEXT,
            description TEXT DEFAULT '',
            created_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bank_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'approved',
            created_at INTEGER NOT NULL,
            UNIQUE(user_id, bank_name),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()


def generate_bank_account_number(cur):
    while True:
        account_number = str(secrets.randbelow(9000000) + 1000000)

        cur.execute(
            "SELECT id FROM bank_accounts WHERE account_number = ?",
            (account_number,),
        )

        if cur.fetchone() is None:
            return account_number


def generate_bank_account_code(cur):
    alphabet = string.ascii_uppercase + string.digits

    while True:
        account_code = "".join(
            secrets.choice(alphabet)
            for _ in range(10)
        )

        cur.execute(
            "SELECT id FROM bank_accounts WHERE account_code = ?",
            (account_code,),
        )

        if cur.fetchone() is None:
            return account_code


def generate_upi_id(cur, account_number):
    base = f"{account_number}@hrishu"

    cur.execute(
        "SELECT id FROM bank_accounts WHERE upi_id = ?",
        (base,),
    )

    if cur.fetchone() is None:
        return base

    suffix = secrets.token_hex(2)
    return f"{account_number}{suffix}@hrishu"


def hash_hpin(hpin):
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(hpin).encode(),
        salt,
        150000,
    )

    return (
        salt.hex()
        + ":"
        + digest.hex()
    )


def verify_hpin(hpin, stored_hash):
    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)

        salt = bytes.fromhex(salt_hex)

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            str(hpin).encode(),
            salt,
            150000,
        )

        return secrets.compare_digest(
            digest.hex(),
            digest_hex,
        )

    except Exception:
        return False


def get_bank_account(user_id, bank_name="Hrishu Bank"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM bank_accounts
        WHERE user_id = ?
          AND bank_name = ?
          AND status = 'active'
        LIMIT 1
        """,
        (user_id, bank_name),
    )

    account = cur.fetchone()

    conn.close()
    return account


def get_user_bank_accounts(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM bank_accounts
        WHERE user_id = ?
          AND status = 'active'
        ORDER BY created_at ASC
        """,
        (user_id,),
    )

    accounts = cur.fetchall()

    conn.close()
    return accounts


def get_bank_account_by_number(account_number):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM bank_accounts
        WHERE account_number = ?
          AND status = 'active'
        LIMIT 1
        """,
        (str(account_number),),
    )

    account = cur.fetchone()

    conn.close()
    return account


def get_bank_account_by_upi(upi_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM bank_accounts
        WHERE LOWER(upi_id) = LOWER(?)
          AND status = 'active'
        LIMIT 1
        """,
        (upi_id,),
    )

    account = cur.fetchone()

    conn.close()
    return account


def create_bank_account(user_id, bank_name, hpin):
    now = int(time.time())

    conn = get_connection()
    cur = conn.cursor()

    existing = get_bank_account(user_id, bank_name)

    if existing:
        conn.close()
        return None

    account_number = generate_bank_account_number(cur)
    account_code = generate_bank_account_code(cur)
    upi_id = generate_upi_id(cur, account_number)

    hpin_hash = hash_hpin(hpin)

    cur.execute(
        """
        INSERT INTO bank_accounts (
            user_id,
            bank_name,
            account_number,
            account_code,
            upi_id,
            hpin_hash,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            bank_name,
            account_number,
            account_code,
            upi_id,
            hpin_hash,
            now,
        ),
    )

    conn.commit()

    cur.execute(
        "SELECT * FROM bank_accounts WHERE id = ?",
        (cur.lastrowid,),
    )

    account = cur.fetchone()

    conn.close()
    return account


def add_bank_transaction(
    user_id,
    transaction_type,
    amount,
    balance_after,
    other_user_id=None,
    other_account_number=None,
    description="",
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO bank_transactions (
            user_id,
            transaction_type,
            amount,
            balance_after,
            other_user_id,
            other_account_number,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            transaction_type,
            amount,
            balance_after,
            other_user_id,
            other_account_number,
            description,
            int(time.time()),
        ),
    )

    conn.commit()
    conn.close()


def get_last_bank_transactions(user_id, limit=5):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM bank_transactions
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )

    transactions = cur.fetchall()

    conn.close()
    return transactions


def transfer_bank_coins(
    sender_user_id,
    recipient_user_id,
    amount,
    description="Bank transfer",
):
    amount = int(amount)

    if amount <= 0:
        return False, "invalid_amount"

    conn = get_connection()

    try:
        cur = conn.cursor()
        conn.execute("BEGIN IMMEDIATE")

        cur.execute(
            "SELECT bank FROM users WHERE user_id = ?",
            (sender_user_id,),
        )
        sender = cur.fetchone()

        cur.execute(
            "SELECT bank FROM users WHERE user_id = ?",
            (recipient_user_id,),
        )
        recipient = cur.fetchone()

        if not sender or not recipient:
            conn.rollback()
            return False, "user_not_found"

        if sender["bank"] < amount:
            conn.rollback()
            return False, "insufficient_balance"

        sender_balance = sender["bank"] - amount
        recipient_balance = recipient["bank"] + amount

        cur.execute(
            """
            UPDATE users
            SET bank = ?
            WHERE user_id = ?
            """,
            (sender_balance, sender_user_id),
        )

        cur.execute(
            """
            UPDATE users
            SET bank = ?
            WHERE user_id = ?
            """,
            (recipient_balance, recipient_user_id),
        )

        now = int(time.time())

        cur.execute(
            """
            INSERT INTO bank_transactions (
                user_id,
                transaction_type,
                amount,
                balance_after,
                other_user_id,
                description,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sender_user_id,
                "sent",
                amount,
                sender_balance,
                recipient_user_id,
                description,
                now,
            ),
        )

        cur.execute(
            """
            INSERT INTO bank_transactions (
                user_id,
                transaction_type,
                amount,
                balance_after,
                other_user_id,
                description,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipient_user_id,
                "received",
                amount,
                recipient_balance,
                sender_user_id,
                description,
                now,
            ),
        )

        conn.commit()
        return True, "success"

    except Exception:
        conn.rollback()
        return False, "error"

    finally:
        conn.close()

def get_user_by_hrishu_id(hrishu_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE LOWER(hrishu_id) = LOWER(?)
        LIMIT 1
        """,
        (str(hrishu_id).strip(),),
    )

    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE LOWER(username) = LOWER(?)
        LIMIT 1
        """,
        (str(username).strip().lstrip("@"),),
    )

    user = cur.fetchone()
    conn.close()
    return user

def get_bank_account_by_username(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            bank_accounts.*,
            users.username,
            users.hrishu_id
        FROM bank_accounts
        JOIN users
          ON users.user_id = bank_accounts.user_id
        WHERE LOWER(users.username) = LOWER(?)
          AND bank_accounts.bank_name = 'Hrishu Bank'
          AND bank_accounts.status = 'active'
        LIMIT 1
        """,
        (username,),
    )

    account = cur.fetchone()

    conn.close()
    return account
