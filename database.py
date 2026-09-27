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

    new_level = max(old_level, (new_xp // 100) + 1)

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


# =========================
# POKEMON SYSTEM
# =========================

def init_pokemon_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_species (
            species_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type1 TEXT NOT NULL,
            type2 TEXT,
            base_hp INTEGER NOT NULL,
            base_atk INTEGER NOT NULL,
            base_def INTEGER NOT NULL,
            base_spd INTEGER NOT NULL,
            catch_rate INTEGER NOT NULL DEFAULT 45,
            price INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            move_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            power INTEGER DEFAULT 0,
            accuracy INTEGER DEFAULT 100
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS species_moves (
            species_id INTEGER NOT NULL,
            move_id INTEGER NOT NULL,
            learn_level INTEGER DEFAULT 1,
            FOREIGN KEY(species_id) REFERENCES pokemon_species(species_id),
            FOREIGN KEY(move_id) REFERENCES moves(move_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_pokemon (
            poke_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            species_id INTEGER NOT NULL,
            nickname TEXT,
            level INTEGER DEFAULT 5,
            xp INTEGER DEFAULT 0,
            current_hp INTEGER,
            iv_hp INTEGER DEFAULT 0,
            iv_atk INTEGER DEFAULT 0,
            iv_def INTEGER DEFAULT 0,
            iv_spd INTEGER DEFAULT 0,
            in_team INTEGER DEFAULT 0,
            team_slot INTEGER,
            caught_at INTEGER,
            FOREIGN KEY(species_id) REFERENCES pokemon_species(species_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_pokemon_moves (
            poke_id INTEGER NOT NULL,
            move_id INTEGER NOT NULL,
            slot INTEGER NOT NULL,
            FOREIGN KEY(poke_id) REFERENCES user_pokemon(poke_id),
            FOREIGN KEY(move_id) REFERENCES moves(move_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_inventory (
            user_id INTEGER PRIMARY KEY,
            pokeball INTEGER DEFAULT 5,
            greatball INTEGER DEFAULT 0,
            masterball INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wild_spawns (
            chat_id INTEGER PRIMARY KEY,
            species_id INTEGER,
            level INTEGER,
            current_hp INTEGER,
            max_hp INTEGER,
            spawned_at INTEGER,
            FOREIGN KEY(species_id) REFERENCES pokemon_species(species_id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# POKEMON GAME LOGIC
# =========================

TYPE_CHART = {
    "Fire": {"Water":0.5,"Grass":2.0,"Ice":2.0,"Rock":0.5,"Fire":0.5},
    "Water": {"Fire":2.0,"Grass":0.5,"Electric":0.5,"Ground":2.0,"Rock":2.0,"Water":0.5},
    "Grass": {"Water":2.0,"Fire":0.5,"Ground":2.0,"Rock":2.0,"Flying":0.5,"Grass":0.5,"Ice":0.5},
    "Electric": {"Water":2.0,"Flying":2.0,"Ground":0.0,"Grass":0.5,"Electric":0.5},
    "Ice": {"Grass":2.0,"Ground":2.0,"Flying":2.0,"Fire":0.5,"Water":0.5,"Ice":0.5,"Rock":0.5},
    "Ground": {"Fire":2.0,"Electric":2.0,"Rock":2.0,"Grass":0.5,"Flying":0.0,"Ice":0.5},
    "Flying": {"Grass":2.0,"Electric":0.5,"Rock":0.5,"Ice":0.5},
    "Psychic": {"Psychic":0.5},
    "Rock": {"Fire":2.0,"Ice":2.0,"Flying":2.0,"Ground":0.5},
    "Normal": {"Rock":0.5},
    "Poison": {"Grass":2.0,"Poison":0.5,"Ground":0.5,"Rock":0.5,"Ghost":0.5},
    "Fighting": {"Normal":2.0,"Ice":2.0,"Rock":2.0,"Flying":0.5,"Psychic":0.5,"Poison":0.5,"Ghost":0.0},
    "Ghost": {"Ghost":2.0,"Psychic":2.0,"Normal":0.0},
    "Dragon": {"Dragon":2.0},
}

def type_multiplier(atk_type, def_type1, def_type2=None):
    chart = TYPE_CHART.get(atk_type, {})
    mult = chart.get(def_type1, 1.0)
    if def_type2:
        mult *= chart.get(def_type2, 1.0)
    return mult

def get_species_by_id(species_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM pokemon_species WHERE species_id=?", (species_id,))
    row = cur.fetchone(); conn.close(); return row

def get_move_by_id(move_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM moves WHERE move_id=?", (move_id,))
    row = cur.fetchone(); conn.close(); return row

def get_species_moves(species_id, level):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT m.* FROM species_moves sm JOIN moves m ON sm.move_id=m.move_id
                   WHERE sm.species_id=? AND sm.learn_level<=? ORDER BY sm.learn_level""", (species_id, level))
    rows = cur.fetchall(); conn.close(); return rows

def calc_stats(species_row, level):
    hp = species_row["base_hp"] + level*3 + 10
    atk = species_row["base_atk"] + level*2
    dfn = species_row["base_def"] + level*2
    spd = species_row["base_spd"] + level*2
    return {"hp": hp, "atk": atk, "def": dfn, "spd": spd}

def xp_needed(level):
    return level * 80

def get_coins(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close()
    return row["coins"] if row else 0

def add_coins(user_id, delta):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (delta, user_id))
    conn.commit(); conn.close()

def ensure_pokemon_inventory(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO pokemon_inventory (user_id) VALUES (?)", (user_id,))
    conn.commit(); conn.close()

def get_balls(user_id):
    ensure_pokemon_inventory(user_id)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT pokeball, greatball, masterball FROM pokemon_inventory WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close(); return dict(row)

def add_balls(user_id, ball_type, qty):
    ensure_pokemon_inventory(user_id)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE pokemon_inventory SET " + ball_type + " = " + ball_type + " + ? WHERE user_id=?", (qty, user_id))
    conn.commit(); conn.close()

def use_ball(user_id, ball_type):
    ensure_pokemon_inventory(user_id)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT " + ball_type + " AS n FROM pokemon_inventory WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row or row["n"] <= 0:
        conn.close(); return False
    cur.execute("UPDATE pokemon_inventory SET " + ball_type + " = " + ball_type + " - 1 WHERE user_id=?", (user_id,))
    conn.commit(); conn.close(); return True

def get_user_pokemon_list(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT up.poke_id, up.nickname, up.level, up.xp, up.current_hp, up.in_team, up.team_slot,
                          ps.species_id, ps.name, ps.type1, ps.type2, ps.base_hp, ps.base_atk, ps.base_def, ps.base_spd
                   FROM user_pokemon up JOIN pokemon_species ps ON up.species_id=ps.species_id
                   WHERE up.owner_id=? ORDER BY up.poke_id""", (user_id,))
    rows = cur.fetchall(); conn.close(); return rows

def get_pokemon_by_id(poke_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT up.*, ps.name, ps.type1, ps.type2, ps.base_hp, ps.base_atk, ps.base_def, ps.base_spd
                   FROM user_pokemon up JOIN pokemon_species ps ON up.species_id=ps.species_id
                   WHERE up.poke_id=?""", (poke_id,))
    row = cur.fetchone(); conn.close(); return row

def get_team(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT up.*, ps.name, ps.type1, ps.type2, ps.base_hp, ps.base_atk, ps.base_def, ps.base_spd
                   FROM user_pokemon up JOIN pokemon_species ps ON up.species_id=ps.species_id
                   WHERE up.owner_id=? AND up.in_team=1 ORDER BY up.team_slot""", (user_id,))
    rows = cur.fetchall(); conn.close(); return rows

def set_team_slot(user_id, poke_id, slot):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT owner_id FROM user_pokemon WHERE poke_id=?", (poke_id,))
    row = cur.fetchone()
    if not row or row["owner_id"] != user_id:
        conn.close(); return False
    cur.execute("UPDATE user_pokemon SET in_team=0, team_slot=NULL WHERE owner_id=? AND team_slot=?", (user_id, slot))
    cur.execute("UPDATE user_pokemon SET in_team=1, team_slot=? WHERE poke_id=?", (slot, poke_id))
    conn.commit(); conn.close(); return True

def buy_pokemon(user_id, species_id):
    species_row = get_species_by_id(species_id)
    if not species_row:
        return None, "not_found"
    price = species_row["price"]
    if get_coins(user_id) < price:
        return species_row, "no_coins"
    add_coins(user_id, -price)
    stats = calc_stats(species_row, 5)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""INSERT INTO user_pokemon (owner_id,species_id,level,xp,current_hp,in_team,team_slot,caught_at)
                   VALUES (?,?,5,0,?,0,NULL,?)""", (user_id, species_id, stats["hp"], int(time.time())))
    conn.commit(); conn.close()
    return species_row, "bought"

def spawn_wild(chat_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT species_id, rarity FROM pokemon_species")
    rows = cur.fetchall()
    weights_map = {"common": 100, "rare": 15, "legendary": 1}
    pool = [r["species_id"] for r in rows]
    wts = [weights_map.get(r["rarity"] or "common", 100) for r in rows]
    chosen_id = random.choices(pool, weights=wts, k=1)[0]
    species_row = get_species_by_id(chosen_id)
    if species_row["rarity"] == "legendary":
        level = random.randint(55, 90)
    elif species_row["rarity"] == "rare":
        level = random.randint(15, 45)
    else:
        level = random.randint(3, 25)
    stats = calc_stats(species_row, level)
    shiny = 1 if random.randint(1, 150) == 1 else 0
    cur.execute("DELETE FROM wild_spawns WHERE chat_id=?", (chat_id,))
    cur.execute("""INSERT INTO wild_spawns (chat_id,species_id,level,current_hp,max_hp,spawned_at,shiny)
                   VALUES (?,?,?,?,?,?,?)""", (chat_id, chosen_id, level, stats["hp"], stats["hp"], int(time.time()), shiny))
    conn.commit(); conn.close()
    return species_row, level, stats["hp"], shiny

def get_wild(chat_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM wild_spawns WHERE chat_id=?", (chat_id,))
    row = cur.fetchone(); conn.close(); return row

def clear_wild(chat_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM wild_spawns WHERE chat_id=?", (chat_id,))
    conn.commit(); conn.close()

def damage_wild(chat_id, dmg):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE wild_spawns SET current_hp = MAX(0, current_hp - ?) WHERE chat_id=?", (dmg, chat_id))
    conn.commit()
    cur.execute("SELECT current_hp FROM wild_spawns WHERE chat_id=?", (chat_id,))
    row = cur.fetchone(); conn.close()
    return row["current_hp"] if row else 0

def add_pokemon_xp(poke_id, amount):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM user_pokemon WHERE poke_id=?", (poke_id,))
    poke = cur.fetchone()
    if not poke:
        conn.close(); return None
    level = poke["level"]; xp = poke["xp"] + amount
    leveled_up = False
    while level < 100 and xp >= xp_needed(level):
        xp -= xp_needed(level)
        level += 1
        leveled_up = True
    cur.execute("UPDATE user_pokemon SET level=?, xp=? WHERE poke_id=?", (level, xp, poke_id))
    conn.commit(); conn.close()
    return level, leveled_up

def catch_pokemon(user_id, chat_id, ball_type):
    wild = get_wild(chat_id)
    if not wild:
        return None, "no_wild", 0
    if not use_ball(user_id, ball_type):
        return None, "no_balls", 0
    species_row = get_species_by_id(wild["species_id"])
    if ball_type == "masterball":
        catch_chance = 1.0
    else:
        hp_frac = wild["current_hp"] / wild["max_hp"] if wild["max_hp"] else 1.0
        ball_bonus = {"pokeball": 1.0, "greatball": 1.5}[ball_type]
        base_rate = species_row["catch_rate"] / 255.0
        catch_chance = min(0.95, base_rate * ball_bonus * (1.5 - hp_frac))
    success = random.random() < catch_chance
    if success:
        shiny = wild["shiny"] if "shiny" in wild.keys() else 0
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""INSERT INTO user_pokemon (owner_id,species_id,level,xp,current_hp,in_team,team_slot,caught_at,shiny)
                       VALUES (?,?,?,0,?,0,NULL,?,?)""",
                    (user_id, wild["species_id"], wild["level"], wild["current_hp"], int(time.time()), shiny))
        conn.commit(); conn.close()
        clear_wild(chat_id)
        return species_row, "caught", shiny
    return species_row, "escaped", 0

def heal_team(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT poke_id, species_id, level FROM user_pokemon WHERE owner_id=? AND in_team=1", (user_id,))
    rows = cur.fetchall()
    healed = 0
    for r in rows:
        species_row = get_species_by_id(r["species_id"])
        stats = calc_stats(species_row, r["level"])
        cur.execute("UPDATE user_pokemon SET current_hp=? WHERE poke_id=?", (stats["hp"], r["poke_id"]))
        healed += 1
    conn.commit(); conn.close()
    return healed

def damage_pokemon(poke_id, dmg):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE user_pokemon SET current_hp = MAX(0, current_hp - ?) WHERE poke_id=?", (dmg, poke_id))
    conn.commit()
    cur.execute("SELECT current_hp FROM user_pokemon WHERE poke_id=?", (poke_id,))
    row = cur.fetchone(); conn.close()
    return row["current_hp"] if row else 0

# =========================
# EVOLUTION
# =========================

def check_evolution(poke_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM user_pokemon WHERE poke_id=?", (poke_id,))
    poke = cur.fetchone()
    if not poke:
        conn.close(); return None
    species_row = get_species_by_id(poke["species_id"])
    if species_row["evolves_to"] and species_row["evolve_level"] and poke["level"] >= species_row["evolve_level"]:
        new_species = get_species_by_id(species_row["evolves_to"])
        new_stats = calc_stats(new_species, poke["level"])
        cur.execute("UPDATE user_pokemon SET species_id=?, current_hp=? WHERE poke_id=?",
                    (species_row["evolves_to"], new_stats["hp"], poke_id))
        conn.commit(); conn.close()
        return species_row["name"], new_species["name"]
    conn.close(); return None

# =========================
# PVP POKEMON BATTLES
# =========================

def init_pvp_pokemon_db():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pvp_pokemon_battles (
            battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_a INTEGER, poke_a_id INTEGER, hp_a INTEGER, max_hp_a INTEGER,
            user_b INTEGER, poke_b_id INTEGER, hp_b INTEGER, max_hp_b INTEGER,
            turn INTEGER,
            status TEXT DEFAULT 'pending',
            created_at INTEGER
        )
    """)
    conn.commit(); conn.close()

def create_pvp_challenge(chat_id, challenger_id, opponent_id):
    team = get_team(challenger_id)
    if not team:
        return None, "no_team"
    fighter = team[0]
    stats = calc_stats(fighter, fighter["level"])
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM pvp_pokemon_battles WHERE chat_id=? AND status='pending'", (chat_id,))
    cur.execute("""INSERT INTO pvp_pokemon_battles (chat_id,user_a,poke_a_id,hp_a,max_hp_a,user_b,status,created_at)
                   VALUES (?,?,?,?,?,?,'pending',?)""",
                (chat_id, challenger_id, fighter["poke_id"], stats["hp"], stats["hp"], opponent_id, int(time.time())))
    conn.commit(); conn.close()
    return fighter, "challenged"

def accept_pvp_challenge(chat_id, opponent_id):
    team = get_team(opponent_id)
    if not team:
        return None, "no_team"
    fighter = team[0]
    stats = calc_stats(fighter, fighter["level"])
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM pvp_pokemon_battles WHERE chat_id=? AND user_b=? AND status='pending'", (chat_id, opponent_id))
    row = cur.fetchone()
    if not row:
        conn.close(); return None, "no_challenge"
    cur.execute("""UPDATE pvp_pokemon_battles SET poke_b_id=?, hp_b=?, max_hp_b=?, turn=?, status='active'
                   WHERE battle_id=?""", (fighter["poke_id"], stats["hp"], stats["hp"], row["user_a"], row["battle_id"]))
    conn.commit(); conn.close()
    return fighter, "accepted"

def get_active_pvp(chat_id, user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT * FROM pvp_pokemon_battles WHERE chat_id=? AND status='active'
                   AND (user_a=? OR user_b=?)""", (chat_id, user_id, user_id))
    row = cur.fetchone(); conn.close(); return row

def end_pvp_battle(battle_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM pvp_pokemon_battles WHERE battle_id=?", (battle_id,))
    conn.commit(); conn.close()

def pvp_attack(chat_id, user_id):
    battle = get_active_pvp(chat_id, user_id)
    if not battle:
        return None
    is_a = (battle["user_a"] == user_id)
    if battle["turn"] != user_id:
        return {"error": "not_your_turn"}

    my_poke_id = battle["poke_a_id"] if is_a else battle["poke_b_id"]
    opp_poke_id = battle["poke_b_id"] if is_a else battle["poke_a_id"]
    my_poke = get_pokemon_by_id(my_poke_id)
    opp_poke = get_pokemon_by_id(opp_poke_id)
    my_stats = calc_stats(my_poke, my_poke["level"])
    moves = get_species_moves(my_poke["species_id"], my_poke["level"])
    move = moves[-1] if moves else None
    if not move:
        return {"error": "no_move"}

    base_dmg = max(1, int(move["power"] * my_stats["atk"] / 50))
    mult = type_multiplier(move["type"], opp_poke["type1"], opp_poke["type2"])
    dmg = max(1, int(base_dmg * mult))

    conn = get_connection(); cur = conn.cursor()
    if is_a:
        new_hp = max(0, battle["hp_b"] - dmg)
        cur.execute("UPDATE pvp_pokemon_battles SET hp_b=?, turn=? WHERE battle_id=?", (new_hp, battle["user_b"], battle["battle_id"]))
    else:
        new_hp = max(0, battle["hp_a"] - dmg)
        cur.execute("UPDATE pvp_pokemon_battles SET hp_a=?, turn=? WHERE battle_id=?", (new_hp, battle["user_a"], battle["battle_id"]))
    conn.commit(); conn.close()

    result = {
        "attacker_name": my_poke["nickname"] or my_poke["name"],
        "defender_name": opp_poke["nickname"] or opp_poke["name"],
        "move_name": move["name"], "dmg": dmg, "mult": mult, "new_hp": new_hp,
        "max_hp": battle["max_hp_b"] if is_a else battle["max_hp_a"],
        "fainted": new_hp <= 0,
        "winner_id": user_id if new_hp <= 0 else None,
        "loser_id": (battle["user_b"] if is_a else battle["user_a"]) if new_hp <= 0 else None,
        "battle_id": battle["battle_id"],
    }
    return result

# =========================
# POKEMON TEAM / ELIGIBILITY / LEADERBOARD
# =========================

def init_pokemon_team_db():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_teams (
            user_id INTEGER PRIMARY KEY,
            team_name TEXT UNIQUE,
            joined_at INTEGER
        )
    """)
    conn.commit(); conn.close()

def has_joined_pokemon(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT team_name FROM pokemon_teams WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close()
    return row["team_name"] if row else None

def check_pokemon_eligibility(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT level, xp, coins FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close()
    if not row:
        return False, ["Account not found. Send /start first."]
    reasons = []
    if row["level"] < 3:
        reasons.append(f"Player level too low ({row['level']}/3 required)")
    if row["xp"] < 150:
        reasons.append(f"Not enough XP ({row['xp']}/150 required)")
    if row["coins"] < 3200:
        reasons.append(f"Not enough coins ({row['coins']}/3200 required) — try /work, /fight or /rob")
    return (len(reasons) == 0), reasons

def team_name_taken(name):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM pokemon_teams WHERE LOWER(team_name)=LOWER(?)", (name,))
    row = cur.fetchone(); conn.close()
    return row is not None

def join_pokemon_system(user_id, team_name):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO pokemon_teams (user_id, team_name, joined_at) VALUES (?,?,?)",
                (user_id, team_name, int(time.time())))
    conn.commit(); conn.close()

def get_pokemon_leaderboard(limit=10):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT user_id, team_name FROM pokemon_teams")
    teams = cur.fetchall()
    results = []
    for t in teams:
        cur.execute("SELECT level, xp FROM user_pokemon WHERE owner_id=? AND in_team=1", (t["user_id"],))
        team_pokemon = cur.fetchall()
        total = 0
        for p in team_pokemon:
            total += int(80 * (p["level"] - 1) * p["level"] / 2) + p["xp"]
        results.append((t["team_name"], t["user_id"], total))
    conn.close()
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]

# =========================
# POKEMON STEALING (PvP)
# =========================

def get_protection_remaining(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT protected_until FROM protection WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close()
    if not row:
        return 0
    return max(0, int(row["protected_until"]) - int(time.time()))

def init_steal_db():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS steal_battles (
            chat_id INTEGER,
            attacker_id INTEGER,
            target_id INTEGER,
            target_poke_id INTEGER,
            current_hp INTEGER,
            max_hp INTEGER,
            PRIMARY KEY (chat_id, attacker_id)
        )
    """)
    conn.commit(); conn.close()

def start_steal_battle(chat_id, attacker_id, target_id):
    team = get_team(target_id)
    if not team:
        return None, "no_target_team"
    my_team = get_team(attacker_id)
    if not my_team:
        return None, "no_my_team"
    target_poke = None
    for p in team:
        if p["current_hp"] > 0:
            target_poke = p
            break
    if not target_poke:
        return None, "target_all_fainted"
    max_hp = calc_stats(target_poke, target_poke["level"])["hp"]
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM steal_battles WHERE chat_id=? AND attacker_id=?", (chat_id, attacker_id))
    cur.execute("""INSERT INTO steal_battles (chat_id,attacker_id,target_id,target_poke_id,current_hp,max_hp)
                   VALUES (?,?,?,?,?,?)""",
                (chat_id, attacker_id, target_id, target_poke["poke_id"], target_poke["current_hp"], max_hp))
    conn.commit(); conn.close()
    return target_poke, "started"

def get_steal_battle(chat_id, attacker_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM steal_battles WHERE chat_id=? AND attacker_id=?", (chat_id, attacker_id))
    row = cur.fetchone(); conn.close()
    return row

def clear_steal_battle(chat_id, attacker_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM steal_battles WHERE chat_id=? AND attacker_id=?", (chat_id, attacker_id))
    conn.commit(); conn.close()

def damage_steal_target(chat_id, attacker_id, dmg):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""UPDATE steal_battles SET current_hp = MAX(0, current_hp - ?)
                   WHERE chat_id=? AND attacker_id=?""", (dmg, chat_id, attacker_id))
    conn.commit()
    cur.execute("SELECT current_hp FROM steal_battles WHERE chat_id=? AND attacker_id=?", (chat_id, attacker_id))
    row = cur.fetchone(); conn.close()
    return row["current_hp"] if row else 0

def steal_pokemon(user_id, chat_id, ball_type):
    battle = get_steal_battle(chat_id, user_id)
    if not battle:
        return None, "no_battle"
    if not use_ball(user_id, ball_type):
        return None, "no_balls"
    target_poke = get_pokemon_by_id(battle["target_poke_id"])
    if not target_poke:
        clear_steal_battle(chat_id, user_id)
        return None, "target_gone"
    species_row = get_species_by_id(target_poke["species_id"])
    if ball_type == "masterball":
        catch_chance = 1.0
    else:
        hp_frac = battle["current_hp"] / battle["max_hp"] if battle["max_hp"] else 1.0
        ball_bonus = {"pokeball": 1.0, "greatball": 1.5}[ball_type]
        base_rate = species_row["catch_rate"] / 255.0
        catch_chance = min(0.90, base_rate * ball_bonus * (1.5 - hp_frac) * 0.7)
    success = random.random() < catch_chance
    if success:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""UPDATE user_pokemon SET owner_id=?, in_team=0, team_slot=NULL, current_hp=?
                       WHERE poke_id=?""", (user_id, battle["current_hp"], target_poke["poke_id"]))
        conn.commit(); conn.close()
        clear_steal_battle(chat_id, user_id)
        return species_row, "stolen"
    return species_row, "escaped"
