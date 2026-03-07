import os
import random
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

ASSET_URL = "https://tokenscan.io/asset/{}"

CARDS_JSON = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"

cards = requests.get(CARDS_JSON).json()["cards"]
ASSETS = {c["asset"]: c["image"] for c in cards}
ASSET_LIST = list(ASSETS.keys())


# ---------------- PAGE ----------------

def load_page(asset):

    r = requests.get(ASSET_URL.format(asset), timeout=20)

    if r.status_code != 200:
        return None

    return BeautifulSoup(r.text, "lxml")


# ---------------- DISPENSES ----------------

def parse_last_sale(soup):

    tables = soup.find_all("table")

    for table in tables:

        thead = table.find("thead")

        if not thead:
            continue

        if "BTC Paid" in thead.text:

            row = table.find("tbody").find("tr")
            cols = row.find_all("td")

            buyer = cols[2].text.strip()
            price = cols[4].text.strip()

            link = cols[5].find("a")["href"]
            tx = link.split("/")[-1]

            return price, buyer, tx

    return None


# ---------------- DISPENSERS ----------------

def parse_floor(soup):

    tables = soup.find_all("table")

    for table in tables:

        thead = table.find("thead")

        if not thead:
            continue

        if "Remaining" in thead.text:

            rows = table.find("tbody").find_all("tr")

            best_price = None
            best_tx = None
            seller = None

            for r in rows:

                cols = r.find_all("td")

                price = float(cols[4].text.strip())
                s = cols[2].text.strip()

                link = cols[5].find("a")["href"]
                tx = link.split("/")[-1]

                if best_price is None or price < best_price:

                    best_price = price
                    seller = s
                    best_tx = tx

            return best_price, seller, best_tx

    return None


# ---------------- MARKET ----------------

def parse_market(soup):

    tables = soup.find_all("table")

    for table in tables:

        thead = table.find("thead")

        if not thead:
            continue

        if "Price" in thead.text and "XCP" in table.text:

            row = table.find("tbody").find("tr")

            cols = row.find_all("td")

            price = cols[-1].text.strip()

            return price

    return None


# ---------------- COMMANDS ----------------

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

    asset = context.args[0].upper()

    soup = load_page(asset)

    data = parse_last_sale(soup)

    if not data:

        await update.message.reply_text("No sales found")
        return

    price, buyer, tx = data

    caption = f"""🐦 LAST SALE

{asset}

Price
{price} BTC

Buyer
{buyer}

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    soup = load_page(asset)

    data = parse_floor(soup)

    if not data:

        await update.message.reply_text("No listings")
        return

    price, seller, tx = data

    caption = f"""🐦 {asset} FLOOR

Price
{price} BTC

Seller
{seller}

https://tokenscan.io/tx/{tx}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    asset = context.args[0].upper()

    soup = load_page(asset)

    price = parse_market(soup)

    if not price:

        await update.message.reply_text("No orders")
        return

    caption = f"""🐦 {asset} MARKET

Best SELL

{price}
"""

    await update.message.reply_photo(
        photo=ASSETS.get(asset),
        caption=caption
    )


# ---------------- MAIN ----------------

def main():

    print("Rare Pigeons bot running")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))

    app.add_handler(CommandHandler("pigeon", pigeon))
    app.add_handler(CommandHandler("random", random_pigeon))

    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
