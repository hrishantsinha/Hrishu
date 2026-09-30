import os, hmac, hashlib, json, time, sqlite3
from urllib.parse import parse_qsl
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

BASE = os.path.dirname(os.path.abspath(__file__))

def _token():
    t = os.getenv("BOT_TOKEN")
    if t:
        return t
    try:
        for line in open(os.path.join(BASE, ".env")):
            if line.startswith("BOT_TOKEN"):
                return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""

TOKEN = _token()
app = FastAPI()

def check(init_data):
    d = dict(parse_qsl(init_data, keep_blank_values=True))
    h = d.pop("hash", None)
    if not h or not TOKEN:
        raise HTTPException(401, "bad auth")
    s = "\n".join(f"{k}={v}" for k, v in sorted(d.items()))
    key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(hmac.new(key, s.encode(), hashlib.sha256).hexdigest(), h):
        raise HTTPException(401, "bad auth")
    if time.time() - int(d.get("auth_date", 0)) > 86400:
        raise HTTPException(401, "expired")
    return json.loads(d["user"])

@app.get("/api/me")
def me(x_init_data: str = Header("")):
    print("AUTH DEBUG: len=", len(x_init_data), "has_hash=", "hash=" in x_init_data, "has_user=", "user=" in x_init_data)
    u = check(x_init_data)
    c = sqlite3.connect(os.path.join(BASE, "hrishu.db"))
    c.row_factory = sqlite3.Row
    r = c.execute("select first_name,username,coins,bank,xp,level,kills,deaths,robs,hp,max_hp from users where user_id=?", (u["id"],)).fetchone()
    c.close()
    if not r:
        raise HTTPException(404, "Send /start to the bot first")
    return dict(r)

@app.get("/")
def home():
    return FileResponse(os.path.join(BASE, "webapp", "index.html"))

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "webapp")), name="static")


def db():
    c = sqlite3.connect(os.path.join(BASE, "hrishu.db"))
    c.row_factory = sqlite3.Row
    return c

@app.get("/api/rank")
def rank(x_init_data: str = Header("")):
    u = check(x_init_data)
    c = db()
    top = [dict(r) for r in c.execute("select user_id,first_name,username,xp,level from users where hrishu_id != '69988' order by xp desc limit 12")]
    mine = c.execute("select xp from users where user_id=?", (u["id"],)).fetchone()
    pos = None
    if mine:
        pos = c.execute("select count(*)+1 from users where hrishu_id != '69988' and xp > ?", (mine["xp"],)).fetchone()[0]
    c.close()
    for t in top:
        t["me"] = t.pop("user_id") == u["id"]
    return {"top": top, "pos": pos}

@app.get("/api/arena")
def arena(x_init_data: str = Header("")):
    u = check(x_init_data)
    c = db()
    r = c.execute("select hp,max_hp,kills,deaths,robs,sword_durability,shield_durability,sword_upgrade,power_hp_level,power_attack_level,power_sword_level,power_durability_level,power_shield_level from users where user_id=?", (u["id"],)).fetchone()
    c.close()
    if not r:
        raise HTTPException(404, "Send /start to the bot first")
    return dict(r)


from fastapi import Body
SHOP_PRICE = {"sword": 2500, "shield": 2000, "potion": 500}
SHOP_SQL = "select coins,inventory,sword_durability,shield_durability,swords_bought,shields_bought from users where user_id=?"

def shop_state(r):
    inv = [x for x in (r["inventory"] or "").split(",") if x]
    return {
        "coins": r["coins"],
        "sword": {"price": int(2500 * 1.20 ** r["swords_bought"]), "owned": r["sword_durability"] > 0},
        "shield": {"price": int(2000 * 1.20 ** r["shields_bought"]), "owned": r["shield_durability"] > 0},
        "potion": {"price": 500, "count": inv.count("potion")},
    }

@app.get("/api/shop")
def shop_get(x_init_data: str = Header("")):
    u = check(x_init_data)
    c = db()
    r = c.execute(SHOP_SQL, (u["id"],)).fetchone()
    c.close()
    if not r:
        raise HTTPException(404, "Send /start to the bot first")
    return shop_state(r)

