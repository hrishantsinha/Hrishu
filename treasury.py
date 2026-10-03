import os, sqlite3
from telegram.ext import CommandHandler

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hrishu.db")
SEED = 500000        # starting treasury coins
EMERGENCY = 0.25     # if treasury can't cover a reward, this share of the shortfall is newly minted


def _c():
    c = sqlite3.connect(DB, timeout=10)
    c.execute("create table if not exists treasury (id integer primary key, balance integer not null, "
              "minted integer default 0, collected integer default 0, paid integer default 0)")
    c.execute("insert or ignore into treasury (id, balance) values (1, ?)", (SEED,))
    c.commit()
    return c


def stats():
    c = _c()
    r = c.execute("select balance, collected, paid, minted from treasury where id=1").fetchone()
    c.close()
    return r


def deposit(n):
    n = int(n)
    if n <= 0:
        return
    c = _c()
    c.execute("update treasury set balance=balance+?, collected=collected+? where id=1", (n, n))
    c.commit()
    c.close()


def payout(amount):
    amount = int(amount)
    c = _c()
    bal = c.execute("select balance from treasury where id=1").fetchone()[0]
    if bal >= amount:
        pay, mint = amount, 0
        c.execute("update treasury set balance=balance-?, paid=paid+? where id=1", (amount, amount))
    else:
        mint = int((amount - bal) * EMERGENCY)
        pay = bal + mint
        c.execute("update treasury set balance=0, paid=paid+?, minted=minted+? where id=1", (bal, mint))
    c.commit()
    c.close()
    return pay


def spend(n):
    deposit(n)
    return int(n)


async def treasury_cmd(update, ctx):
    b, col, paid, minted = stats()
    await update.message.reply_text(
        "🏦 Government Treasury\n\n"
        "💰 Balance: {:,}\n📥 Taxes collected: {:,}\n📤 Paid to players: {:,}\n🪙 Emergency minted: {:,}".format(
            b, col, paid, minted))


def register(app):
    h = CommandHandler("treasury", treasury_cmd)
    app.add_handler(h)
    app.handlers[0].remove(h)
    app.handlers[0].insert(0, h)
