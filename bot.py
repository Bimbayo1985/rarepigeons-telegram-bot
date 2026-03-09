import os
import random
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


BOT_TOKEN = os.getenv("BOT_TOKEN")

LIST_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# LOAD CARDS
# -----------------------------

cards_data = requests.get(LIST_JSON).json()["cards"]

CARDS = {c["asset"]: c["image"] for c in cards_data}
ASSETS = list(CARDS.keys())


# -----------------------------
# MENU
# -----------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
Rare Pigeons Bot

/pigeon ASSET
/random
/ls ASSET
/floor ASSET
/market ASSET
"""

    await update.message.reply_text(text)


# -----------------------------
# RANDOM CARD
# -----------------------------

async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSETS)
    img = CARDS[asset]

    await update.message.reply_photo(
        photo=img,
        caption=f"{asset}"
    )


# -----------------------------
# PIGEON CARD
# -----------------------------

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /pigeon ASSET")
        return

    asset = context.args[0].upper()

    if asset not in CARDS:
        await update.message.reply_text("Asset not found")
        return

    await update.message.reply_photo(
        photo=CARDS[asset],
        caption=asset
    )


# -----------------------------
# LAST SALE
# -----------------------------

def get_last_sale(asset):

    url = f"https://tokenscan.io/api/dispenses/{asset}"

    r = requests.get(url, headers=HEADERS).json()

    if not r["data"]:
        return None

    d = r["data"][0]

    price = float(d["btc_amount"])

    tx = d["tx_hash"]

    return price, tx


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    sale = get_last_sale(asset)

    if not sale:
        await update.message.reply_text("No sales found")
        return

    price, tx = sale

    text = f"""
{asset} last sale

Price: {price} BTC

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_text(text)


# -----------------------------
# FLOOR DISPENSER
# -----------------------------

def get_floor(asset):

    url = f"https://tokenscan.io/api/dispensers/{asset}?status=open"

    r = requests.get(url, headers=HEADERS).json()

    if not r["data"]:
        return None

    d = r["data"][0]

    price = float(d["satoshi_price"])

    tx = d["tx_hash"]

    return price, tx


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /floor ASSET")
        return

    asset = context.args[0].upper()

    listing = get_floor(asset)

    if not listing:
        await update.message.reply_text("No listings")
        return

    price, tx = listing

    text = f"""
{asset} floor

Price: {price} BTC

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_text(text)


# -----------------------------
# MARKET ORDER
# -----------------------------

def get_market(asset):

    url = f"https://api.unspendablelabs.com:4000/v2/orders?give_asset={asset}&status=open"

    r = requests.get(url, headers=HEADERS).json()

    if not r["result"]:
        return None

    order = r["result"][0]

    give_qty = order["give_quantity"]
    get_qty = order["get_quantity"]

    price = (get_qty / 1e8) / give_qty

    tx_index = order["tx_index"]

    remaining = order["give_remaining"]

    return price, remaining, tx_index


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /market ASSET")
        return

    asset = context.args[0].upper()

    data = get_market(asset)

    if not data:
        await update.message.reply_text("No orders")
        return

    price, remaining, tx = data

    text = f"""
{asset} market

Price: {price} XCP
Available: {remaining}

https://cp20.tokenscan.io/tx/{tx}
"""

    await update.message.reply_text(text)


# -----------------------------
# START BOT
# -----------------------------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("random", random_card))
app.add_handler(CommandHandler("pigeon", pigeon))
app.add_handler(CommandHandler("ls", ls))
app.add_handler(CommandHandler("floor", floor))
app.add_handler(CommandHandler("market", market))

print("Bot running")

app.run_polling()
