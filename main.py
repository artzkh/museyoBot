import os
from dotenv import load_dotenv
from vkbottle import AiohttpClient
from vkbottle.bot import Bot, Message
from vkbottle_types import BaseStateGroup
from bs4 import BeautifulSoup

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
bot = Bot(BOT_TOKEN)

ADMINS = {"id": {"url": 1, "photo": 1, "description": 1},
          "id2": {"url": 1, "photo": 1, "description": 1}}


class MenuState(BaseStateGroup):
    MENU = 1
    LINK = 2
    DESCRIPTION = 3


@bot.on.private_message(state=None)
@bot.on.private_message(state=MenuState.MENU)
async def message_handler(message: Message):
    await message.answer("Пришли мне ссылку на пост")
    await bot.state_dispenser.set(message.peer_id, MenuState.LINK)


@bot.on.private_message(state=MenuState.LINK)
async def message_handler(message: Message):
    await message.answer("1")
    http = AiohttpClient()
    print(BeautifulSoup(await http.request_text("get", "https://google.com"), 'html.parser').find_all('table'))
    await http.close()
    await bot.state_dispenser.set(message.peer_id, MenuState.MENU)


bot.run_forever()
