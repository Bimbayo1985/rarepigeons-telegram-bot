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

    data = requests.get(JSON_URL).json()

    return {c["asset"]: c["image"] for c in data["cards"]}


assets = load_assets()

print("Rare Pigeons watcher started")


def get_latest_ids():

    d1 = requests.get(DISPENSES_URL).json()["data"][0][0]
    d2 = requests.get(DISPENSERS_URL).json()["data"][0][0]
    d3 = requests.get(ORDERS_URL).json()["data"][0][0]

    return d1, d2, d3


last_dispense, last_dispenser, last_order = get_latest_ids()


while True:

    try:

        # ----------------------------------
        # 1️⃣ DISPENSER SALES
        # ----------------------------------

        r = requests.get(DISPENSES_URL).json()

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


        # ----------------------------------
        # 2️⃣ DISPENSER CREATED
        # ----------------------------------

        r = requests.get(DISPENSERS_URL).json()

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


        # ----------------------------------
        # 3️⃣ DEX EVENTS
        # ----------------------------------

        r = requests.get(ORDERS_URL).json()

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


            # SELL ORDER
            if give_asset in assets:

                asset = give_asset
                price = get_qty / give_qty

                if status == "open":
                    event = "🔵 SELL ORDER"

                if status == "filled":
                    event = "🔥 DEX SALE"


            # BUY ORDER
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
{price} XCP
"""

                send_photo(assets[asset], caption)

            last_order = event_id


    except Exception as e:

        print("Error:", e)

    time.sleep(20)