@app.post("/api/buy")
def shop_buy(body: dict = Body(...), x_init_data: str = Header("")):
    u = check(x_init_data)
    item = str(body.get("item", ""))
    if item not in SHOP_PRICE:
        raise HTTPException(400, "Item not found")
    c = db()
    c.isolation_level = None
    try:
        c.execute("begin immediate")
        r = c.execute(SHOP_SQL, (u["id"],)).fetchone()
        if not r:
            raise HTTPException(404, "Send /start to the bot first")
        st = shop_state(r)
        price = st[item]["price"]
        if item != "potion" and st[item]["owned"]:
            raise HTTPException(400, "You already have one equipped")
        if r["coins"] < price:
            raise HTTPException(400, "Not enough coins (need %s)" % format(price, ","))
        if item == "sword":
            c.execute("update users set coins=coins-?, sword_durability=12, sword_upgrade=0, swords_bought=swords_bought+1 where user_id=?", (price, u["id"]))
        elif item == "shield":
            c.execute("update users set coins=coins-?, shield_durability=4, shields_bought=shields_bought+1 where user_id=?", (price, u["id"]))
        else:
            inv = [x for x in (r["inventory"] or "").split(",") if x] + ["potion"]
            c.execute("update users set coins=coins-?, inventory=? where user_id=?", (price, ",".join(inv), u["id"]))
        c.execute("commit")
        return shop_state(c.execute(SHOP_SQL, (u["id"],)).fetchone())
    except Exception:
        if c.in_transaction:
            c.execute("rollback")
        raise
    finally:
        c.close()


POWERS = {
    "hp": ("power_hp_level", "power_hp_upgrades", 7.0),
    "attack": ("power_attack_level", "power_attack_upgrades", 4.5),
    "shield": ("power_shield_level", "power_shield_upgrades", 2.0),
    "defense": ("power_durability_level", "power_durability_upgrades", 2.0),
}
PW_SQL = "select coins,xp,hp,max_hp,power_hp_level,power_hp_upgrades,power_attack_level,power_attack_upgrades,power_shield_level,power_shield_upgrades,power_durability_level,power_durability_upgrades from users where user_id=?"

def pw_mult(level, upgrades, maximum):
    total = (level - 1) * 10 + upgrades
    if maximum == 7.0:
        m = 1.0 + total * 0.10
    elif maximum == 4.5:
        m = 1.0 + total * (3.5 / 60)
    else:
        m = 1.0 + total * (1.0 / 60)
    return min(m, maximum)

def pw_cost(level, upgrades):
    p = (level - 1) * 10 + upgrades
    return 400 + p * 100, 100 + p * 25

def pw_state(r):
    out = {"coins": r["coins"], "xp": r["xp"], "hp": r["hp"], "max_hp": r["max_hp"]}
    for k, (lf, uf, mx) in POWERS.items():
        lv = int(r[lf] or 1)
        up = int(r[uf] or 0)
        co, xp = pw_cost(lv, up)
        out[k] = {"level": lv, "upgrades": up, "mult": pw_mult(lv, up, mx), "coins": co, "xp": xp}
    return out

@app.get("/api/power")
def power_get(x_init_data: str = Header("")):
    u = check(x_init_data)
    c = db()
    r = c.execute(PW_SQL, (u["id"],)).fetchone()
    c.close()
    if not r:
        raise HTTPException(404, "Send /start to the bot first")
    return pw_state(r)

@app.post("/api/power")
def power_up(body: dict = Body(...), x_init_data: str = Header("")):
    u = check(x_init_data)
    k = str(body.get("type", ""))
    if k not in POWERS:
        raise HTTPException(400, "Invalid power")
    lf, uf, mx = POWERS[k]
    c = db()
    c.isolation_level = None
    try:
        c.execute("begin immediate")
        r = c.execute(PW_SQL, (u["id"],)).fetchone()
        if not r:
            raise HTTPException(404, "Send /start to the bot first")
        lv = int(r[lf] or 1)
        up = int(r[uf] or 0)
        if lv >= 7:
            raise HTTPException(400, "This power is already MAX LEVEL")
        co, xp = pw_cost(lv, up)
        if r["coins"] < co:
            raise HTTPException(400, "You need %s coins" % format(co, ","))
        if r["xp"] < xp:
            raise HTTPException(400, "You need %s XP" % format(xp, ","))
        up += 1
        leveled = False
        if up >= 10:
            up = 0
            lv += 1
            leveled = True
        c.execute("update users set coins=coins-?, xp=xp-?, %s=?, %s=? where user_id=?" % (lf, uf), (co, xp, lv, up, u["id"]))
        if k == "hp":
            nm = max(100, int(round(100 * pw_mult(lv, up, 7.0))))
            c.execute("update users set max_hp=?, hp=min(hp,?) where user_id=?", (nm, nm, u["id"]))
        c.execute("commit")
        s = pw_state(c.execute(PW_SQL, (u["id"],)).fetchone())
        s["leveled"] = leveled
        return s
    except Exception:
        if c.in_transaction:
            c.execute("rollback")
        raise
    finally:
        c.close()


