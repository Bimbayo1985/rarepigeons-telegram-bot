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


def get_dispenses(asset):

    url = f"https://tokenscan.io/explorer/dispenses?asset={asset}&start=0&length=10"

    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.json()["data"]


def get_dispensers(asset):

    url = f"https://tokenscan.io/explorer/dispensers?asset={asset}&start=0&length=100"

    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.json()["data"]


def get_orders(asset):

    url = f"https://tokenscan.io/explorer/orders?asset={asset}&start=0&length=100"

    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.json()["data"]


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

    rows = get_dispenses(asset)

    if not rows:
        await update.message.reply_text("No sales found")
        return

    row = rows[0]

    price = row[6]
    buyer = row[3]
    tx = row[7]

    caption = f"""🐦 LAST SALE

{asset}

Price
{price} BTC

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

    rows = get_dispensers(asset)

    if not rows:
        await update.message.reply_text("No listings")
        return

    best = None
    seller = None
    tx = None

    for row in rows:

        try:
            price = float(row[6])
        except:
            continue

        if best is None or price < best:

            best = price
            seller = row[3]
            tx = row[7]

    caption = f"""🐦 {asset} FLOOR

Price
{best} BTC

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

    rows = get_orders(asset)

    if not rows:
        await update.message.reply_text("No orders")
        return

    best = None

    for row in rows:

        try:
            give = float(row[3])
            get = float(row[5])
        except:
            continue

        price = get / give

        if best is None or price < best:
            best = price

    caption = f"""🐦 {asset} MARKET

Best order

{best:.8f} XCP
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
