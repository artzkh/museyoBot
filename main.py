import os
from random import randint

from vkbottle import API, PhotoWallUploader, PhotoMessageUploader, Keyboard
from dotenv import load_dotenv
from vkbottle import AiohttpClient
from vkbottle.bot import Bot, Message
from vkbottle_types import BaseStateGroup
from bs4 import BeautifulSoup

load_dotenv()
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
USER_TOKEN = str(os.getenv("USER_TOKEN"))
bot = Bot(BOT_TOKEN)
api = API(token=USER_TOKEN)
group_id = 196150271
photo_message_uploader = PhotoMessageUploader(bot.api, generate_attachment_strings=True)
photo_wall_uploader = PhotoWallUploader(api, generate_attachment_strings=True)


class Fields:
    url = "0"
    title = "0"
    year = "0"
    author = "0"
    photo = "0"
    payload = "0"
    description = "0"


ADMINS = {"318378590": Fields(),
          "172736464": Fields()}


class MenuState(BaseStateGroup):
    LINK = 1
    DESCRIPTION = 2


@bot.on.private_message(text="Опубликовать")
async def post_artchive(message: Message):
    peer_id = str(message.peer_id)
    print(message.payload)
    print('{"id":"' + ADMINS[peer_id].payload + '"}')
    if message.payload == '{"id":"' + ADMINS[peer_id].payload + '"}':
        ADMINS[peer_id].payload = "0"
        http = AiohttpClient()
        try:
            print(await api.wall.post(owner_id=-group_id,
                                      message=f"{ADMINS[peer_id].author} — \"{ADMINS[peer_id].title}\"\n\n{ADMINS[peer_id].year}",
                                      attachments=[await photo_wall_uploader.upload(
                                                   path_like=await http.request_content("get", ADMINS[peer_id].photo),
                                                   owner_id=-group_id)],
                                      publish_date=1612961602))
            await message.answer("&#9989; Пост успешно опубликован.")
        except:
            await message.answer("&#10060; Ошибка при публикации поста.")
        await http.close()
    else:
        await message.answer("&#10060; Этот пост уже нельзя опубликовать")


@bot.on.private_message(state=None)
@bot.on.private_message(state=MenuState.LINK)
async def message_handler(message: Message):
    if message.text.find("artchive.ru") != -1:
        if message.text.find("works/") != -1:
            if await parse_artchive(str(message.peer_id), message.text):
                await bot.state_dispenser.set(message.peer_id, MenuState.LINK)
                await message_artchive(str(message.peer_id))
            else:
                await message.answer("&#10060; Произошла ошибка.")
        else:
            await message.answer("&#10060; Произошла ошибка. \n(Ссылка ведёт на Artchive, но не на работу художника.)")
    else:
        await message.answer("&#10060; Неизвестный источник.\nВот список всех доступных:")


async def message_artchive(peer_id):
    http = AiohttpClient()
    ADMINS[peer_id].payload = str(randint(1, 1000))
    await bot.api.messages.send(group_id=group_id,
                                peer_id=peer_id,
                                message=f"{ADMINS[peer_id].author} — \"{ADMINS[peer_id].title}\"\n\n{ADMINS[peer_id].year}",
                                attachment=await photo_message_uploader.upload(
                                           path_like=await http.request_content("get", ADMINS[peer_id].photo),
                                           peer_id=int(peer_id)),
                                keyboard=(Keyboard(inline=True).schema([[{
                                          "label": "Опубликовать",
                                          "type": "text",
                                          "color": "positive",
                                          "payload": '{"id": 'f'"{ADMINS[peer_id].payload}"''}'}
                                          ]]).get_json()),
                                random_id=randint(100, 10000))
    await http.close()


async def parse_artchive(peer_id, url):
    try:
        http = AiohttpClient()
        ADMINS[peer_id].url = str(BeautifulSoup(await http.request_text("get", url), 'html.parser'))
        await http.close()
        ADMINS[peer_id].author = str(BeautifulSoup(ADMINS[peer_id].url, 'html.parser').find('span', 'zoom-in iblock'))
        ADMINS[peer_id].photo = str(BeautifulSoup(ADMINS[peer_id].author, 'html.parser').find('img')['data-src'])
        ADMINS[peer_id].author = str(BeautifulSoup(ADMINS[peer_id].author, 'html.parser').find('img')['title'])
        ADMINS[peer_id].title = ADMINS[peer_id].author[ADMINS[peer_id].author.find(".") + 2:]
        ADMINS[peer_id].author = ADMINS[peer_id].author[:ADMINS[peer_id].author.find(".")]
        if ADMINS[peer_id].author.count(" ") == 2:
            if ADMINS[peer_id].author.find(" фон ") == -1 & ADMINS[peer_id].author.find(" де ") == -1 & \
                    ADMINS[peer_id].author.find(" Ван ") == -1:
                ADMINS[peer_id].author = ADMINS[peer_id].author[:ADMINS[peer_id].author.find(" ")] + \
                                         ADMINS[peer_id].author[ADMINS[peer_id].author.rfind(" "):]
        ADMINS[peer_id].year = str(BeautifulSoup(ADMINS[peer_id].url, 'html.parser').find \
                                       ('div', 'item-info').get_text())
        if ADMINS[peer_id].year.count(",") == 0:
            ADMINS[peer_id].year = ""
        else:
            ADMINS[peer_id].year = ADMINS[peer_id].year[ADMINS[peer_id].year.find(" ") + 1:]
            if ADMINS[peer_id].year.count(",") >= 1:
                ADMINS[peer_id].year = ADMINS[peer_id].year[:ADMINS[peer_id].year.find(",")]
            if ADMINS[peer_id].year.find("е") == -1:
                if ADMINS[peer_id].year != "":
                    ADMINS[peer_id].year += " г."
        return True
    except:
        return False


bot.run_forever()
