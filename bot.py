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


def scan_dispenses(asset):

    for page in range(20):

        start = page * 100

        url = f"https://tokenscan.io/explorer/dispenses?start={start}&length=100"

        rows = requests.get(url).json()["data"]

        for row in rows:

            if row[5] == asset:

                return {
                    "buyer": row[3],
                    "price": float(row[6]),
                    "tx": row[7]
                }

    return None


def scan_dispensers(asset):

    best = None

    for page in range(20):

        start = page * 100

        url = f"https://tokenscan.io/explorer/dispensers?start={start}&length=100"

        rows = requests.get(url).json()["data"]

        for row in rows:

            if row[5] != asset:
                continue

            price = float(row[6])

            if best is None or price < best["price"]:

                best = {
                    "price": price,
                    "seller": row[3],
                    "tx": row[8]
                }

    return best


def scan_orders(asset):

    best = None

    for page in range(20):

        start = page * 100

        url = f"https://tokenscan.io/explorer/orders?start={start}&length=100"

        rows = requests.get(url).json()["data"]

        for row in rows:

            give_asset = row[4]
            get_asset = row[6]

            if give_asset != asset and get_asset != asset:
                continue

            give_qty = float(row[3])
            get_qty = float(row[5])

            price = (get_qty / give_qty) * 1000

            if best is None or price < best["price"]:

                best = {
                    "price": price,
                    "tx": row[9]
                }

    return best


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


async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    if asset not in ASSETS:

        await update.message.reply_text("Unknown pigeon")
        return

    await update.message.reply_photo(ASSETS[asset])


async def random_pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(ASSETS[asset], caption=asset)


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = scan_dispenses(asset)

    if not data:

        await update.message.reply_text("No sales found")
        return

    caption = f"""🐦 LAST SALE

{asset}

Price
{data["price"]:.8f} BTC

Buyer
{data["buyer"]}

https://tokenscan.io/tx/{data["tx"]}
"""

    await update.message.reply_photo(ASSETS[asset], caption=caption)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = scan_dispensers(asset)

    if not data:

        await update.message.reply_text("No listings")
        return

    caption = f"""🐦 {asset} FLOOR

Price
{data["price"]:.8f} BTC

Seller
{data["seller"]}

https://tokenscan.io/tx/{data["tx"]}
"""

    await update.message.reply_photo(ASSETS[asset], caption=caption)


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = scan_orders(asset)

    if not data:

        await update.message.reply_text("No orders")
        return

    caption = f"""🐦 {asset} MARKET

Best order

{data["price"]:.2f} XCP

https://tokenscan.io/tx/{data["tx"]}
"""

    await update.message.reply_photo(ASSETS[asset], caption=caption)


def main():

    print("Rare Pigeons bot running")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("pigeon", pigeon))
    app.add_handler(CommandHandler("random", random_pigeon))

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))

    app.run_polling()


if __name__ == "__main__":
    main()
