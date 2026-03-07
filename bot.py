import os
import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

DISPENSES = "https://tokenscan.io/explorer/dispenses?start=0&length=200"
DISPENSERS = "https://tokenscan.io/explorer/dispensers?start=0&length=200"
ORDERS = "https://tokenscan.io/explorer/orders?start=0&length=200"

cards = requests.get(CARDS_JSON).json()["cards"]
ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


# ---------------- MENU ----------------

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


# ---------------- PIGEON ----------------

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    if asset not in ASSETS:
        await update.message.reply_text("Unknown pigeon")
        return

    await update.message.reply_photo(photo=ASSETS[asset])


async def random_pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(photo=ASSETS[asset], caption=asset)


# ---------------- LAST SALE ----------------

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    r = requests.get(DISPENSES).json()

    for row in r["data"]:

        if row[4] == asset:

            buyer = row[3]
            price = row[6]
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

            return

    await update.message.reply_text("No sales found")


# ---------------- FLOOR ----------------

async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    r = requests.get(DISPENSERS).json()

    best_price = None
    best_tx = None
    seller = None

    for row in r["data"]:

        if row[4] == asset:

            price = float(row[6])

            if best_price is None or price < best_price:

                best_price = price
                seller = row[3]
                best_tx = row[7]

    if best_price is None:

        await update.message.reply_text("No listings")
        return

    caption = f"""🐦 {asset} FLOOR

Price
{best_price} BTC

Seller
{seller}

https://tokenscan.io/tx/{best_tx}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


# ---------------- MARKET ----------------

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    r = requests.get(ORDERS).json()

    best_price = None

    for row in r["data"]:

        give_qty = float(row[3])
        give_asset = row[4]

        get_qty = float(row[5])
        get_asset = row[6]

        status = row[7]

        if status != "open":
            continue

        if give_asset == asset:

            price = get_qty / give_qty

            if best_price is None or price < best_price:
                best_price = price

    if best_price is None:

        await update.message.reply_text("No orders")
        return

    caption = f"""🐦 {asset} MARKET

Best SELL

{best_price:.8f} XCP
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


# ---------------- MAIN ----------------

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

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
