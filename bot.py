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


def get_asset(asset):
    url = f"https://cp20.tokenscan.io/{asset}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


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

    await update.message.reply_photo(
        photo=ASSETS[asset],
        caption=asset
    )


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_asset(asset)

    if not data:
        await update.message.reply_text("Asset not found")
        return

    floor = data["market_info"]["btc"]["floor"]

    caption = f"""🐦 {asset} FLOOR

{floor} BTC

https://tokenscan.io/asset/{asset}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_asset(asset)

    if not data:
        await update.message.reply_text("Asset not found")
        return

    price = data["estimated_value"]["btc"]

    caption = f"""🐦 LAST SALE

{asset}

≈ {price} BTC
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_asset(asset)

    if not data:
        await update.message.reply_text("Asset not found")
        return

    price = data["market_info"]["btc"]["price"]

    caption = f"""🐦 {asset} MARKET

{price} BTC
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
