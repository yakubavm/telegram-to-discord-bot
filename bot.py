import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import discord
from discord.ext import tasks

# Зчитування токенів і ID з оточення
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
    print(f"Discord бот запущений як {discord_client.user}")
    if not discord_sender.is_running():
        discord_sender.start()

@tasks.loop(seconds=5)
async def discord_sender():
    channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        print("Discord канал не знайдено!")
        return

    while not discord_messages_queue.empty():
        content = await discord_messages_queue.get()
        try:
            await channel.send(content)
            print("Повідомлення відправлено у Discord")
        except Exception as e:
            print(f"Помилка при відправленні у Discord: {e}")

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # Перевірка, що повідомлення з потрібного Telegram-каналу/чату
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
        print("Отримано повідомлення з Telegram, додано до черги Discord")

async def main():
    # Ініціалізація Telegram бота
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_telegram_message))

    await app.initialize()
    await app.start()
    polling_task = asyncio.create_task(app.updater.start_polling())

    # Логін і коннект Discord бота
    await discord_client.login(DISCORD_TOKEN)
    discord_task = asyncio.create_task(discord_client.connect())

    # Чекаємо одночасно завершення обох тасків (будуть працювати вічно)
    await asyncio.gather(polling_task, discord_task)

if __name__ == "__main__":
    asyncio.run(main())
