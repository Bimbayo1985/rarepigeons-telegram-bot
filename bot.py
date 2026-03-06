import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"

JSON_URL = "PASTE_YOUR_GITHUB_JSON_URL"

async def pigeon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Use: /pigeon CARDNAME")
        return

    card_name = context.args[0].upper()

    data = requests.get(JSON_URL).json()

    for card in data:

        if card["asset"] == card_name:

            image = card["image"]

            text = f"""
🐦 {card_name}

❤️ HP: {card["hp"]}
⚔️ ATK: {card["atk"]}
⚡ SPD: {card["spd"]}

⭐ Rareness: {card["rarity"]}
"""

            await update.message.reply_photo(photo=image, caption=text)
            return

    await update.message.reply_text("Pigeon not found")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("pigeon", pigeon))

app.run_polling()
