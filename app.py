import asyncio

from aiogram import executor

from data import config
from loader import dp
import middlewares, filters, handlers
from utils.misc.scheduler_task import scheduler_tasks
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from loader import db
from utils.db_api.db_gino import on_startup as on_start_gino


async def on_startup(dispatcher):
    # Устанавливаем дефолтные команды
    await set_default_commands(dispatcher)

    await on_start_gino(dp)

    # print('Удаление таблиц')
    # await db.gino.drop_all()
    # print('Создание таблиц')
    # await db.gino.create_all()

    # Уведомляет про запуск
    await on_startup_notify(dispatcher)

    asyncio.create_task(scheduler_tasks())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)

