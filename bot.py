import requests
import random
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]

JSON_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"
LEADERBOARD_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/leaderboard.json"

DISPENSES_URL = "https://tokenscan.io/explorer/dispenses?start=0&length=100"
DISPENSERS_URL = "https://tokenscan.io/explorer/dispensers?start=0&length=100"
ORDERS_URL = "https://tokenscan.io/explorer/orders?start=0&length=100"


def load_cards():
    data = requests.get(JSON_URL).json()
    return data["cards"]


def get_assets():
    return {c["asset"]: c["image"] for c in load_cards()}


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
            await update.message.reply_text("Card not found 🐦")
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

    await update.message.reply_photo(
        photo=card["image"],
        caption=f"🐦 {card['asset']}"
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🐦 Rare Pigeons Bot

Cards
/pigeon ASSET
/random

Market
/ls ASSET
/sales ASSET
/price ASSET
/market ASSET
/floor

Leaderboard
/leaderboard
/leaderboard ADDRESS
"""

    await update.message.reply_text(text)


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = requests.get(LEADERBOARD_URL).json()

    if len(context.args) == 0:

        text = "🏆 Rare Pigeons Leaderboard\n\n"

        for i, row in enumerate(data[:20]):
            addr = row["address"]
            cards = row["cards"]
            percent = row["percent"]

            text += f"{i+1}. {addr[:6]}...{addr[-4:]}\n"
            text += f"Cards: {cards} ({percent}%)\n\n"

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


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    r = requests.get(DISPENSES_URL).json()

    for row in r["data"]:

        if row[4] == asset:

            price = row[6]
            tx = row[7]

            text = f"""
🐦 LAST SALE

{asset}

Price
{price} BTC

TX
https://tokenscan.io/tx/{tx}
"""

            await update.message.reply_text(text)
            return

    await update.message.reply_text("No sales found")


async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /sales ASSET")
        return

    asset = context.args[0].upper()

    r = requests.get(DISPENSES_URL).json()

    text = f"🐦 {asset} SALES\n\n"

    count = 0

    for row in r["data"]:

        if row[4] == asset:

            price = row[6]
            text += f"{price} BTC\n"
            count += 1

            if count == 5:
                break

    await update.message.reply_text(text)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    assets = get_assets()

    r = requests.get(DISPENSERS_URL).json()

    btc_prices = []

    for row in r["data"]:

        asset = row[4]

        if asset in assets:

            price = float(row[6])
            btc_prices.append(price)

    if not btc_prices:
        await update.message.reply_text("No listings")
        return

    floor_price = min(btc_prices)

    await update.message.reply_text(
        f"🐦 Rare Pigeons Floor\n\nBTC floor\n{floor_price} BTC"
    )


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /market ASSET")
        return

    asset = context.args[0].upper()

    r = requests.get(ORDERS_URL).json()

    sell = None
    buy = None

    for row in r["data"]:

        give_asset = row[4]
        get_asset = row[6]
        status = row[7]

        if status != "open":
            continue

        if give_asset == asset:

            price = float(row[3]) / float(row[5])

            if sell is None or price < sell:
                sell = price

        if get_asset == asset:

            price = float(row[5]) / float(row[3])

            if buy is None or price > buy:
                buy = price

    text = f"🐦 {asset} MARKET\n\n"

    if sell:
        text += f"Best SELL\n{sell} XCP\n"

    if buy:
        text += f"\nBest BUY\n{buy} XCP\n"

    await update.message.reply_text(text)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("pigeon", pigeon))
app.add_handler(CommandHandler("random", randompigeon))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("ls", ls))
app.add_handler(CommandHandler("sales", sales))
app.add_handler(CommandHandler("floor", floor))
app.add_handler(CommandHandler("market", market))

print("Rare Pigeons bot started 🐦")

app.run_polling()
