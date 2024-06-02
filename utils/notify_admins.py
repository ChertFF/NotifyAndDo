import logging

from aiogram import Dispatcher

from data import config
from data.config import ADMINS
import aiogram.utils.markdown as fmt


async def on_startup_notify(dp: Dispatcher):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, "Бот Запущен")

        except Exception as err:
            logging.exception(err)
