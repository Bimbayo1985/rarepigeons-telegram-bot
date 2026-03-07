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


def dispenses(asset):
    url = f"https://tokenscan.io/explorer/dispenses?asset={asset}&start=0&length=50"
    return requests.get(url).json()["data"]


def dispensers(asset):
    url = f"https://tokenscan.io/explorer/dispensers?asset={asset}&start=0&length=200"
    return requests.get(url).json()["data"]


def orders(asset):
    url = f"https://tokenscan.io/explorer/orders?asset={asset}&start=0&length=200"
    return requests.get(url).json()["data"]


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🐦 Rare Pigeons Bot\n\n"
        "/pigeon ASSET\n"
        "/random\n\n"
        "/ls ASSET\n"
        "/floor ASSET\n"
        "/market ASSET"
    )

    await update.message.reply_text(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu(update, context)


async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    if asset not in ASSETS:
        await update.message.reply_text("Unknown pigeon")
        return

    await update.message.reply_photo(photo=ASSETS[asset])


async def random_pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(photo=ASSETS[asset], caption=asset)


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    rows = dispenses(asset)

    if not rows:
        await update.message.reply_text("No sales found")
        return

    row = rows[0]

    buyer = row[3]
    price = float(row[6])
    tx = row[7]

    caption = f"""🐦 LAST SALE

{asset}

Price
{price:.8f} BTC

Buyer
{buyer}

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    rows = dispensers(asset)

    if not rows:
        await update.message.reply_text("No listings")
        return

    best_price = None
    seller = None
    tx = None

    for row in rows:

        price = float(row[6])

        if best_price is None or price < best_price:

            best_price = price
            seller = row[3]
            tx = row[8]

    caption = f"""🐦 {asset} FLOOR

Price
{best_price:.8f} BTC

Seller
{seller}

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    rows = orders(asset)

    if not rows:
        await update.message.reply_text("No orders")
        return

    best_price = None
    tx = None

    for row in rows:

        give_qty = float(row[3])
        get_qty = float(row[5])

        price = (get_qty / give_qty) * 1000

        if best_price is None or price < best_price:

            best_price = price
            tx = row[8]

    caption = f"""🐦 {asset} MARKET

Best order

{best_price:.2f} XCP

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


def main():

    print("Rare Pigeons bot running")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))

    app.add_handler(CommandHandler("pigeon", pigeon))
    app.add_handler(CommandHandler("random", random_pigeon))

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))

    app.run_polling()


if __name__ == "__main__":
    main()
