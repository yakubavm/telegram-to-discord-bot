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
    channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        print(f"Не вдалося знайти Discord канал з ID: {DISCORD_CHANNEL_ID}")
    else:
        print(f"Discord канал для надсилання: {channel.name} (ID: {DISCORD_CHANNEL_ID})")
    discord_sender.start()

@tasks.loop(seconds=5)
async def discord_sender():
    channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        print("Discord канал не знайдено!")
        return
    if not discord_messages_queue.empty():
        content = await discord_messages_queue.get()
        try:
            await channel.send(content)
            print(f"Відправлено в Discord: {content}")
        except Exception as e:
            print(f"Помилка відправки в Discord: {e}")

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # Фільтр за каналом (якщо заданий)
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

    if content:
        await discord_messages_queue.put(content)
        print(f"Повідомлення додано в чергу: {content}")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_telegram_message))

    await asyncio.gather(
        discord_client.start(DISCORD_TOKEN),
        app.run_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())
