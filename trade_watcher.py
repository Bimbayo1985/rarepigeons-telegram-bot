import requests
import time
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

API = "https://api.unspendablelabs.com/v2"
SAT = 100000000

LIST_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/refs/heads/main/list.json"

SEEN_FILE = "seen.json"

session = requests.Session()


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


seen = load_seen()


def send_photo(url, caption):

    tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:
        session.post(
            tg,
            data={
                "chat_id": CHAT_ID,
                "photo": url,
                "caption": caption
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)


def load_cards():

    try:

        r = session.get(LIST_URL, timeout=30)
        data = r.json()

        cards = set()
        images = {}

        for c in data["cards"]:

            asset = c["asset"]
            img = c.get("image")

            cards.add(asset)
            images[asset] = img

        print("Cards loaded:", len(cards))

        return cards, images

    except Exception as e:

        print("Card load error:", e)
        return set(), {}


def norm(q):
    return round(q / SAT, 8)


cards, images = load_cards()
print("WATCHER STARTED")

def process_dispenses():

    r = session.get(f"{API}/dispenses?limit=30", timeout=30).json()

    for d in r["result"]:

        asset = d["asset"]

        if asset not in cards:
            continue

        tx = d["tx_hash"]

        if tx in seen:
            continue

        seen.add(tx)

        qty = d["dispense_quantity"]
        btc = norm(d["btc_amount"])

        img = images.get(asset)

        caption = f"""{asset} sold via dispenser

Price: {btc} BTC
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

        print("Dispenser sale:", asset)

        send_photo(img, caption)


def process_dispenser_open():

    r = session.get(f"{API}/dispensers?status=0&limit=30", timeout=30).json()

    for d in r["result"]:

        asset = d["asset"]

        if asset not in cards:
            continue

        tx = d["tx_hash"]

        if tx in seen:
            continue

        seen.add(tx)

        price = norm(d["satoshirate"])

        img = images.get(asset)

        caption = f"""{asset} dispenser opened

Price: {price} BTC

https://tokenscan.io/tx/{tx}
"""

        print("Dispenser opened:", asset)

        send_photo(img, caption)


def process_orders():

    r = session.get(f"{API}/orders?limit=30", timeout=30).json()

    for o in r["result"]:

        tx = o["tx_hash"]

        if tx in seen:
            continue

        give_asset = o["give_asset"]
        get_asset = o["get_asset"]

        if give_asset in cards:

            qty = norm(o["give_remaining"])
            if qty == 0:
                continue

            price = norm(o["get_remaining"]) / qty

            seen.add(tx)

            img = images.get(give_asset)

            caption = f"""{give_asset} sell order placed

Price: {round(price,8)} {get_asset}
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

            print("Sell order:", give_asset)

            send_photo(img, caption)

        elif get_asset in cards:

            qty = norm(o["get_remaining"])
            if qty == 0:
                continue

            price = norm(o["give_remaining"]) / qty

            seen.add(tx)

            img = images.get(get_asset)

            caption = f"""{get_asset} buy order placed

Price: {round(price,8)} {give_asset}
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

            print("Buy order:", get_asset)

            send_photo(img, caption)


def process_fills():

    r = session.get(f"{API}/order_matches?limit=30", timeout=30).json()

    for m in r["result"]:

        asset = m["forward_asset"]

        if asset not in cards:
            continue

        tx = m["tx0_hash"]

        if tx in seen:
            continue

        qty = norm(m["forward_quantity"])

        if qty == 0:
            continue

        price = norm(m["backward_quantity"]) / qty
        token = m["backward_asset"]

        seen.add(tx)

        img = images.get(asset)

        caption = f"""{asset} order filled

Price: {round(price,8)} {token}
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

        print("Order filled:", asset)

        send_photo(img, caption)


while True:

    try:

        process_dispenses()
        process_dispenser_open()
        process_orders()
        process_fills()

        save_seen(seen)

    except Exception as e:

        print("Watcher error:", e)

    time.sleep(15)
