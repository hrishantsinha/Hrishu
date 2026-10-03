import asyncio, random, string, html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
import database as db

GAMES = {}
JOIN_SECS = 120
TURN_SECS = 120


def mention(p):
    return '<a href="tg://user?id=%d">%s</a>' % (p["id"], html.escape(p["name"]))


def coins(uid):
    try:
        return int(db.get_coins(uid) or 0)
    except Exception:
        return 0


def give(p, nums):
    for n in nums:
        k = next(c for c in string.ascii_lowercase if c not in p["hand"])
        p["hand"][k] = n


async def send_hand(bot, p):
    body = "  ".join("%s = %d" % (k.upper(), v) for k, v in sorted(p["hand"].items())) or "none"
    try:
        await bot.send_message(p["id"], "🎴 Your cards:\n" + body + "\n\nPlay in the group: /drop a  or  /drop a b c")
    except Exception:
        pass


async def announce(bot, g, extra=""):
    p = g["players"][g["turn"]]
    g["need"] = random.randint(1, 4)
    g["tid"] += 1
    counts = " | ".join("%s: %d" % (html.escape(x["name"]), len(x["hand"])) for x in g["players"])
    t = extra + "🃏 %s's turn - Hrishu says drop <b>%d</b>!\n" % (mention(p), g["need"])
    t += "Pile: %d cards\nCards left: %s\n" % (len(g["pile"]), counts)
    if g["win"]:
        t += "⚠️ %s has 0 cards! /judge now or they win!\n" % mention(g["win"])
    if g["last"]:
        t += "Options: /drop a b ...  or  /judge\n"
    else:
        t += "Use: /drop a b ...\n"
    t += "⏳ %d min" % (TURN_SECS // 60)
    await bot.send_message(g["chat"], t, parse_mode="HTML")
    asyncio.create_task(turn_timer(bot, g, g["tid"]))


async def cancel(bot, g, msg):
    g["over"] = True
    if GAMES.get(g["chat"]) is g:
        GAMES.pop(g["chat"])
    if g["bet"]:
        for p in g["players"]:
            db.add_coins(p["id"], g["bet"])
    await bot.send_message(g["chat"], msg)


async def finish(bot, g, w, msg=""):
    g["over"] = True
    if GAMES.get(g["chat"]) is g:
        GAMES.pop(g["chat"])
    pot = g["bet"] * len(g["players"])
    if pot:
        _tax = pot * 5 // 100
        try:
            import treasury
            treasury.deposit(_tax)
        except Exception:
            _tax = 0
        pot -= _tax
        db.add_coins(w["id"], pot)
    t = msg + "\n🏆 %s wins Hrishu Bluff!" % mention(w)
    if pot:
        t += " +%d coins (5%% tax went to the treasury)" % pot
    await bot.send_message(g["chat"], t, parse_mode="HTML")


async def turn_timer(bot, g, tid):
    await asyncio.sleep(TURN_SECS)
    if g["over"] or g["tid"] != tid:
        return
    p = g["players"][g["turn"]]
    g["idle"] += 1
    if g["idle"] >= 3:
        return await cancel(bot, g, "💤 Nobody is playing. Game cancelled, bets refunded.")
    if g["win"]:
        return await finish(bot, g, g["win"], "⏰ %s timed out." % mention(p))
    n = len(g["pile"])
    give(p, g["pile"])
    g["pile"] = []
    g["last"] = None
    await send_hand(bot, p)
    g["turn"] = (g["turn"] + 1) % len(g["players"])
    await announce(bot, g, "⏰ %s timed out and took %d pile cards!\n\n" % (mention(p), n))


async def join_timer(bot, g):
    await asyncio.sleep(JOIN_SECS)
    if g["over"] or g["started"]:
        return
    ps = g["players"]
    if len(ps) < 2:
        return await cancel(bot, g, "❌ Not enough players. Game cancelled (bets refunded).")
    g["started"] = True
    n = len(ps)
    deck = [x for x in range(1, 5) for _ in range(n)]
    random.shuffle(deck)
    for i, p in enumerate(ps):
        give(p, deck[i * 4:(i + 1) * 4])
    random.shuffle(ps)
    for p in ps:
        await send_hand(bot, p)
    g["turn"] = 0
    await announce(bot, g, "🎴 Cards sent in DM! Players: %d\n\n" % n)


async def add_player(ctx, g, u, reply):
    if any(p["id"] == u.id for p in g["players"]):
        await reply("You already joined.")
        return False
    if len(g["players"]) >= 6:
        await reply("Game is full (6 players).")
        return False
    if g["bet"] and coins(u.id) < g["bet"]:
        await reply("Not enough coins for the %d bet." % g["bet"])
        return False
    try:
        await ctx.bot.send_message(u.id, "✅ You joined Hrishu Bluff! Your cards will arrive here.")
    except Exception:
        await reply("Open me in DM first: https://t.me/%s then /enter again" % ctx.bot.username)
        return False
    if g["bet"]:
        db.add_coins(u.id, -g["bet"])
    g["players"].append({"id": u.id, "name": u.first_name or "Player", "hand": {}})
    return True


async def bluff(update, ctx):
    m, u, chat = update.effective_message, update.effective_user, update.effective_chat
    if chat.type == "private":
        return await m.reply_text("Use /bluff in a group.")
    if ctx.args and ctx.args[0].lower() == "leave":
        return await leave(update, ctx)
    if chat.id in GAMES:
        return await m.reply_text("A Hrishu game is already running here.")
    bet = 0
    if ctx.args:
        try:
            bet = int(ctx.args[0])
        except ValueError:
            return await m.reply_text("Usage: /bluff  or  /bluff 500")
        if bet < 0:
            return await m.reply_text("Bet can't be negative.")
    g = {"chat": chat.id, "bet": bet, "players": [], "started": False, "over": False, "pile": [],
         "last": None, "win": None, "turn": 0, "need": 1, "tid": 0, "idle": 0}
    GAMES[chat.id] = g
    if not await add_player(ctx, g, u, m.reply_text):
        GAMES.pop(chat.id, None)
        return
    await m.reply_text("🃏 HRISHU BLUFF! Entry bet: %d coins\nType /enter to join. Starts in 2 minutes." % bet)
    asyncio.create_task(join_timer(ctx.bot, g))


async def enter(update, ctx):
    m, u, chat = update.effective_message, update.effective_user, update.effective_chat
    g = GAMES.get(chat.id)
    if not g or g["started"]:
        return await m.reply_text("No game open. Start one with /bluff")
    if await add_player(ctx, g, u, m.reply_text):
        await m.reply_text("✅ %s joined! Players: %d" % (u.first_name, len(g["players"])))


def cur(update):
    g = GAMES.get(update.effective_chat.id)
    if not g or not g["started"] or g["over"]:
        return None, None
    p = g["players"][g["turn"]]
    return g, (p if p["id"] == update.effective_user.id else None)


async def drop(update, ctx):
    m = update.effective_message
    g, p = cur(update)
    if not g:
        return
    if not p:
        return await m.reply_text("Not your turn.")
    if g["win"]:
        return await finish(ctx.bot, g, g["win"], "%s didn't judge." % mention(p))
    keys = [a.lower() for a in ctx.args]
    if not keys or len(set(keys)) != len(keys) or any(k not in p["hand"] for k in keys):
        return await m.reply_text("Usage: /drop a  or  /drop a b c (letters from your DM cards)")
    cards = [p["hand"].pop(k) for k in keys]
    g["pile"] += cards
    g["last"] = {"pid": p["id"], "cards": cards, "claim": g["need"]}
    g["idle"] = 0
    g["tid"] += 1
    await send_hand(ctx.bot, p)
    if not p["hand"]:
        g["win"] = p
    g["turn"] = (g["turn"] + 1) % len(g["players"])
    await announce(ctx.bot, g, "%s dropped %d card(s) as %ds.\n\n" % (mention(p), len(cards), g["last"]["claim"]))


async def judge(update, ctx):
    m = update.effective_message
    g, p = cur(update)
    if not g:
        return
    if not p:
        return await m.reply_text("Not your turn.")
    if not g["last"]:
        return await m.reply_text("Nothing to judge yet. Use /drop")
    last = g["last"]
    bluffer = next(x for x in g["players"] if x["id"] == last["pid"])
    truth = all(c == last["claim"] for c in last["cards"])
    pile = g["pile"]
    g["pile"], g["last"], g["idle"] = [], None, 0
    g["tid"] += 1
    if truth:
        give(p, pile)
        res = "❌ %s judged WRONG! The cards were real. They take %d pile cards.\n" % (mention(p), len(pile))
        await send_hand(ctx.bot, p)
        if g["win"]:
            return await finish(ctx.bot, g, g["win"], res)
    else:
        give(bluffer, pile)
        g["win"] = None
        if p["hand"]:
            p["hand"].pop(random.choice(list(p["hand"])))
        res = "✅ %s caught a BLUFF! %s takes %d pile cards and %s loses 1 card.\n" % (
            mention(p), mention(bluffer), len(pile), html.escape(p["name"]))
        await send_hand(ctx.bot, bluffer)
        await send_hand(ctx.bot, p)
        if not p["hand"]:
            return await finish(ctx.bot, g, p, res)
    await announce(ctx.bot, g, res + "\n")


async def cards(update, ctx):
    uid = update.effective_user.id
    for g in GAMES.values():
        for p in g["players"]:
            if p["id"] == uid and g["started"]:
                return await send_hand(ctx.bot, p)


def lv_text(g):
    yes = [p for p in g["players"] if p["id"] in g["lv"]["yes"]]
    return "🚪 <b>Leave vote</b>\n✅ Accepted: %d/%d\n%s\nAll players must accept to end the game." % (
        len(yes), len(g["players"]), ", ".join(html.escape(p["name"]) for p in yes))


def lv_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Accept", callback_data="bkleave_yes"),
                                  InlineKeyboardButton("❌ Decline", callback_data="bkleave_no")]])


