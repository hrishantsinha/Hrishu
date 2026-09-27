import sqlite3
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from telegram import Bot
from telegram.error import TelegramError

DB = "hrishu.db"
BONUS = 5000

MESSAGE = """🎉💖 HELLO KUCCHUUU PUCHHHUUSSS! 🥹🫶

I’m sooo glad to see you all again! 😭💗

⚠️ HRISHU got glitched due to high server load, but don’t worry…

🔥 WE’RE BACK AGAIN! 🚀✨

And we’re coming back with a small gift for you! 🎁💰

💸 +5,000 COINS have been added to your balance! 🤑✨

💰 Check your current balance:
 /bal

Thank you for staying with HRISHU while we got everything back up! 🫂❤️

🐻💖 Welcome back, Kucchuuu Puchhhuuusss!
"""

async def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found.")
        print("Make sure BOT_TOKEN exists in .env")
        return

    db = sqlite3.connect(DB)
    cur = db.cursor()

    # One-time protection using a dedicated table.
    # Do NOT touch the bot's existing bot_migrations table.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comeback_bonus_log (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            completed_at INTEGER NOT NULL
        )
    """)

    cur.execute(
        "SELECT 1 FROM comeback_bonus_log WHERE id = 1"
    )

    if cur.fetchone():
        print("❌ The 5,000 comeback bonus has already been given.")
        db.close()
        return

    users = cur.execute(
        "SELECT user_id FROM users"
    ).fetchall()

    print(f"👥 Found {len(users)} users.")
    print("💰 Adding 5,000 coins to everyone...")

    # Give the bonus to EVERY user exactly once.
    cur.execute("UPDATE users SET coins = coins + ?", (BONUS,))
    db.commit()

    print("✅ 5,000 coins added to every registered user.")

    bot = Bot(token=token)

    sent = 0
    failed = 0

    print("📩 Sending comeback messages by DM...")
    
    for (user_id,) in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=MESSAGE
            )

            sent += 1
            print(f"✅ DM sent: {user_id}")

            # Small delay to avoid hitting Telegram too quickly.
            await asyncio.sleep(0.05)

        except TelegramError as e:
            failed += 1
            print(f"⚠️ Could not DM {user_id}: {e}")

        except Exception as e:
            failed += 1
            print(f"⚠️ Error for {user_id}: {e}")

    # Mark the bonus as permanently completed.
    cur.execute(
        """
        INSERT INTO comeback_bonus_log (id, completed_at)
        VALUES (1, strftime('%s','now'))
        """
    )

    db.commit()
    db.close()

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎉 COMEBACK BONUS COMPLETE!")
    print(f"💰 Bonus: +{BONUS:,} coins")
    print(f"👥 Total users: {len(users)}")
    print(f"📩 DMs sent: {sent}")
    print(f"⚠️ DMs failed/skipped: {failed}")
    print("🛡️ Bonus locked as ONE-TIME.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    asyncio.run(main())
