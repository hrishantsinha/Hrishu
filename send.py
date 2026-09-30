import api, os, json, urllib.request as u
oid = os.getenv("OWNER_ID")
if not oid:
    for l in open(os.path.join(api.BASE, ".env")):
        if l.startswith("OWNER_ID"):
            oid = l.split("=", 1)[1].strip().strip("\"'")
d = json.dumps({"chat_id": int(oid), "text": "🎮 Hrishu Game is ready! Tap the button below.", "reply_markup": {"inline_keyboard": [[{"text": "🎮 Play Hrishu", "web_app": {"url": "https://colleagues-invited-concentrate-thermal.trycloudflare.com"}}]]}}).encode()
print(u.urlopen(u.Request("https://api.telegram.org/bot" + api.TOKEN + "/sendMessage", d, {"Content-Type": "application/json"})).read().decode()[:120])
