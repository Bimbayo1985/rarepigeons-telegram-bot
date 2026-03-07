import requests
import time
import os
from telegram import Bot

TOKEN = os.environ["BOT_TOKEN"]

CHAT_ID = -1003513082996

JSON_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

TRADES_API = "https://api.horizon.market/trades?limit=50"

bot = Bot(token=TOKEN)

data = requests.get(JSON_URL).json()
assets = [c["asset"] for c in data["cards"]]

seen = set()

def post_trade(trade):

    asset = trade["asset"]
    price = trade["price"]
    qty = trade["quantity"]
    tx = trade["tx_hash"]

    text = f"""
🐦 {asset} purchased

Amount: {qty}

Price: {price} BTC

TX:
https://mempool.space/tx/{tx}

Project: Rare Pigeons
"""

    bot.send_message(chat_id=CHAT_ID, text=text)


while True:

    try:

        r = requests.get(TRADES_API).json()

        for trade in r:

            tx = trade["tx_hash"]

            if tx in seen:
                continue

            asset = trade["asset"]

            if asset in assets:

                post_trade(trade)
                seen.add(tx)

        time.sleep(20)

    except Exception as e:

        print("Watcher error:", e)
        time.sleep(20)
