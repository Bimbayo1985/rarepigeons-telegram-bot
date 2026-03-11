import requests
import time
import json
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

API = "https://api.unspendablelabs.com/v2"

SAT = 100000000

seen = set()


def send_photo(url, caption):

    tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(
        tg,
        data={
            "chat_id": CHAT_ID,
            "photo": url,
            "caption": caption
        }
    )


def get_cards():

    with open("list.json") as f:
        return set(json.load(f))


def get_image(asset):

    try:
        r = requests.get(f"https://tokenscan.io/api/asset/{asset}")
        j = r.json()

        return j.get("image")

    except:
        return None


def norm(q):

    return round(q / SAT, 8)


cards = get_cards()


while True:

    try:

        # DISPENSER SALES
        r = requests.get(f"{API}/dispenses?limit=30").json()

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

            img = get_image(asset)

            caption = f"""{asset} sold via dispenser

Price: {btc} BTC
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

            send_photo(img, caption)

        # DISPENSER OPEN
        r = requests.get(f"{API}/dispensers?status=0&limit=30").json()

        for d in r["result"]:

            asset = d["asset"]

            if asset not in cards:
                continue

            tx = d["tx_hash"]

            if tx in seen:
                continue

            seen.add(tx)

            price_btc = norm(d["satoshirate"])

            img = get_image(asset)

            caption = f"""{asset} dispenser opened

Price: {price_btc} BTC

https://tokenscan.io/tx/{tx}
"""

            send_photo(img, caption)

        # ORDERS
        r = requests.get(f"{API}/orders?limit=30").json()

        for o in r["result"]:

            give_asset = o["give_asset"]
            get_asset = o["get_asset"]

            tx = o["tx_hash"]

            if tx in seen:
                continue

            if give_asset in cards:

                seen.add(tx)

                qty = norm(o["give_remaining"])
                price = norm(o["get_remaining"]) / qty

                img = get_image(give_asset)

                caption = f"""{give_asset} sell order placed

Price: {round(price,8)} {get_asset}
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

                send_photo(img, caption)

            elif get_asset in cards:

                seen.add(tx)

                qty = norm(o["get_remaining"])
                price = norm(o["give_remaining"]) / qty

                img = get_image(get_asset)

                caption = f"""{get_asset} buy order placed

Price: {round(price,8)} {give_asset}
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

                send_photo(img, caption)

        # ORDER FILLS
        r = requests.get(f"{API}/order_matches?limit=30").json()

        for m in r["result"]:

            asset = m["forward_asset"]

            if asset not in cards:
                continue

            tx = m["tx0_hash"]

            if tx in seen:
                continue

            seen.add(tx)

            qty = norm(m["forward_quantity"])

            price = norm(m["backward_quantity"]) / qty

            token = m["backward_asset"]

            img = get_image(asset)

            caption = f"""{asset} order filled

Price: {round(price,8)} {token}
Quantity: {qty}

https://tokenscan.io/tx/{tx}
"""

            send_photo(img, caption)

    except Exception as e:

        print("Watcher error:", e)

    time.sleep(15)
