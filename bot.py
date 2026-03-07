import requests
import random
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

ORDERS = "https://cp20.tokenscan.io/explorer/orders"
DISPENSES = "https://cp20.tokenscan.io/explorer/dispenses"
DISPENSERS = "https://cp20.tokenscan.io/explorer/dispensers"

SCAN = 2000
STEP = 100


# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def clean(x):
    return str(x).replace("|","")


def get_cards():
    return requests.get(CARDS_JSON).json()["cards"]


def get_card(asset):

    cards = get_cards()

    for c in cards:
        if c["asset"] == asset:
            return c

    return None


# ------------------------------------------------
# CARD
# ------------------------------------------------

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = get_cards()

    if not context.args:
        card = random.choice(cards)
    else:

        asset = context.args[0].upper()

        card = get_card(asset)

        if not card:
            await update.message.reply_text("Card not found")
            return

    await update.message.reply_photo(
        photo=card["image"],
        caption=f"🐦 {card['asset']}\n\nhttps://www.rarepigeons.com"
    )


async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = get_cards()

    card = random.choice(cards)

    await update.message.reply_photo(
        photo=card["image"],
        caption=card["asset"]
    )


# ------------------------------------------------
# LAST SALE
# ------------------------------------------------

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    card = get_card(asset)
    image = card["image"] if card else None


    # DISPENSER SALES

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{DISPENSES}?start={start}&length={STEP}").json()

        for row in r["data"]:

            a = clean(row[5])

            if a == asset:

                price = float(row[6])
                tx = row[7]

                text = f"""🐦 LAST SALE

{asset}

{price:.8f} BTC

https://cp20.tokenscan.io/tx/{tx}
"""

                if image:
                    await update.message.reply_photo(photo=image, caption=text)
                else:
                    await update.message.reply_text(text)

                return


    # DEX SALES

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset = clean(row[4])
            status = row[7]

            if status == "filled" and give_asset == asset:

                give = float(row[3])
                get = float(row[5])
                price = get/give

                tx = row[8]

                text = f"""🐦 LAST SALE

{asset}

{price:.8f} XCP

https://cp20.tokenscan.io/tx/{tx}
"""

                if image:
                    await update.message.reply_photo(photo=image, caption=text)
                else:
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

    card = get_card(asset)
    image = card["image"] if card else None

    text = f"🐦 {asset} SALES\n\n"
    count = 0


    # DISPENSER SALES

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{DISPENSES}?start={start}&length={STEP}").json()

        for row in r["data"]:

            a = clean(row[5])

            if a == asset:

                price = float(row[6])

                text += f"{price:.8f} BTC\n"

                count += 1

                if count == 10:

                    if image:
                        await update.message.reply_photo(photo=image, caption=text)
                    else:
                        await update.message.reply_text(text)

                    return


    # DEX SALES

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset = clean(row[4])
            status = row[7]

            if status == "filled" and give_asset == asset:

                give = float(row[3])
                get = float(row[5])
                price = get/give

                text += f"{price:.8f} XCP\n"

                count += 1

                if count == 10:

                    if image:
                        await update.message.reply_photo(photo=image, caption=text)
                    else:
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

    card = get_card(asset)
    image = card["image"] if card else None

    floors = []


    # DEX FLOOR

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset = clean(row[4])
            status = row[7]

            if status == "open" and give_asset == asset:

                give = float(row[3])
                get = float(row[5])
                price = get/give

                tx = row[8]

                floors.append({
                    "price": price,
                    "type": "XCP",
                    "link": f"https://cp20.tokenscan.io/tx/{tx}"
                })


    # DISPENSER FLOOR

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{DISPENSERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            a = clean(row[4])

            if a == asset:

                price = float(row[6])
                tx = row[8]

                floors.append({
                    "price": price,
                    "type": "BTC",
                    "link": f"https://cp20.tokenscan.io/tx/{tx}"
                })


    if not floors:
        await update.message.reply_text("No listings")
        return


    best = min(floors, key=lambda x: x["price"])

    text = f"""🐦 {asset} FLOOR

{best['price']:.8f} {best['type']}

{best['link']}
"""

    if image:
        await update.message.reply_photo(photo=image, caption=text)
    else:
        await update.message.reply_text(text)


# ------------------------------------------------
# MARKET
# ------------------------------------------------

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /market ASSET")
        return

    asset = context.args[0].upper()

    card = get_card(asset)
    image = card["image"] if card else None

    best_buy = None
    best_sell = None


    for start in range(0,SCAN,STEP):

        r = requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset = clean(row[4])
            get_asset = clean(row[6])
            status = row[7]

            if status != "open":
                continue

            give = float(row[3])
            get = float(row[5])
            tx = row[8]

            if give_asset == asset:

                price = get/give

                if best_sell is None or price < best_sell["price"]:
                    best_sell = {"price":price,"tx":tx}

            if get_asset == asset:

                price = give/get

                if best_buy is None or price > best_buy["price"]:
                    best_buy = {"price":price,"tx":tx}


    text = f"🐦 {asset} MARKET\n\n"

    if best_sell:

        text += f"Best SELL\n{best_sell['price']:.8f} XCP\n"
        text += f"https://cp20.tokenscan.io/tx/{best_sell['tx']}\n\n"

    if best_buy:

        text += f"Best BUY\n{best_buy['price']:.8f} XCP\n"
        text += f"https://cp20.tokenscan.io/tx/{best_buy['tx']}"

    if image:
        await update.message.reply_photo(photo=image, caption=text)
    else:
        await update.message.reply_text(text)


# ------------------------------------------------
# MENU
# ------------------------------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"""🐦 Rare Pigeons Bot

/pigeon ASSET
/random

/ls ASSET
/sales ASSET
/floor ASSET
/market ASSET
"""
    )


# ------------------------------------------------
# RUN
# ------------------------------------------------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("pigeon", pigeon))
app.add_handler(CommandHandler("random", random_card))
app.add_handler(CommandHandler("ls", ls))
app.add_handler(CommandHandler("sales", sales))
app.add_handler(CommandHandler("floor", floor))
app.add_handler(CommandHandler("market", market))
app.add_handler(CommandHandler("menu", menu))

print("Rare Pigeons bot started")

app.run_polling()
