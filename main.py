import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command

from config import TOKEN
from handlers import (
    command_start_handler,
    help_handler,
    on_new_member,
    captcha_callback,
    add_word,
    filter_handler
)

dp = Dispatcher()

dp.message.register(command_start_handler, CommandStart())
dp.message.register(help_handler, Command("help"))
dp.chat_member.register(on_new_member)
dp.message.register(add_word, Command("addword"))
dp.message.register(filter_handler, F.chat.type.in_({"group", "supergroup"}))
dp.callback_query.register(captcha_callback)

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())