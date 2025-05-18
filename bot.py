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

# Зберігаємо повідомлення, які треба відправити у Discord (через чергу)
discord_messages_queue = asyncio.Queue()

@discord_client.event
async def on_ready():
    print(f'Discord бот запущений як {discord_client.user}')
    # Запускаємо таск, який надсилатиме повідомлення в Discord
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

# Telegram хендлер для тексту, фото, документів тощо
async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # Перевіряємо, що повідомлення з потрібного каналу (опціонально)
    if TELEGRAM_CHANNEL_ID and update.effective_chat.id != TELEGRAM_CHANNEL_ID:
        return

    content = ""

    if message.text:
        content += f"📝 Текст з Telegram:\n{message.text}\n"

    # Якщо фото
    if message.photo:
        # беремо останнє (найкращу якість)
        photo = message.photo[-1]
        file = await photo.get_file()
        file_url = file.file_path
        content += f"🖼 Фото: {file_url}\n"

    # Якщо документ (pdf, відео і т.п.)
    if message.document:
        file = await message.document.get_file()
        file_url = file.file_path
        content += f"📎 Документ: {file_url}\n"

    # Якщо відео
    if message.video:
        file = await message.video.get_file()
        file_url = file.file_path
        content += f"🎥 Відео: {file_url}\n"

    # Відправляємо у чергу повідомлень для Discord
    await discord_messages_queue.put(content)

async def main():
    # Запускаємо Telegram бот
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Додаємо хендлер на всі типи повідомлень
    app.add_handler(MessageHandler(filters.ALL, handle_telegram_message))

    # Запускаємо Discord бота і Telegram бот паралельно
    await asyncio.gather(
        discord_client.start(DISCORD_TOKEN),
        app.run_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())