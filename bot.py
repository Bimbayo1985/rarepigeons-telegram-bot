import os
import random
import requests
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.getenv("BOT_TOKEN")

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

cards = requests.get(CARDS_JSON).json()["cards"]

ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


def parse_asset_page(asset):

    url = f"https://tokenscan.io/asset/{asset}"

    html = requests.get(url).text

    soup = BeautifulSoup(html, "html.parser")

    return soup


def get_last_sale(asset):

    soup = parse_asset_page(asset)

    table = soup.find("table", {"id": "dispenses-table"})

    if not table:
        return None

    rows = table.find_all("tr")

    if len(rows) < 2:
        return None

    cols = rows[1].find_all("td")

    price = cols[5].text.strip()
    buyer = cols[3].text.strip()

    link = cols[0].find("a")["href"]

    return price, buyer, "https://tokenscan.io" + link


def get_floor(asset):

    soup = parse_asset_page(asset)

    table = soup.find("table", {"id": "dispensers-table"})

    if not table:
        return None

    rows = table.find_all("tr")

    if len(rows) < 2:
        return None

    cols = rows[1].find_all("td")

    price = cols[6].text.strip()
    seller = cols[3].text.strip()

    link = cols[0].find("a")["href"]

    return price, seller, "https://tokenscan.io" + link


def get_market(asset):

    soup = parse_asset_page(asset)

    table = soup.find("table", {"id": "orders-table"})

    if not table:
        return None

    rows = table.find_all("tr")

    if len(rows) < 2:
        return None

    cols = rows[1].find_all("td")

    price = cols[6].text.strip()

    link = cols[0].find("a")["href"]

    return price, "https://tokenscan.io" + link


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_last_sale(asset)

    if not data:
        await update.message.reply_text("No sales found")
        return

    price, buyer, tx = data

    text = f"""
🐦 LAST SALE

{asset}

Price
{price}

Buyer
{buyer}

{tx}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_floor(asset)

    if not data:
        await update.message.reply_text("No listings")
        return

    price, seller, tx = data

    text = f"""
🐦 {asset} FLOOR

Price
{price}

Seller
{seller}

{tx}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    data = get_market(asset)

    if not data:
        await update.message.reply_text("No orders")
        return

    price, tx = data

    text = f"""
🐦 {asset} MARKET

Best order

{price}

{tx}
"""

    await update.message.reply_photo(ASSETS[asset], caption=text)


async def random_card(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(ASSETS[asset], caption=asset)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))
    app.add_handler(CommandHandler("random", random_card))

    app.run_polling()


if __name__ == "__main__":
    main()
