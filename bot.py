import os
import random
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

cards = requests.get(CARDS_JSON).json()["cards"]

ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


# -------------------------
# LAST SALE
# -------------------------

def find_last_sale(asset):

    start = 0

    while start < 500:

        url = f"https://tokenscan.io/explorer/dispenses?start={start}&length=50"

        rows = requests.get(url).json()["data"]

        if not rows:
            return None

        for r in rows:

            if r[4] == asset:

                return {
                    "price": float(r[6]),
                    "buyer": r[3],
                    "tx": r[7]
                }

        start += 50

    return None


# -------------------------
# FLOOR
# -------------------------

def find_floor(asset):

    start = 0
    best = None

    while start < 500:

        url = f"https://tokenscan.io/explorer/dispensers?start={start}&length=50"

        rows = requests.get(url).json()["data"]

        if not rows:
            break

        for r in rows:

            if r[4] == asset:

                price = float(r[6])

                if best is None or price < best["price"]:

                    best = {
                        "price": price,
                        "seller": r[3],
                        "tx": r[8]
                    }

        start += 50

    return best


# -------------------------
# MARKET
# -------------------------

def find_market(asset):

    start = 0
    best = None

    while start < 500:

        url = f"https://tokenscan.io/explorer/orders?start={start}&length=50"

        rows = requests.get(url).json()["data"]

        if not rows:
            break

        for r in rows:

            give_qty = float(r[3])
            give_asset = r[4]

            get_qty = float(r[5])
            get_asset = r[6]

            if give_asset == asset and get_asset == "XCP":

                price = get_qty / give_qty

                if best is None or price < best["price"]:

                    best = {
                        "price": price,
                        "tx": r[9]
                    }

        start += 50

    return best


# -------------------------
# COMMANDS
# -------------------------

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

{data['price']:.2f} XCP

https://tokenscan.io/tx/{data['tx']}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


# -------------------------
# BOT START
# -------------------------

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
