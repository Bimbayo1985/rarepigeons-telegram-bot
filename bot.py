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


def get_last_sale(asset):

    url = f"https://tokenscan.io/api/dispenses?asset={asset}"

    data = requests.get(url).json()

    if not data:
        return None

    row = data[0]

    return {
        "price": row["btc_amount"],
        "buyer": row["destination"],
        "tx": row["tx_hash"]
    }


def get_floor(asset):

    url = f"https://tokenscan.io/api/dispensers?asset={asset}"

    data = requests.get(url).json()

    if not data:
        return None

    best = min(data, key=lambda x: x["satoshirate"])

    return {
        "price": best["satoshirate"] / 100000000,
        "seller": best["source"],
        "tx": best["tx_hash"]
    }


def get_market(asset):

    url = f"https://tokenscan.io/api/orders?asset={asset}"

    data = requests.get(url).json()

    if not data:
        return None

    best = min(data, key=lambda x: x["price"])

    return {
        "price": best["price"],
        "tx": best["tx_hash"]
    }


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_last_sale(asset)

    if not data:
        await update.message.reply_text("No sales found")
        return

    text = f"""
🐦 LAST SALE

{asset}

Price
{data['price']} BTC

Buyer
{data['buyer']}

https://tokenscan.io/tx/{data['tx']}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_floor(asset)

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

    asset = context.args[0].upper()

    data = get_market(asset)

    if not data:
        await update.message.reply_text("No orders")
        return

    text = f"""
🐦 {asset} MARKET

Best order

{data['price']} XCP

https://tokenscan.io/tx/{data['tx']}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(ASSETS[asset], caption=asset)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))
    app.add_handler(CommandHandler("random", random_card))

    app.run_polling()


if __name__ == "__main__":
    main()
