import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LIST_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rarepigeons/main/list.json"

DISPENSERS_API = "https://tokenscan.io/api/dispensers/"
DISPENSES_API = "https://tokenscan.io/api/dispenses/"
ORDERS_API = "https://api.unspendablelabs.com:4000/v2/orders?status=open"
MATCHES_API = "https://api.unspendablelabs.com:4000/v2/order_matches"

CHECK_INTERVAL = 15
CARDS_REFRESH = 300  # 5 хвилин

cards = {}

seen_dispenses = set()
seen_dispensers = set()
seen_orders = set()
seen_matches = set()

last_cards_refresh = 0


def send_photo(image, caption):

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "photo": image,
                "caption": caption
            },
            timeout=10
        )
    except:
        pass


def safe_json(url):

    try:
        r = requests.get(url, timeout=15)

        if r.status_code != 200:
            return None

        return r.json()

    except:
        return None


def load_cards():

    global cards

    data = safe_json(LIST_JSON)

    if not data:
        return

    for c in data["cards"]:
        cards[c["asset"].upper()] = c["image"]


def refresh_cards():

    global last_cards_refresh

    if time.time() - last_cards_refresh > CARDS_REFRESH:
        load_cards()
        last_cards_refresh = time.time()


def check_dispenses():

    for asset, image in cards.items():

        data = safe_json(DISPENSES_API + asset)

        if not data:
            continue

        for tx in data.get("data", []):

            tx_hash = tx["tx_hash"]

            if tx_hash in seen_dispenses:
                continue

            seen_dispenses.add(tx_hash)

            try:
                btc_amount = float(tx["btc_amount"])
                price = float(tx["satoshi_price"])
                qty = int(round(btc_amount / price))
            except:
                price = float(tx.get("satoshi_price", 0))
                qty = int(tx.get("quantity", 1))

            caption = (
                f"{asset} sold via dispenser\n\n"
                f"Price: {price:.8f} BTC\n"
                f"Quantity: {qty}\n\n"
                f"https://tokenscan.io/tx/{tx_hash}"
            )

            send_photo(image, caption)


def check_dispensers():

    for asset, image in cards.items():

        data = safe_json(DISPENSERS_API + asset + "?status=open")

        if not data:
            continue

        for d in data.get("data", []):

            tx = d["tx_hash"]

            if tx in seen_dispensers:
                continue

            seen_dispensers.add(tx)

            price = float(d["satoshi_price"])
            qty = int(d["give_remaining"])

            caption = (
                f"{asset} dispenser opened\n\n"
                f"Price: {price:.8f} BTC\n"
                f"Quantity: {qty}\n\n"
                f"https://tokenscan.io/tx/{tx}"
            )

            send_photo(image, caption)


def check_orders():

    data = safe_json(ORDERS_API)

    if not data:
        return

    for o in data.get("result", []):

        tx = str(o["tx_index"])

        if tx in seen_orders:
            continue

        seen_orders.add(tx)

        give_asset = o["give_asset"]
        get_asset = o["get_asset"]

        if give_asset in cards:
            asset = give_asset
            image = cards[asset]
        elif get_asset in cards:
            asset = get_asset
            image = cards[asset]
        else:
            continue

        give_qty = float(o["give_quantity"])
        get_qty = float(o["get_quantity"])

        price = get_qty / give_qty

        if give_asset in cards:

            caption = (
                f"{asset} sell order placed\n\n"
                f"Price: {price:.4f} {get_asset}\n"
                f"Quantity: {give_qty}\n\n"
                f"https://cp20.tokenscan.io/tx/{tx}"
            )

        else:

            caption = (
                f"{asset} buy order placed\n\n"
                f"Price: {price:.4f} {give_asset}\n"
                f"Quantity: {get_qty}\n\n"
                f"https://cp20.tokenscan.io/tx/{tx}"
            )

        send_photo(image, caption)


def check_matches():

    data = safe_json(MATCHES_API)

    if not data:
        return

    for m in data.get("result", []):

        match_id = str(m["id"])

        if match_id in seen_matches:
            continue

        seen_matches.add(match_id)

        forward_asset = m["forward_asset"]
        backward_asset = m["backward_asset"]

        if forward_asset in cards:
            asset = forward_asset
            image = cards[asset]
        elif backward_asset in cards:
            asset = backward_asset
            image = cards[asset]
        else:
            continue

        qty = float(m["forward_quantity"])
        price = float(m["backward_quantity"]) / qty

        tx = m["tx0_hash"]

        caption = (
            f"{asset} order filled\n\n"
            f"Price: {price:.4f} {backward_asset}\n"
            f"Quantity: {qty}\n\n"
            f"https://tokenscan.io/tx/{tx}"
        )

        send_photo(image, caption)


def initialize():

    load_cards()

    for asset in cards:

        d = safe_json(DISPENSES_API + asset)

        if d:
            for tx in d.get("data", []):
                seen_dispenses.add(tx["tx_hash"])

        d = safe_json(DISPENSERS_API + asset + "?status=open")

        if d:
            for tx in d.get("data", []):
                seen_dispensers.add(tx["tx_hash"])

    o = safe_json(ORDERS_API)

    if o:
        for tx in o.get("result", []):
            seen_orders.add(str(tx["tx_index"]))

    m = safe_json(MATCHES_API)

    if m:
        for tx in m.get("result", []):
            seen_matches.add(str(tx["id"]))


def main():

    initialize()

    while True:

        refresh_cards()

        check_dispenses()
        check_dispensers()
        check_orders()
        check_matches()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
