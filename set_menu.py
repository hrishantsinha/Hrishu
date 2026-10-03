import api
import json
import urllib.request

URL = "https://accurately-configuration-airline-limits.trycloudflare.com"

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
