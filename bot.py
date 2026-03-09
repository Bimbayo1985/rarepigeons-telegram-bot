import os
import random
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

cards = requests.get(CARDS_JSON).json()["cards"]

ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


# -----------------------------
# LAST SALE
# -----------------------------

def find_last_sale(asset):

    url = f"https://tokenscan.io/api/dispenses/{asset}"

    r = requests.get(url).json()

    if not r["data"]:
        return None

    d = r["data"][0]

    return {
        "price": float(d["btc_amount"]),
        "buyer": d["address"],
        "tx": d["tx_hash"]
    }


# -----------------------------
# FLOOR
# -----------------------------

def find_floor(asset):

    url = f"https://tokenscan.io/api/dispensers/{asset}?status=open"

    r = requests.get(url).json()

    if not r["data"]:
        return None

    best = min(r["data"], key=lambda x: float(x["satoshirate"]))

    return {
        "price": float(best["satoshirate"]),
        "seller": best["source"],
        "tx": best["tx_hash"]
    }


# -----------------------------
# MARKET (HORIZON)
# -----------------------------

def find_market(asset):

    url = "https://horizon.market/api/orders"

    r = requests.get(url, headers=HEADERS).json()

    best = None

    for o in r["orders"]:

        if o["give_asset"] != asset:
            continue

        give = float(o["give_quantity"])
        get = float(o["get_quantity"])

        price = get / give

        if best is None or price < best["price"]:

            best = {
                "price": price,
                "tx": o["tx_index"]
            }

    return best


# -----------------------------
# COMMANDS
# -----------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🐦 Rare Pigeons Bot

/pigeon ASSET
/random

/ls ASSET
/floor ASSET
/market ASSET
"""

    await update.message.reply_text(text)


async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /pigeon ASSET")
        return

    asset = context.args[0].upper()

    if asset not in ASSETS:
        await update.message.reply_text("Asset not found")
        return

    await update.message.reply_photo(ASSETS[asset], caption=asset)


async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(ASSETS[asset], caption=asset)


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    data = find_last_sale(asset)

    if not data:
        await update.message.reply_text("No sales found")
        return

    text = f"""
🐦 LAST SALE

{asset}

Price
{data['price']:.8f} BTC

Buyer
{data['buyer']}

https://tokenscan.io/tx/{data['tx']}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /floor ASSET")
        return

    asset = context.args[0].upper()

    data = find_floor(asset)

    if not data:
        await update.message.reply_text("No listings")
        return

    text = f"""
🐦 {asset} FLOOR

Price
{data['price']:.8f} BTC

Seller
{data['seller']}

https://tokenscan.io/tx/{data['tx']}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /market ASSET")
        return

    asset = context.args[0].upper()

    data = find_market(asset)

    if not data:
        await update.message.reply_text("No orders")
        return

    text = f"""
🐦 {asset} MARKET

Best order

{data['price']:.4f} XCP

https://cp20.tokenscan.io/tx/{data['tx']}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


# -----------------------------

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("pigeon", pigeon))
    app.add_handler(CommandHandler("random", random_card))
    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))

    print("Rare Pigeons bot started")

    app.run_polling()


if __name__ == "__main__":
    main()
