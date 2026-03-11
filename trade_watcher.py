import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE = "https://api.unspendablelabs.com:4000/v2"

LIST_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

CHECK_INTERVAL = 15
CARDS_REFRESH = 300

cards = {}

seen_dispenses = set()
seen_dispensers = set()
seen_orders = set()
seen_matches = set()

last_cards_refresh = 0


def tg_photo(image, caption):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "photo": image,
                "caption": caption
            },
            timeout=15
        )

    except:
        pass


def api(url):

    try:

        r = requests.get(url, timeout=20)

        if r.status_code != 200:
            return None

        return r.json()

    except:
        return None


def load_cards():

    global cards

    data = api(LIST_URL)

    if not data:
        return

    cards = {}

    for c in data["cards"]:
        cards[c["asset"].upper()] = c["image"]


def refresh_cards():

    global last_cards_refresh

    if time.time() - last_cards_refresh > CARDS_REFRESH:

        load_cards()

        last_cards_refresh = time.time()


def check_dispenses():

    for asset, image in cards.items():

        url = f"{BASE}/dispenses?asset={asset}"

        data = api(url)

        if not data:
            continue

        for tx in data.get("result", []):

            tx_hash = tx["tx_hash"]

            if tx_hash in seen_dispenses:
                continue

            seen_dispenses.add(tx_hash)

            btc = float(tx["btc_amount"]) / 100000000
            qty = float(tx["dispense_quantity"]) / 100000000

            price = btc / qty if qty else 0

            caption = (
                f"{asset} sold via dispenser\n\n"
                f"Price: {price:.8f} BTC\n"
                f"Quantity: {qty:.0f}\n\n"
                f"https://tokenscan.io/tx/{tx_hash}"
            )

            tg_photo(image, caption)


def check_dispensers():

    for asset, image in cards.items():

        url = f"{BASE}/dispensers?asset={asset}&status=open"

        data = api(url)

        if not data:
            continue

        for d in data.get("result", []):

            tx = d["tx_hash"]

            if tx in seen_dispensers:
                continue

            seen_dispensers.add(tx)

            price = float(d["satoshi_price"]) / 100000000
            qty = float(d["give_remaining"]) / 100000000

            caption = (
                f"{asset} dispenser opened\n\n"
                f"Price: {price:.8f} BTC\n"
                f"Quantity: {qty:.0f}\n\n"
                f"https://tokenscan.io/tx/{tx}"
            )

            tg_photo(image, caption)


def check_orders():

    for asset, image in cards.items():

        url = f"{BASE}/orders?give_asset={asset}"

        data = api(url)

        if not data:
            continue

        for o in data.get("result", []):

            tx_hash = o["tx_hash"]

            if tx_hash in seen_orders:
                continue

            seen_orders.add(tx_hash)

            give_qty = float(o["give_quantity"]) / 100000000
            get_qty = float(o["get_quantity"]) / 100000000

            get_asset = o["get_asset"]

            price = get_qty / give_qty if give_qty else 0

            caption = (
                f"{asset} sell order placed\n\n"
                f"Price: {price:.4f} {get_asset}\n"
                f"Quantity: {give_qty:.0f}\n\n"
                f"https://tokenscan.io/tx/{tx_hash}"
            )

            tg_photo(image, caption)


def check_matches():

    url = f"{BASE}/order_matches"

    data = api(url)

    if not data:
        return

    for m in data.get("result", []):

        match_id = str(m["id"])

        if match_id in seen_matches:
            continue

        forward_asset = m["forward_asset"]
        backward_asset = m["backward_asset"]

        asset = None

        if forward_asset in cards:
            asset = forward_asset

        if backward_asset in cards:
            asset = backward_asset

        if not asset:
            continue

        seen_matches.add(match_id)

        image = cards[asset]

        qty = float(m["forward_quantity"]) / 100000000
        price = (float(m["backward_quantity"]) / 100000000) / qty if qty else 0

        tx = m["tx0_hash"]

        caption = (
            f"{asset} order filled\n\n"
            f"Price: {price:.4f} {backward_asset}\n"
            f"Quantity: {qty:.0f}\n\n"
            f"https://tokenscan.io/tx/{tx}"
        )

        tg_photo(image, caption)


def initialize():

    load_cards()

    for asset in cards:

        d = api(f"{BASE}/dispenses?asset={asset}")

        if d:
            for tx in d.get("result", []):
                seen_dispenses.add(tx["tx_hash"])

        d = api(f"{BASE}/dispensers?asset={asset}&status=open")

        if d:
            for tx in d.get("result", []):
                seen_dispensers.add(tx["tx_hash"])

        d = api(f"{BASE}/orders?give_asset={asset}")

        if d:
            for tx in d.get("result", []):
                seen_orders.add(tx["tx_hash"])

    m = api(f"{BASE}/order_matches")

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
