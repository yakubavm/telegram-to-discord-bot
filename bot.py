import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import discord
from discord.ext import tasks

# Завантаження змінних середовища
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID"))  # числовий ID каналу (опціонально)

# Ініціалізація Discord клієнта
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

discord_messages_queue = asyncio.Queue()

@discord_client.event
async def on_ready():
    print(f'Discord бот запущений як {discord_client.user}')
    discord_sender.start()

@tasks.loop(seconds=5)
async def discord_sender():
    channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        print("Discord канал не знайдено!")
        return
    while not discord_messages_queue.empty():
        content = await discord_messages_queue.get()
        await channel.send(content)

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if TELEGRAM_CHANNEL_ID and update.effective_chat.id != TELEGRAM_CHANNEL_ID:
        return

    content = ""

    if message.text:
        content += f"📝 Текст з Telegram:\n{message.text}\n"

    if message.photo:
        photo = message.photo[-1]
        file = await photo.get_file()
        content += f"🖼 Фото: {file.file_path}\n"

    if message.document:
        file = await message.document.get_file()
        content += f"📎 Документ: {file.file_path}\n"

    if message.video:
        file = await message.video.get_file()
        content += f"🎥 Відео: {file.file_path}\n"

    await discord_messages_queue.put(content)

async def run_telegram_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_telegram_message))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # Залишатись в режимі idle, щоб бот не завершився
    await app.updater.idle()
    await app.stop()

async def main():
    await asyncio.gather(
        discord_client.start(DISCORD_TOKEN),
        run_telegram_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
