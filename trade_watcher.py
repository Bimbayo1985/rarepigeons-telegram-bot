import requests
import time
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

JSON_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

DISPENSES_URL = "https://tokenscan.io/explorer/dispenses?start=0&length=20"
DISPENSERS_URL = "https://tokenscan.io/explorer/dispensers?start=0&length=20"
ORDERS_URL = "https://tokenscan.io/explorer/orders?start=0&length=20"


def send_photo(image, caption):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "photo": image,
        "caption": caption
    })


def load_assets():

    r = requests.get(JSON_URL)

    data = r.json()

    return {c["asset"]: c["image"] for c in data["cards"]}


def safe_json(url):

    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return None


assets = load_assets()

print("Rare Pigeons watcher started")

last_dispense = 0
last_dispenser = 0
last_order = 0


def init_ids():

    global last_dispense
    global last_dispenser
    global last_order

    d = safe_json(DISPENSES_URL)
    if d and d["data"]:
        last_dispense = d["data"][0][0]

    d = safe_json(DISPENSERS_URL)
    if d and d["data"]:
        last_dispenser = d["data"][0][0]

    d = safe_json(ORDERS_URL)
    if d and d["data"]:
        last_order = d["data"][0][0]


init_ids()

print("Watcher initialized")


while True:

    try:

        # ------------------
        # DISPENSE SALES
        # ------------------

        r = safe_json(DISPENSES_URL)

        if r:

            for row in r["data"]:

                event_id = row[0]

                if event_id <= last_dispense:
                    break

                asset = row[4]

                if asset in assets:

                    buyer = row[3]
                    price = row[6]
                    tx = row[7]

                    caption = f"""
🐦 SOLD

{asset}

Price
{price} BTC

Buyer
{buyer}

https://tokenscan.io/tx/{tx}
"""

                    send_photo(assets[asset], caption)

                last_dispense = event_id


        # ------------------
        # DISPENSER CREATED
        # ------------------

        r = safe_json(DISPENSERS_URL)

        if r:

            for row in r["data"]:

                event_id = row[0]

                if event_id <= last_dispenser:
                    break

                asset = row[4]

                if asset in assets:

                    seller = row[3]
                    price = row[6]

                    caption = f"""
🟡 DISPENSER CREATED

{asset}

Price
{price} BTC

Seller
{seller}
"""

                    send_photo(assets[asset], caption)

                last_dispenser = event_id


        # ------------------
        # DEX EVENTS
        # ------------------

        r = safe_json(ORDERS_URL)

        if r:

            for row in r["data"]:

                event_id = row[0]

                if event_id <= last_order:
                    break

                give_qty = float(row[3])
                give_asset = row[4]

                get_qty = float(row[5])
                get_asset = row[6]

                status = row[7]

                asset = None
                event = None
                price = None

                if give_asset in assets:

                    asset = give_asset
                    price = get_qty / give_qty

                    if status == "open":
                        event = "🔵 SELL ORDER"

                    if status == "filled":
                        event = "🔥 DEX SALE"

                elif get_asset in assets:

                    asset = get_asset
                    price = give_qty / get_qty

                    if status == "open":
                        event = "🟢 BUY ORDER"

                    if status == "filled":
                        event = "🔥 DEX SALE"

                if asset and event:

                    caption = f"""
{event}

{asset}

Price
{price:.4f} XCP
"""

                    send_photo(assets[asset], caption)

                last_order = event_id

    except Exception as e:

        print("Watcher error:", e)

    time.sleep(20)
