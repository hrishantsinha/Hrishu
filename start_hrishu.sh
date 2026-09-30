#!/bin/bash

cd ~/Hrishu

echo "===== STARTING HRISHU ====="

# Stop old instances
pkill -f "uvicorn api:app" 2>/dev/null || true
pkill -f "cloudflared tunnel --url" 2>/dev/null || true

sleep 2

# Start API
nohup ./venv/bin/python -m uvicorn api:app \
  --host 0.0.0.0 \
  --port 8000 \
  > api.log 2>&1 &

sleep 3

# Verify API
if ! curl -fsS http://localhost:8000/ >/dev/null; then
    echo "ERROR: API failed."
    exit 1
fi

echo "API OK."

# Start Cloudflare Quick Tunnel
: > tunnel.log

nohup cloudflared tunnel --url http://localhost:8000 \
  > tunnel.log 2>&1 &

echo "Waiting for Cloudflare URL..."

URL=""

for i in {1..60}; do
    URL=$(grep -oE 'https://[-a-z0-9]+\.trycloudflare\.com' tunnel.log | tail -1)

    if [ -n "$URL" ]; then
        break
    fi

    sleep 1
done

if [ -z "$URL" ]; then
    echo "ERROR: Cloudflare URL not found."
    exit 1
fi

echo
echo "Hrishu WebApp:"
echo "$URL"

# Update send.py
sed -i -E \
"s#https://[-a-z0-9]+\.trycloudflare\.com#$URL#g" \
send.py 2>/dev/null || true

# Update Telegram menu
cat > set_menu.py <<PY
import api
import json
import urllib.request

URL = "$URL"

data = {
    "menu_button": {
        "type": "web_app",
        "text": "🎮 Play Hrishu",
        "web_app": {
            "url": URL
        }
    }
}

req = urllib.request.Request(
    "https://api.telegram.org/bot" + api.TOKEN + "/setChatMenuButton",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"}
)

print(urllib.request.urlopen(req).read().decode())
PY

echo
echo "Updating Telegram menu..."

./venv/bin/python set_menu.py

echo
echo "===== FINAL CHECK ====="

if curl -fsS "$URL/" >/dev/null; then
    echo "WebApp: ONLINE"
else
    echo "WebApp: FAILED"
    exit 1
fi

echo
echo "================================"
echo " HRISHU WEBAPP READY"
echo " $URL"
echo "================================"
