import os
import random
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

cards = requests.get(CARDS_JSON).json()["cards"]

ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


def last_sale(asset):

    url = f"https://tokenscan.io/explorer/dispenses?asset={asset}&start=0&length=1"

    rows = requests.get(url).json()["data"]

    if not rows:
        return None

    r = rows[0]

    return {
        "buyer": r[3],
        "price": float(r[6]),
        "tx": r[7]
    }


def floor(asset):

    url = f"https://tokenscan.io/explorer/dispensers?asset={asset}&start=0&length=50"

    rows = requests.get(url).json()["data"]

    if not rows:
        return None

    best = None

    for r in rows:

        price = float(r[6])

        if best is None or price < best["price"]:

            best = {
                "price": price,
                "seller": r[3],
                "tx": r[8]
            }

    return best


def market(asset):

    url = f"https://tokenscan.io/explorer/orders?asset={asset}&start=0&length=50"

    rows = requests.get(url).json()["data"]

    if not rows:
        return None

    best = None

    for r in rows:

        give_qty = float(r[3])
        get_qty = float(r[5])

        price = get_qty / give_qty

        if best is None or price < best["price"]:

            best = {
                "price": price,
                "tx": r[9]
            }

    return best


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = last_sale(asset)

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


async def floor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = floor(asset)

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


async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = market(asset)

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


async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(ASSETS[asset], caption=asset)


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("random", random_card))

    app.run_polling()


if __name__ == "__main__":
    main()
