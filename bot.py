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

# Черга повідомлень для Discord
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

    # Перевірка, що повідомлення з потрібного каналу (опціонально)
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
    # Запускаємо Telegram бот
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Додаємо хендлер для всіх типів повідомлень
    app.add_handler(MessageHandler(filters.ALL, handle_telegram_message))

    # Паралельно запускаємо Discord і Telegram боти
    await asyncio.gather(
        discord_client.start(DISCORD_TOKEN),
        app.run_polling()
    )

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
