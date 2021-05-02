import os
from datetime import datetime, time
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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

timestamp = int(open('timestamp.txt', 'r').read())
low_time = time(12, 0, 0)
high_time = time(23, 59, 59)
print("Hello world")

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
    global timestamp
    peer_id = str(message.peer_id)
    if message.payload == '{"id":"' + ADMINS[peer_id].payload + '"}':
        ADMINS[peer_id].payload = "0"
        http = AiohttpClient()
        try:
            await api.wall.post(owner_id=-group_id,
                                message=f"{ADMINS[peer_id].author} — "
                                        f"\"{ADMINS[peer_id].title}\"\n"
                                        f"\n{ADMINS[peer_id].year}",
                                attachments=[await photo_wall_uploader.upload(
                                    path_like=await http.request_content("get", ADMINS[peer_id].photo),
                                    owner_id=-group_id)],
                                publish_date=timestamp)
            timestamp += randint(7000, 11000)
            timestamp_time = datetime.fromtimestamp(timestamp).time()
            while low_time > timestamp_time or timestamp_time > high_time:
                timestamp += 3600
                timestamp_time = datetime.fromtimestamp(timestamp).time()
            open('timestamp.txt', 'w').write(str(timestamp))
            date = datetime.fromtimestamp(timestamp)
            await message.answer("&#9989; Пост успешно опубликован.\n"
                                 f"Следующий пост {date.strftime('%d.%m')} в {date.strftime('%H:%M')}")
        except Exception as err:
            print(err)
            await message.answer("&#10060; Ошибка при публикации поста.")
        await http.close()
    else:
        await message.answer("&#10060; Этот пост уже нельзя опубликовать")


@bot.on.private_message(state=None)
@bot.on.private_message(state=MenuState.LINK)
async def message_handler(message: Message):
    if message.text.find("http") != -1:
        if message.text.find("artchive.ru") != -1:
            if message.text.find("works/") != -1:
                if await parse_artchive(str(message.peer_id), message.text):
                    await bot.state_dispenser.set(message.peer_id, MenuState.LINK)
                    await message_artchive(str(message.peer_id))
                else:
                    await message.answer("&#10060; Произошла ошибка.")
            else:
                await message.answer("&#10060; Произошла ошибка. \n"
                                     "(Ссылка ведёт на артхив, но не на работу художника.)")
        elif message.text.find("artstation") != -1:
            if message.text.find("artwork/") != -1:
                if await parse_artstation(str(message.peer_id), message.text):
                    await bot.state_dispenser.set(message.peer_id, MenuState.LINK)
                    await message_artstation(str(message.peer_id))
            else:
                await message.answer("&#10060; Произошла ошибка. \n"
                                     "(Ссылка ведёт на artstation, но не на работу художника.)")
        else:
            await message.answer("&#10060; Неизвестный источник.\n\nВот список всех доступных:"
                                 "\n1. artchive.ru")
    else:
        date = datetime.fromtimestamp(timestamp)
        if date.day == datetime.today().day:
            await message.answer(f"Ближайший пост сегодня в {date.timetz()}")
        elif date.day == datetime.today().day-1:
            await message.answer(f"Ближайший пост завтра в {date.timetz()}")
        else:
            await message.answer(f"Ближайший пост {date.strftime('%d.%m')}"
                                 f" в {date.strftime('%H:%M')}")


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
        try:
            ADMINS[peer_id].photo = str(BeautifulSoup(ADMINS[peer_id].author, 'html.parser').find('img')['src'])
        except:
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
        if (ADMINS[peer_id].year.count(",") == 0) or \
           (ADMINS[peer_id].year.count(",") == 1 and ADMINS[peer_id].year.count("см") == 1):
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


async def message_artstation(peer_id):
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


async def parse_artstation(peer_id, url):
    try:
        options = Options()
        browser = webdriver.Chrome(executable_path=r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe', options=options)
        print(1)
        print(BeautifulSoup(browser.get(url).page_source, 'html.parser'))
        print(2)
        print(ADMINS[peer_id].url)
        ADMINS[peer_id].author = str(BeautifulSoup(ADMINS[peer_id].url, 'html.parser').find("div", class_="artwork-info ps-container"))
        print(ADMINS[peer_id].author)
        try:
            ADMINS[peer_id].photo = str(BeautifulSoup(ADMINS[peer_id].author, 'html.parser').find('img')['src'])
        except:
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
        if (ADMINS[peer_id].year.count(",") == 0) or \
           (ADMINS[peer_id].year.count(",") == 1 and ADMINS[peer_id].year.count("см") == 1):
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
