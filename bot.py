import requests
import random
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]

JSON_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

DISPENSES_BASE = "https://tokenscan.io/explorer/dispenses"
DISPENSERS_BASE = "https://tokenscan.io/explorer/dispensers"
ORDERS_BASE = "https://tokenscan.io/explorer/orders"

MAX_SCAN = 10000
STEP = 100


def load_cards():

    data = requests.get(JSON_URL).json()

    return data["cards"]


def get_assets():

    cards = load_cards()

    return {c["asset"]: c["image"] for c in cards}


def short(addr):

    return addr[:6] + "..." + addr[-4:]


# ------------------------------------------------
# PIGEON
# ------------------------------------------------

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = load_cards()

    if len(context.args) == 0:

        card = random.choice(cards)

    else:

        name = context.args[0].upper()

        card = None

        for c in cards:

            if c["asset"] == name:

                card = c

        if card is None:

            await update.message.reply_text("Pigeon not found 🐦")

            return

    caption = f"""
🐦 {card['asset']}

Rare Pigeons

https://www.rarepigeons.com
"""

    await update.message.reply_photo(photo=card["image"], caption=caption)


# ------------------------------------------------
# RANDOM
# ------------------------------------------------

async def randompigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = load_cards()

    card = random.choice(cards)

    await update.message.reply_photo(photo=card["image"], caption=card["asset"])


# ------------------------------------------------
# LAST SALE
# ------------------------------------------------

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text("Usage: /ls ASSET")

        return

    asset = context.args[0].upper()

    for start in range(0, MAX_SCAN, STEP):

        url = f"{DISPENSES_BASE}?start={start}&length={STEP}"

        r = requests.get(url).json()

        for row in r["data"]:

            if row[4] == asset:

                buyer = row[3]

                price = row[6]

                tx = row[7]

                text = f"""
🐦 LAST SALE

{asset}

Price
{price} BTC

Buyer
{short(buyer)}

https://tokenscan.io/tx/{tx}
"""

                await update.message.reply_text(text)

                return

    await update.message.reply_text("No sales found")


# ------------------------------------------------
# SALES HISTORY
# ------------------------------------------------

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text("Usage: /sales ASSET")

        return

    asset = context.args[0].upper()

    text = f"🐦 {asset} SALES\n\n"

    count = 0

    for start in range(0, MAX_SCAN, STEP):

        url = f"{DISPENSES_BASE}?start={start}&length={STEP}"

        r = requests.get(url).json()

        for row in r["data"]:

            if row[4] == asset:

                price = row[6]

                text += f"{price} BTC\n"

                count += 1

                if count == 10:

                    await update.message.reply_text(text)

                    return

    await update.message.reply_text("No sales found")


# ------------------------------------------------
# FLOOR
# ------------------------------------------------

async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    assets = get_assets()

    prices = []

    for start in range(0, MAX_SCAN, STEP):

        url = f"{DISPENSERS_BASE}?start={start}&length={STEP}"

        r = requests.get(url).json()

        for row in r["data"]:

            asset = row[4]

            if asset in assets:

                price = float(row[6])

                prices.append(price)

    if not prices:

        await update.message.reply_text("No listings")

        return

    floor_price = min(prices)

    text = f"""
🐦 Rare Pigeons Floor

{floor_price} BTC
"""

    await update.message.reply_text(text)


# ------------------------------------------------
# MARKET
# ------------------------------------------------

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text("Usage: /market ASSET")

        return

    asset = context.args[0].upper()

    best_sell = None

    best_buy = None

    for start in range(0, MAX_SCAN, STEP):

        url = f"{ORDERS_BASE}?start={start}&length={STEP}"

        r = requests.get(url).json()

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

                if best_sell is None or price < best_sell:

                    best_sell = price

            if get_asset == asset:

                price = give_qty / get_qty

                if best_buy is None or price > best_buy:

                    best_buy = price

    text = f"🐦 {asset} MARKET\n\n"

    if best_sell:

        text += f"Best SELL\n{best_sell} XCP\n"

    if best_buy:

        text += f"\nBest BUY\n{best_buy} XCP\n"

    if not best_sell and not best_buy:

        text += "No orders found"

    await update.message.reply_text(text)


# ------------------------------------------------
# MENU
# ------------------------------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🐦 Rare Pigeons Bot

Cards
/pigeon ASSET
/random

Market
/ls ASSET
/sales ASSET
/market ASSET
/floor

Menu
/menu
"""

    await update.message.reply_text(text)


# ------------------------------------------------
# RUN BOT
# ------------------------------------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("pigeon", pigeon))

app.add_handler(CommandHandler("random", randompigeon))

app.add_handler(CommandHandler("ls", ls))

app.add_handler(CommandHandler("sales", sales))

app.add_handler(CommandHandler("floor", floor))

app.add_handler(CommandHandler("market", market))

app.add_handler(CommandHandler("menu", menu))

print("Rare Pigeons bot started 🐦")

app.run_polling()
