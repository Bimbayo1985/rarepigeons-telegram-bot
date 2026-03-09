import os
import time
import json
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LIST_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

IMAGE_BASE = "https://rarepigeons.com/cards/"

CHECK_INTERVAL = 15

STATE_FILE = "watcher_state.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# LOAD CARDS
# -----------------------------

cards_data = requests.get(LIST_JSON).json()["cards"]

CARDS = {}
ASSETS = []

for c in cards_data:

    asset = c["asset"]
    image = c["image"]

    if not image.startswith("http"):
        image = IMAGE_BASE + image

    CARDS[asset] = image
    ASSETS.append(asset)


# -----------------------------
# STATE
# -----------------------------

if os.path.exists(STATE_FILE):

    with open(STATE_FILE) as f:
        state = json.load(f)

else:

    state = {
        "dispenses": [],
        "dispensers": [],
        "orders": [],
        "matches": []
    }


def save_state():

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# -----------------------------
# TELEGRAM
# -----------------------------

def send_photo(asset, text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    data = {
        "chat_id": CHAT_ID,
        "photo": CARDS.get(asset),
        "caption": text
    }

    requests.post(url, data=data)


# -----------------------------
# DISPENSE SALES
# -----------------------------

def check_dispenses():

    for asset in ASSETS:

        url = f"https://tokenscan.io/api/dispenses/{asset}"

        r = requests.get(url, headers=HEADERS).json()

        for d in r["data"]:

            tx = d["tx_hash"]

            if tx in state["dispenses"]:
                continue

            state["dispenses"].append(tx)

            price = d["btc_amount"]

            text = f"""{asset} sold via dispenser

Price: {price} BTC
Amount: 1

TX
https://tokenscan.io/tx/{tx}
"""

            send_photo(asset, text)


# -----------------------------
# NEW DISPENSERS
# -----------------------------

def check_dispensers():

    for asset in ASSETS:

        url = f"https://tokenscan.io/api/dispensers/{asset}"

        r = requests.get(url, headers=HEADERS).json()

        for d in r["data"]:

            tx = d["tx_hash"]

            if tx in state["dispensers"]:
                continue

            state["dispensers"].append(tx)

            price = d["satoshi_price"]
            amount = d["give_remaining"]

            text = f"""{asset} listed via dispenser

Amount: {amount}
Price: {price} BTC

TX
https://tokenscan.io/tx/{tx}
"""

            send_photo(asset, text)


# -----------------------------
# ORDERS
# -----------------------------

def check_orders():

    url = "https://api.unspendablelabs.com:4000/v2/orders?status=open"

    r = requests.get(url, headers=HEADERS).json()

    for o in r["result"]:

        tx = o["tx_hash"]

        if tx in state["orders"]:
            continue

        give_asset = o["give_asset"]
        get_asset = o["get_asset"]

        if give_asset not in ASSETS and get_asset not in ASSETS:
            continue

        state["orders"].append(tx)

        if give_asset in ASSETS:

            text = f"""{give_asset} sell order

Sell: {o["give_quantity"]} {give_asset}
Price: {o["get_price"]} {get_asset}

TX
https://tokenscan.io/tx/{tx}
"""

            send_photo(give_asset, text)

        else:

            text = f"""{get_asset} buy order

Buy: {o["get_quantity"]} {get_asset}
Price: {o["give_price"]} {give_asset}

TX
https://tokenscan.io/tx/{tx}
"""

            send_photo(get_asset, text)


# -----------------------------
# MATCHES
# -----------------------------

def check_matches():

    url = "https://api.unspendablelabs.com:4000/v2/order_matches"

    r = requests.get(url, headers=HEADERS).json()

    for m in r["result"]:

        tx = m["tx_hash"]

        if tx in state["matches"]:
            continue

        asset = m["forward_asset"]

        if asset not in ASSETS:
            continue

        state["matches"].append(tx)

        text = f"""{asset} trade executed

Amount: {m["forward_quantity"]}

TX
https://tokenscan.io/tx/{tx}
"""

        send_photo(asset, text)


# -----------------------------
# LOOP
# -----------------------------

print("Watcher started")

while True:

    try:

        check_dispenses()
        check_dispensers()
        check_orders()
        check_matches()

        save_state()

    except Exception as e:

        print("Watcher error:", e)

    time.sleep(CHECK_INTERVAL)
