import asyncio
import datetime
import logging
from loader import bot
import aioschedule
import aiogram.utils.markdown as fmt
from utils.db_api.schemas.user import Task


async def send_reminder():
    # Получаем все задачи
    today = datetime.date.today()
    tasks = await Task.query.where((Task.status != 'Завершена') & (Task.notification_date == today)).order_by(
        Task.deadline.asc()).gino.all()

    print(tasks)

    for task in tasks:
        try:
            Send = (f"{fmt.hbold('🔸 Напоминаю о задаче 🔸')}\n\n"
                    f"{fmt.hbold('📝 Название: ')}{task.name}\n"
                    f"{fmt.hbold('📌 Описание: ')}{task.description}\n"
                    f"{fmt.hbold('👤 Ответственный: ')}{task.responsible}\n\n"
                    f"{fmt.hbold('📅 Срок решения: ')}{task.deadline}\n"
                    f"{fmt.hbold('🔔 Напоминание: ')}{task.notification_date}")
            await bot.send_message(task.chat_id, Send)
            logging.warning(
                f'Напоминание о задаче {task.id} было отправлено в чат {task.chat_id}')
            await asyncio.sleep(0.27)
        except:
            logging.warning(
                f'Напоминание о задаче {task.id} было НЕ БЫЛО отправлено в чат {task.chat_id}')
            await asyncio.sleep(0.27)

    tasks_after_deadline = await Task.query.where((Task.status != 'Завершена') & (Task.deadline < today)).order_by(
        Task.deadline.asc()).gino.all()

    for task in tasks_after_deadline:
        try:
            Send = (f"{fmt.hbold('🔻 Задача просрочена 🔻')}\n\n"
                    f"{fmt.hbold('📝 Название: ')}{task.name}\n"
                    f"{fmt.hbold('📌 Описание: ')}{task.description}\n"
                    f"{fmt.hbold('👤 Ответственный: ')}{task.responsible}\n\n"
                    f"{fmt.hbold('📅 Срок решения: ')}{task.deadline}\n")
            await bot.send_message(task.chat_id, Send)
            logging.warning(
                f'Напоминание о просроченной задаче {task.id} было отправлено в чат {task.chat_id}')
            await asyncio.sleep(0.27)
        except:
            logging.warning(
                f'Напоминание о просроченной задаче {task.id} было НЕ БЫЛО отправлено в чат {task.chat_id}')
            await asyncio.sleep(0.27)


async def scheduler_tasks():
    aioschedule.every().day.at("00:05").do(send_reminder)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(5)