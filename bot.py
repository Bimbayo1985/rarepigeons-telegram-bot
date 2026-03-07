import requests
import random
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]

JSON_URL = "https://raw.githubusercontent.com/Bimbayo1985/rare-pigeons-assets/main/list.json"


async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    try:
        data = requests.get(JSON_URL).json()
        cards = data["cards"]
    except:
        await update.message.reply_text("Error loading pigeons 🐦")
        return

    # якщо команда без аргументів → random карта
    if len(context.args) == 0:
        card = random.choice(cards)

    else:
        name = context.args[0].upper()
        card = None

        for c in cards:
            if c["asset"] == name:
                card = c
                break

        if card is None:
            await update.message.reply_text("Pigeon not found 🐦")
            return

    asset = card["asset"]
    image = card["image"]

    caption = f"""
🐦 {asset}

Rare Pigeons card

View collection:
https://www.rarepigeons.com
"""

    await update.message.reply_photo(photo=image, caption=caption)


async def randompigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    try:
        data = requests.get(JSON_URL).json()
        cards = data["cards"]
    except:
        await update.message.reply_text("Error loading pigeons 🐦")
        return

    card = random.choice(cards)

    asset = card["asset"]
    image = card["image"]

    caption = f"""
🐦 {asset}

Random Rare Pigeon
https://www.rarepigeons.com
"""

    await update.message.reply_photo(photo=image, caption=caption)


# тимчасова команда для отримання chat_id
async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    await update.message.reply_text(f"Chat ID: {update.effective_chat.id}")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("pigeon", pigeon))
app.add_handler(CommandHandler("random", randompigeon))
app.add_handler(CommandHandler("chatid", chatid))

print("Rare Pigeons bot started 🐦")

app.run_polling()
