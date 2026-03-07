import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")


def get_asset_page(asset):
    url = f"https://cp20.tokenscan.io/asset/{asset}"
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return None
    return BeautifulSoup(r.text, "lxml")


def get_image(soup):
    img = soup.select_one("img")
    if img:
        return img["src"]
    return None


def parse_floor(soup):

    btc_floor = None

    rows = soup.find_all("tr")
    for r in rows:
        t = r.get_text(" ", strip=True)

        if "BTC Floor" in t:
            parts = t.split()
            for p in parts:
                if "0.000" in p:
                    btc_floor = p
                    break

    return btc_floor


def parse_orders(soup):

    orders = []

    rows = soup.find_all("tr")

    for r in rows:
        txt = r.get_text(" ", strip=True)

        if "Selling" in txt or "Buying" in txt:
            continue

        if "BTC" in txt and "XCP" not in txt:
            parts = txt.split()

            for p in parts:
                if p.startswith("0.000"):
                    orders.append(p)

    if orders:
        return min(orders)

    return None


def parse_sales(soup):

    rows = soup.find_all("tr")

    for r in rows:
        txt = r.get_text(" ", strip=True)

        if "BTC Paid" in txt:
            parts = txt.split()

            for p in parts:
                if p.startswith("0.000"):
                    return p

    return None


async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    if not soup:
        await update.message.reply_text("Asset not found")
        return

    price = parse_sales(soup)

    if not price:
        await update.message.reply_text("No sales found")
        return

    img = get_image(soup)

    url = f"https://cp20.tokenscan.io/asset/{asset}"

    if img:
        await update.message.reply_photo(
            photo=img,
            caption=f"🐦 LAST SALE\n\n{asset}\n\n{price} BTC\n{url}",
        )
    else:
        await update.message.reply_text(f"{asset}\n{price} BTC\n{url}")


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    if not soup:
        await update.message.reply_text("Asset not found")
        return

    price = parse_floor(soup)

    if not price:
        await update.message.reply_text("No listings")
        return

    img = get_image(soup)

    url = f"https://cp20.tokenscan.io/asset/{asset}"

    if img:
        await update.message.reply_photo(
            photo=img,
            caption=f"🐦 {asset} FLOOR\n\n{price} BTC\n{url}",
        )
    else:
        await update.message.reply_text(f"{asset} floor\n{price} BTC")


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    asset = context.args[0].upper()

    soup = get_asset_page(asset)

    if not soup:
        await update.message.reply_text("Asset not found")
        return

    price = parse_orders(soup)

    if not price:
        await update.message.reply_text("No orders")
        return

    img = get_image(soup)

    url = f"https://cp20.tokenscan.io/asset/{asset}"

    if img:
        await update.message.reply_photo(
            photo=img,
            caption=f"🐦 {asset} MARKET\n\nBest SELL\n{price} BTC\n{url}",
        )
    else:
        await update.message.reply_text(f"{asset}\nBest SELL {price} BTC")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🐦 Rare Pigeons Bot\n\n"
        "/ls ASSET\n"
        "/floor ASSET\n"
        "/market ASSET"
    )


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ls", ls))
    app.add_handler(CommandHandler("floor", floor))
    app.add_handler(CommandHandler("market", market))

    print("Rare Pigeons bot running")

    app.run_polling()


if __name__ == "__main__":
    main()
