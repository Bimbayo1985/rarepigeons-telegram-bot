import requests
import random
import os
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"


def get_cards():
    return requests.get(CARDS_JSON).json()["cards"]


def get_card(asset):

    cards = get_cards()

    for c in cards:
        if c["asset"] == asset:
            return c

    return None


def get_asset_page(asset):

    url = f"https://cp20.tokenscan.io/asset/{asset}"
    r = requests.get(url)

    return BeautifulSoup(r.text, "html.parser")


def find_table(soup, title):

    headers = soup.find_all("h4")

    for h in headers:
        if title.lower() in h.text.lower():
            table = h.find_next("table")
            return table

    return None


def parse_rows(table):

    rows = table.find_all("tr")

    data = []

    for r in rows[1:]:

        cols = [c.text.strip() for c in r.find_all("td")]

        links = r.find_all("a")

        link = None

        for a in links:
            if "/tx/" in a.get("href",""):
                link = "https://cp20.tokenscan.io" + a.get("href")

        data.append((cols,link))

    return data


# ---------------- CARD ----------------


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
        caption=f"🐦 {card['asset']}"
    )


async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cards = get_cards()
    card = random.choice(cards)

    await update.message.reply_photo(
        photo=card["image"],
        caption=card["asset"]
    )


# ---------------- LAST SALE ----------------


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /ls ASSET")
        return

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    table = find_table(soup,"Dispenses")

    if not table:
        await update.message.reply_text("No sales found")
        return

    rows = parse_rows(table)

    if not rows:
        await update.message.reply_text("No sales found")
        return

    cols,link = rows[0]

    price = cols[-1]

    card = get_card(asset)
    image = card["image"] if card else None

    text = f"""🐦 LAST SALE

{asset}

{price}

{link}
"""

    if image:
        await update.message.reply_photo(photo=image,caption=text)
    else:
        await update.message.reply_text(text)


# ---------------- FLOOR ----------------


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /floor ASSET")
        return

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    dispenser_floor = None
    dispenser_link = None

    dex_floor = None
    dex_link = None


    # DISPENSERS

    table = find_table(soup,"Dispensers")

    if table:

        rows = parse_rows(table)

        for cols,link in rows:

            price = cols[-1].split()[0]

            p = float(price)

            if dispenser_floor is None or p < dispenser_floor:

                dispenser_floor = p
                dispenser_link = link


    # ORDERS

    table = find_table(soup,"Orders")

    if table:

        rows = parse_rows(table)

        for cols,link in rows:

            try:

                price = float(cols[-1])

                if dex_floor is None or price < dex_floor:

                    dex_floor = price
                    dex_link = link

            except:
                pass


    card = get_card(asset)
    image = card["image"] if card else None

    text = f"🐦 {asset} FLOOR\n\n"

    if dispenser_floor:

        text += f"""Dispenser
{dispenser_floor} BTC
{dispenser_link}

"""

    if dex_floor:

        text += f"""DEX
{dex_floor} XCP
{dex_link}
"""


    if image:
        await update.message.reply_photo(photo=image,caption=text)
    else:
        await update.message.reply_text(text)


# ---------------- MARKET ----------------


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Usage: /market ASSET")
        return

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    table = find_table(soup,"Orders")

    if not table:
        await update.message.reply_text("No orders")
        return

    rows = parse_rows(table)

    best_buy = None
    best_sell = None

    buy_link = None
    sell_link = None


    for cols,link in rows:

        pair = cols[1]

        price = float(cols[-1])

        if pair.startswith(asset):

            if best_sell is None or price < best_sell:

                best_sell = price
                sell_link = link

        if pair.endswith(asset):

            if best_buy is None or price > best_buy:

                best_buy = price
                buy_link = link


    card = get_card(asset)
    image = card["image"] if card else None

    text = f"🐦 {asset} MARKET\n\n"

    if best_sell:

        text += f"""Best SELL
{best_sell} XCP
{sell_link}

"""

    if best_buy:

        text += f"""Best BUY
{best_buy} XCP
{buy_link}
"""


    if image:
        await update.message.reply_photo(photo=image,caption=text)
    else:
        await update.message.reply_text(text)


# ---------------- MENU ----------------


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"""🐦 Rare Pigeons Bot

/pigeon ASSET
/random

/ls ASSET
/floor ASSET
/market ASSET
"""
    )


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("pigeon",pigeon))
app.add_handler(CommandHandler("random",random_card))
app.add_handler(CommandHandler("ls",ls))
app.add_handler(CommandHandler("floor",floor))
app.add_handler(CommandHandler("market",market))
app.add_handler(CommandHandler("menu",menu))

print("Rare Pigeons bot started")

app.run_polling()
