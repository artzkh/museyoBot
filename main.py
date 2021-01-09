import os
from dotenv import load_dotenv
from vkbottle.bot import Bot

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

bot = Bot(BOT_TOKEN)


@bot.on.message()
async def handler(_) -> str:
    return "Hello world!"


bot.run_forever()
