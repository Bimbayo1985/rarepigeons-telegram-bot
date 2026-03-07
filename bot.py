import requests
import random
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.environ["BOT_TOKEN"]

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


def short(a):

    return a[:6] + "..." + a[-4:]


def cards():

    return requests.get(CARDS_JSON).json()["cards"]


# ------------------------------------------------
# CARD
# ------------------------------------------------

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    c = cards()

    if not context.args:

        card = random.choice(c)

    else:

        name = context.args[0].upper()

        card = None

        for i in c:

            if i["asset"] == name:

                card = i

        if not card:

            await update.message.reply_text("Card not found")
            return

    await update.message.reply_photo(
        photo=card["image"],
        caption=f"🐦 {card['asset']}\n\nhttps://www.rarepigeons.com"
    )


async def randompigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    c = cards()

    card = random.choice(c)

    await update.message.reply_photo(photo=card["image"], caption=card["asset"])


# ------------------------------------------------
# LAST SALE
# ------------------------------------------------

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    # BTC dispenser sales

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{DISPENSES}?start={start}&length={STEP}").json()

        for row in r["data"]:

            a = clean(row[4])

            if a == asset:

                price = row[6]
                tx = row[7]

                await update.message.reply_text(
                    f"🐦 LAST SALE\n\n{asset}\n\n{price} BTC\n\nhttps://cp20.tokenscan.io/tx/{tx}"
                )

                return

    # XCP DEX sales

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset = clean(row[4])
            get_asset = clean(row[6])
            status = row[7]

            if status=="filled" and give_asset==asset:

                give = float(row[3])
                get = float(row[5])

                price = get/give

                await update.message.reply_text(
                    f"🐦 LAST SALE\n\n{asset}\n\n{price} XCP"
                )

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

    # BTC dispenser

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{DISPENSES}?start={start}&length={STEP}").json()

        for row in r["data"]:

            a = clean(row[4])

            if a == asset:

                text += f"{row[6]} BTC\n"

                count+=1

                if count==10:

                    await update.message.reply_text(text)

                    return

    # XCP DEX

    for start in range(0,SCAN,STEP):

        r = requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset = clean(row[4])
            status = row[7]

            if status=="filled" and give_asset==asset:

                give=float(row[3])
                get=float(row[5])

                text+=f"{get/give} XCP\n"

                count+=1

                if count==10:

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

    asset=context.args[0].upper()

    floors=[]

    # DEX floor

    for start in range(0,SCAN,STEP):

        r=requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset=clean(row[4])
            status=row[7]

            if status=="open" and give_asset==asset:

                give=float(row[3])
                get=float(row[5])

                floors.append(get/give)

    # dispenser floor

    for start in range(0,SCAN,STEP):

        r=requests.get(f"{DISPENSERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            a=clean(row[4])

            if a==asset:

                floors.append(float(row[6]))

    if not floors:

        await update.message.reply_text("No listings")

        return

    floor_price=min(floors)

    await update.message.reply_text(f"🐦 {asset} FLOOR\n\n{floor_price}")


# ------------------------------------------------
# MARKET
# ------------------------------------------------

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Usage: /market ASSET")
        return

    asset=context.args[0].upper()

    best_sell=None
    best_buy=None

    for start in range(0,SCAN,STEP):

        r=requests.get(f"{ORDERS}?start={start}&length={STEP}").json()

        for row in r["data"]:

            give_asset=clean(row[4])
            get_asset=clean(row[6])
            status=row[7]

            if status!="open":

                continue

            give=float(row[3])
            get=float(row[5])

            if give_asset==asset:

                price=get/give

                if best_sell is None or price<best_sell:

                    best_sell=price

            if get_asset==asset:

                price=give/get

                if best_buy is None or price>best_buy:

                    best_buy=price

    text=f"🐦 {asset} MARKET\n\n"

    if best_sell:

        text+=f"Best SELL\n{best_sell} XCP\n"

    if best_buy:

        text+=f"\nBest BUY\n{best_buy} XCP\n"

    if not best_sell and not best_buy:

        text+="No orders"

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

/menu
"""
    )


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
app.add_handler(CommandHandler("menu", menu))

print("Rare Pigeons bot started")

app.run_polling()
