import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import discord
from discord.ext import tasks

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID"))

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
        file_url = file.file_path
        content += f"🖼 Фото: {file_url}\n"

    if message.document:
        file = await message.document.get_file()
        file_url = file.file_path
        content += f"📎 Документ: {file_url}\n"

    if message.video:
        file = await message.video.get_file()
        file_url = file.file_path
        content += f"🎥 Відео: {file_url}\n"

    await discord_messages_queue.put(content)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_telegram_message))

    # Запускаємо Telegram Application без блокування (асинхронно)
    await app.initialize()
    await app.start()
    # Запускаємо polling в окремому таску
    polling_task = asyncio.create_task(app.updater.start_polling())

    # Паралельно запускаємо Discord
    await discord_client.start(DISCORD_TOKEN)

    # Чекаємо завершення polling_task, якщо буде потрібно (тут поки постійно працює)
    await polling_task

if __name__ == "__main__":
    asyncio.run(main())