import urllib.request, urllib.parse
PFP_DIR = os.path.join(BASE, "pfp_cache")
os.makedirs(PFP_DIR, exist_ok=True)

@app.get("/api/pfps")
def pfps_get(x_init_data: str = Header("")):
    u = check(x_init_data)
    c = db()
    rows = c.execute("select pfp_id,title,price,media_type from hrishu_pfps where file_id is not null and file_id != '' order by cast(substr(pfp_id,4) as integer)").fetchall()
    owned = {r[0] for r in c.execute("select pfp_id from hrishu_pfp_owned where user_id=?", (u["id"],))}
    eq = c.execute("select pfp_id from hrishu_pfp_equipped where user_id=?", (u["id"],)).fetchone()
    co = c.execute("select coins from users where user_id=?", (u["id"],)).fetchone()
    c.close()
    return {
        "coins": co[0] if co else 0,
        "equipped": eq[0] if eq else None,
        "items": [{"id": r["pfp_id"], "title": r["title"], "price": r["price"], "media": r["media_type"], "owned": r["pfp_id"] in owned} for r in rows],
    }

@app.get("/api/pfpimg/{pid}")
def pfp_img(pid: str):
    safe = "".join(ch for ch in pid if ch.isalnum())
    hdr = {"Cache-Control": "public, max-age=86400"}
    for f in os.listdir(PFP_DIR):
        if f.startswith(safe + "."):
            return FileResponse(os.path.join(PFP_DIR, f), headers=hdr)
    c = db()
    r = c.execute("select file_id from hrishu_pfps where pfp_id=?", (pid,)).fetchone()
    c.close()
    if not r:
        raise HTTPException(404, "not found")
    try:
        j = json.loads(urllib.request.urlopen("https://api.telegram.org/bot%s/getFile?file_id=%s" % (TOKEN, urllib.parse.quote(r["file_id"])), timeout=20).read())
        path = j["result"]["file_path"]
        data = urllib.request.urlopen("https://api.telegram.org/file/bot%s/%s" % (TOKEN, path), timeout=40).read()
    except Exception:
        raise HTTPException(502, "could not load image")
    ext = path.rsplit(".", 1)[-1] if "." in path else "jpg"
    fn = os.path.join(PFP_DIR, safe + "." + ext)
    with open(fn, "wb") as fh:
        fh.write(data)
    return FileResponse(fn, headers=hdr)


@app.post("/api/pfp")
def pfp_act(body: dict = Body(...), x_init_data: str = Header("")):
    u = check(x_init_data)
    pid = str(body.get("id", ""))
    act = str(body.get("act", ""))
    if act not in ("buy", "equip"):
        raise HTTPException(400, "Invalid action")
    c = db()
    c.isolation_level = None
    try:
        c.execute("begin immediate")
        p = c.execute("select pfp_id,price from hrishu_pfps where pfp_id=?", (pid,)).fetchone()
        if not p:
            raise HTTPException(404, "PFP not found")
        owned = c.execute("select 1 from hrishu_pfp_owned where user_id=? and pfp_id=?", (u["id"], pid)).fetchone()
        if act == "buy":
            if owned:
                raise HTTPException(400, "You already own this PFP")
            n = c.execute("update users set coins=coins-? where user_id=? and coins>=?", (p["price"], u["id"], p["price"])).rowcount
            if n == 0:
                raise HTTPException(400, "You need %s coins" % format(p["price"], ","))
            c.execute("insert into hrishu_pfp_owned (user_id,pfp_id,purchased_at) values (?,?,?)", (u["id"], pid, int(time.time())))
        else:
            if not owned:
                raise HTTPException(400, "Buy this PFP first")
            c.execute("insert or replace into hrishu_pfp_equipped (user_id,pfp_id) values (?,?)", (u["id"], pid))
        c.execute("commit")
        return {"ok": True}
    except Exception:
        if c.in_transaction:
            c.execute("rollback")
        raise
    finally:
        c.close()
