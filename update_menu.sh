#!/bin/bash
cd "$HOME/Hrishu" || exit 1
URL=""
for i in $(seq 1 90); do
  URL=$(grep -oE 'https://[-a-z0-9]+\.trycloudflare\.com' tunnel.log | grep -v '//api\.' | tail -1)
  [ -n "$URL" ] && break
  sleep 1
done
[ -z "$URL" ] && { echo "No tunnel URL found"; exit 1; }
for i in $(seq 1 30); do
  curl -fsS -m 5 "$URL/" >/dev/null && break
  sleep 2
done
sed -i -E "s#https://[-a-z0-9]+\.trycloudflare\.com#$URL#g" send.py 2>/dev/null || true
./venv/bin/python set_menu.py "$URL"
echo "Menu updated: $URL"
