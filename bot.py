import requests
import random
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.environ["BOT_TOKEN"]

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"
LEADERBOARD_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/leaderboard.json"

ORDERS_URL = "https://cp20.tokenscan.io/explorer/orders"
DISPENSES_URL = "https://cp20.tokenscan.io/explorer/dispenses"
DISPENSERS_URL = "https://cp20.tokenscan.io/explorer/dispensers"

SCAN_LIMIT = 2000
STEP = 100


# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def clean(asset):

    return str(asset).replace("|", "")


def short(addr):

    return addr[:6] + "..." + addr[-4:]


def load_cards():

    return requests.get(CARDS_JSON).json()["cards"]


# ------------------------------------------------
# CARDS
# ------------------------------------------------

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = load_cards()

    if len(context.args) == 0:

        card = random.choice(cards)

    else:

        asset = context.args[0].upper()

        card = None

        for c in cards:

            if c["asset"] == asset:
                card = c

        if not card:

            await update.message.reply_text("Card not found")
            return

    caption = f"""
🐦 {card['asset']}

Rare Pigeons

https://www.rarepigeons.com
"""

    await update.message.reply_photo(photo=card["image"], caption=caption)


async def randompigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = load_cards()

    card = random.choice(cards)

    await update.message.reply_photo(photo=card["image"], caption=card["asset"])


# ------------------------------------------------
# LAST SALE
# ------------------------------------------------

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    # DEX SALES

    for start in range(0, SCAN_LIMIT, STEP):

        r = requests.get(f"{ORDERS_URL}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_qty = float(row[3])
            give_asset = clean(row[4])

            get_qty = float(row[5])
            get_asset = clean(row[6])

            status = row[7]
            tx = row[8]

            if status == "filled" and give_asset == asset:

                price = get_qty / give_qty

                text = f"""
🐦 LAST SALE

{asset}

Price
{price} XCP

https://cp20.tokenscan.io/tx/{tx}
"""

                await update.message.reply_text(text)

                return

    await update.message.reply_text("No sales found")


# ------------------------------------------------
# SALES
# ------------------------------------------------

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Usage: /sales ASSET")
        return

    asset = context.args[0].upper()

    text = f"🐦 {asset} SALES\n\n"

    count = 0

    for start in range(0, SCAN_LIMIT, STEP):

        r = requests.get(f"{ORDERS_URL}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_qty = float(row[3])
            give_asset = clean(row[4])

            get_qty = float(row[5])
            get_asset = clean(row[6])

            status = row[7]

            if status == "filled" and give_asset == asset:

                price = get_qty / give_qty

                text += f"{price} XCP\n"

                count += 1

                if count == 10:

                    await update.message.reply_text(text)

                    return

    await update.message.reply_text("No sales found")


# ------------------------------------------------
# FLOOR
# ------------------------------------------------

async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Usage: /floor ASSET")
        return

    asset = context.args[0].upper()

    prices = []

    for start in range(0, SCAN_LIMIT, STEP):

        r = requests.get(f"{ORDERS_URL}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_qty = float(row[3])
            give_asset = clean(row[4])

            get_qty = float(row[5])
            get_asset = clean(row[6])

            status = row[7]

            if status == "open" and give_asset == asset:

                price = get_qty / give_qty

                prices.append(price)

    if not prices:

        await update.message.reply_text("No listings")

        return

    floor_price = min(prices)

    text = f"""
🐦 {asset} FLOOR

{floor_price} XCP
"""

    await update.message.reply_text(text)


# ------------------------------------------------
# MARKET
# ------------------------------------------------

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Usage: /market ASSET")
        return

    asset = context.args[0].upper()

    best_sell = None
    best_buy = None

    for start in range(0, SCAN_LIMIT, STEP):

        r = requests.get(f"{ORDERS_URL}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_qty = float(row[3])
            give_asset = clean(row[4])

            get_qty = float(row[5])
            get_asset = clean(row[6])

            status = row[7]

            if status != "open":
                continue

            # sell order

            if give_asset == asset:

                price = get_qty / give_qty

                if best_sell is None or price < best_sell:

                    best_sell = price

            # buy order

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

        text += "No orders"

    await update.message.reply_text(text)


# ------------------------------------------------
# LEADERBOARD
# ------------------------------------------------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = requests.get(LEADERBOARD_JSON).json()

    if not context.args:

        text = "🏆 Rare Pigeons Leaderboard\n\n"

        for i, row in enumerate(data[:20]):

            addr = row["address"]

            text += f"{i+1}. {short(addr)}\n"
            text += f"Cards {row['cards']} ({row['percent']}%)\n\n"

        await update.message.reply_text(text)

    else:

        addr = context.args[0]

        for i, row in enumerate(data):

            if row["address"] == addr:

                text = f"""
🏆 Rare Pigeons Rank

Address
{addr}

Rank
#{i+1}

Cards
{row['cards']}

Collection
{row['percent']}%

Missing
{row['missing']}
"""

                await update.message.reply_text(text)

                return

        await update.message.reply_text("Address not found")


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
/floor ASSET
/market ASSET

Leaderboard
/leaderboard
/leaderboard ADDRESS

/menu
"""

    await update.message.reply_text(text)


# ------------------------------------------------
# RUN
# ------------------------------------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("pigeon", pigeon))
app.add_handler(CommandHandler("random", randompigeon))
app.add_handler(CommandHandler("ls", ls))
app.add_handler(CommandHandler("sales", sales))
app.add_handler(CommandHandler("floor", floor))
app.add_handler(CommandHandler("market", market))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("menu", menu))

print("Rare Pigeons bot started 🐦")

app.run_polling()
