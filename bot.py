import requests
import time
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = "-1003513082996"

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

last_dispense = 0
last_dispenser = 0
last_order = 0

print("Rare Pigeons watcher started")


while True:

    try:

        r = requests.get(DISPENSES_URL).json()

        for row in r["data"]:

            event_id = row[0]

            if event_id <= last_dispense:
                break

            asset = row[4]

            if asset in assets:

                price = row[6]
                tx = row[7]

                caption = f"""
🐦 SOLD

{asset}

{price} BTC

https://tokenscan.io/tx/{tx}
"""

                send_photo(assets[asset], caption)

            last_dispense = event_id

        r = requests.get(DISPENSERS_URL).json()

        for row in r["data"]:

            event_id = row[0]

            if event_id <= last_dispenser:
                break

            asset = row[4]

            if asset in assets:

                price = row[6]

                caption = f"""
🟡 LISTED

{asset}

{price} BTC
"""

                send_photo(assets[asset], caption)

            last_dispenser = event_id

        r = requests.get(ORDERS_URL).json()

        for row in r["data"]:

            event_id = row[0]

            if event_id <= last_order:
                break

            give_asset = row[4]
            get_asset = row[6]
            status = row[7]

            asset = None

            if give_asset in assets:
                asset = give_asset
                event = "SELL ORDER"

            elif get_asset in assets:
                asset = get_asset
                event = "BUY ORDER"

            if asset:

                caption = f"""
🔵 {event}

{asset}
"""

                send_photo(assets[asset], caption)

            last_order = event_id

    except Exception as e:

        print("Error:", e)

    time.sleep(20)