async def leave(update, ctx):
    m, u, chat = update.effective_message, update.effective_user, update.effective_chat
    g = GAMES.get(chat.id)
    if not g or g["over"]:
        return await m.reply_text("No game running here.")
    if not any(p["id"] == u.id for p in g["players"]):
        return await m.reply_text("You're not in this game.")
    if g.get("lv"):
        return await m.reply_text("A leave vote is already open. Use its buttons.")
    g["lv"] = {"yes": {u.id}}
    await m.reply_text(lv_text(g), parse_mode="HTML", reply_markup=lv_kb())


async def leave_cb(update, ctx):
    q = update.callback_query
    g = GAMES.get(q.message.chat.id)
    if not g or g["over"] or not g.get("lv"):
        return await q.answer("This vote is over.", show_alert=True)
    uid = q.from_user.id
    me = next((p for p in g["players"] if p["id"] == uid), None)
    if not me:
        return await q.answer("Only players in this game can vote.", show_alert=True)
    if q.data == "bkleave_no":
        g["lv"] = None
        await q.answer()
        return await q.edit_message_text("❌ %s declined. Game continues." % mention(me), parse_mode="HTML")
    if uid in g["lv"]["yes"]:
        return await q.answer("You already accepted.")
    g["lv"]["yes"].add(uid)
    await q.answer("Accepted")
    if len(g["lv"]["yes"]) >= len(g["players"]):
        await q.edit_message_text("✅ %d/%d accepted. Game ended." % (len(g["players"]), len(g["players"])))
        return await cancel(ctx.bot, g, "🚪 Everyone left. Game ended, bets refunded.")
    await q.edit_message_text(lv_text(g), parse_mode="HTML", reply_markup=lv_kb())


def register(app):
    hs = [CommandHandler(n, f) for n, f in (("bluff", bluff), ("enter", enter), ("drop", drop),
                                            ("judge", judge), ("cards", cards), ("bluffleave", leave))]
    hs.append(CallbackQueryHandler(leave_cb, pattern=r"^bkleave_"))
    for h in hs:
        app.add_handler(h)
        app.handlers[0].remove(h)
        app.handlers[0].insert(0, h)
