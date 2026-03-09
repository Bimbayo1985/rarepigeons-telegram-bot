import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LIST_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

IMAGE_BASE = "https://rarepigeons.com/cards/"

HEADERS = {"User-Agent": "Mozilla/5.0"}

CHECK_INTERVAL = 15


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
# MEMORY (avoid duplicates)
# -----------------------------

seen_dispenses = set()
seen_dispensers = set()
seen_orders = set()
seen_matches = set()


# -----------------------------
# DISPENSER SALES
# -----------------------------

def check_dispenses():

    for asset in ASSETS:

        url = f"https://tokenscan.io/api/dispenses/{asset}"

        r = requests.get(url, headers=HEADERS).json()

        for d in r["data"]:

            tx = d["tx_hash"]

            if tx in seen_dispenses:
                continue

            seen_dispenses.add(tx)

            price = d["btc_amount"]
            buyer = d["address"]

            text = f"""
{asset} sold via dispenser

Price: {price} BTC
Buyer: {buyer}

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

            if tx in seen_dispensers:
                continue

            seen_dispensers.add(tx)

            price = d["satoshi_price"]
            amount = d["give_remaining"]

            text = f"""
{asset} listed via dispenser

Amount: {amount}
Price: {price} BTC

https://tokenscan.io/tx/{tx}
"""

            send_photo(asset, text)


# -----------------------------
# MARKET ORDERS
# -----------------------------

def check_orders():

    url = "https://api.unspendablelabs.com:4000/v2/orders?status=open"

    r = requests.get(url, headers=HEADERS).json()

    for o in r["result"]:

        tx = o["tx_hash"]

        if tx in seen_orders:
            continue

        give_asset = o["give_asset"]
        get_asset = o["get_asset"]

        if give_asset not in ASSETS and get_asset not in ASSETS:
            continue

        seen_orders.add(tx)

        give_qty = o["give_quantity"]
        get_qty = o["get_quantity"]

        if give_asset in ASSETS:

            price = (get_qty / 1e8) / give_qty

            text = f"""
Sell order

{give_asset} → {get_asset}

Price: {price} {get_asset}

https://tokenscan.io/tx/{tx}
"""

            send_photo(give_asset, text)

        else:

            price = (give_qty / 1e8) / get_qty

            text = f"""
Buy order

{get_asset} ← {give_asset}

Price: {price} {give_asset}

https://tokenscan.io/tx/{tx}
"""

            send_photo(get_asset, text)


# -----------------------------
# ORDER MATCHES
# -----------------------------

def check_matches():

    url = "https://api.unspendablelabs.com:4000/v2/order_matches"

    r = requests.get(url, headers=HEADERS).json()

    for m in r["result"]:

        tx = m["tx_hash"]

        if tx in seen_matches:
            continue

        asset = m["forward_asset"]

        if asset not in ASSETS:
            continue

        seen_matches.add(tx)

        text = f"""
{asset} trade executed

https://tokenscan.io/tx/{tx}
"""

        send_photo(asset, text)


# -----------------------------
# MAIN LOOP
# -----------------------------

print("Watcher running")

while True:

    try:

        check_dispenses()
        check_dispensers()
        check_orders()
        check_matches()

    except Exception as e:

        print("Watcher error:", e)

    time.sleep(CHECK_INTERVAL)
