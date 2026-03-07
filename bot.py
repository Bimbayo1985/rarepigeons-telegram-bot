import os
import random
import requests
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

cards = requests.get(CARDS_JSON).json()["cards"]

ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


def get_asset_page(asset):

    url = f"https://tokenscan.io/asset/{asset}"

    r = requests.get(url, timeout=20)

    if r.status_code != 200:
        return None

    return BeautifulSoup(r.text, "lxml")


def parse_last_sale(soup):

    table = soup.find("table", {"id": "dispenses-table"})

    if not table:
        return None

    row = table.find("tbody").find("tr")

    cols = row.find_all("td")

    buyer = cols[2].text.strip()
    price = cols[4].text.strip()
    tx = cols[5].find("a")["href"]

    return buyer, price, tx


def parse_floor(soup):

    table = soup.find("table", {"id": "dispensers-table"})

    if not table:
        return None

    rows = table.find("tbody").find_all("tr")

    best_price = None
    seller = None
    tx = None

    for row in rows:

        cols = row.find_all("td")

        price = float(cols[4].text.strip())

        if best_price is None or price < best_price:

            best_price = price
            seller = cols[2].text.strip()
            tx = cols[6].find("a")["href"]

    return best_price, seller, tx


def parse_market(soup):

    table = soup.find("table", {"id": "markets-table"})

    if not table:
        return None

    row = table.find("tbody").find("tr")

    cols = row.find_all("td")

    price = cols[3].text.strip()
    tx = cols[6].find("a")["href"]

    return price, tx


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


async def random_pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = random.choice(ASSET_LIST)

    await update.message.reply_photo(ASSETS[asset], caption=asset)


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    result = parse_last_sale(soup)

    if not result:
        await update.message.reply_text("No sales found")
        return

    buyer, price, tx = result

    caption = f"""🐦 LAST SALE

{asset}

Price
{price} BTC

Buyer
{buyer}

https://tokenscan.io{tx}
"""

    await update.message.reply_photo(ASSETS[asset], caption=caption)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    result = parse_floor(soup)

    if not result:
        await update.message.reply_text("No listings")
        return

    price, seller, tx = result

    caption = f"""🐦 {asset} FLOOR

Price
{price} BTC

Seller
{seller}

https://tokenscan.io{tx}
"""

    await update.message.reply_photo(ASSETS[asset], caption=caption)


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    result = parse_market(soup)

    if not result:
        await update.message.reply_text("No orders")
        return

    price, tx = result

    caption = f"""🐦 {asset} MARKET

Best order

{price} XCP

https://tokenscan.io{tx}
"""

    await update.message.reply_photo(ASSETS[asset], caption=caption)


def main():

    print("Rare Pigeons bot running")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))
    app.add_handler(CommandHandler("random", random_pigeon))

    app.run_polling()


if __name__ == "__main__":
    main()
