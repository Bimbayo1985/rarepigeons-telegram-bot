import os
import random
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

ASSET_URL = "https://cp20.tokenscan.io/asset/"
CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"


# -------- LOAD CARDS --------

cards_data = requests.get(CARDS_JSON, timeout=20).json()["cards"]

ASSETS = {c["asset"]: c["image"] for c in cards_data}
ASSET_LIST = list(ASSETS.keys())


# -------- HELPERS --------

def get_page(asset):

    r = requests.get(ASSET_URL + asset, timeout=20)

    if r.status_code != 200:
        return None

    return BeautifulSoup(r.text, "lxml")


def find_price(soup, keyword):

    rows = soup.find_all("tr")

    for r in rows:

        txt = r.get_text(" ", strip=True)

        if keyword in txt:

            parts = txt.split()

            for p in parts:
                if "0.000" in p:
                    return p

    return None


# -------- COMMANDS --------

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

    if not context.args:
        return

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


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    asset = context.args[0].upper()

    soup = get_page(asset)

    if not soup:
        await update.message.reply_text("Asset not found")
        return

    price = find_price(soup, "BTC Paid")

    if not price:
        await update.message.reply_text("No sales found")
        return

    caption = f"""🐦 LAST SALE

{asset}

{price} BTC

https://cp20.tokenscan.io/asset/{asset}
"""

    if asset in ASSETS:
        await update.message.reply_photo(photo=ASSETS[asset], caption=caption)
    else:
        await update.message.reply_text(caption)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    asset = context.args[0].upper()

    soup = get_page(asset)

    if not soup:
        await update.message.reply_text("Asset not found")
        return

    price = find_price(soup, "BTC Floor")

    if not price:
        await update.message.reply_text("No listings")
        return

    caption = f"""🐦 {asset} FLOOR

{price} BTC

https://cp20.tokenscan.io/asset/{asset}
"""

    if asset in ASSETS:
        await update.message.reply_photo(photo=ASSETS[asset], caption=caption)
    else:
        await update.message.reply_text(caption)


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    asset = context.args[0].upper()

    soup = get_page(asset)

    if not soup:
        await update.message.reply_text("Asset not found")
        return

    price = find_price(soup, "Selling")

    if not price:
        await update.message.reply_text("No orders")
        return

    caption = f"""🐦 {asset} MARKET

Best SELL

{price} BTC

https://cp20.tokenscan.io/asset/{asset}
"""

    if asset in ASSETS:
        await update.message.reply_photo(photo=ASSETS[asset], caption=caption)
    else:
        await update.message.reply_text(caption)


# -------- MAIN --------

def main():

    print("Rare Pigeons bot starting")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))

    app.add_handler(CommandHandler("pigeon", pigeon))
    app.add_handler(CommandHandler("random", random_pigeon))

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))

    print("Rare Pigeons bot running")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
