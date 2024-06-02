import logging

from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart

from loader import dp
import aiogram.utils.markdown as fmt

@dp.message_handler(CommandStart(), state="*")
async def bot_start(message: types.Message):
    await message.answer(f"Привет, {message.from_user.full_name} 💬\n"
                         f"Я создан для того, чтобы помочь не забыть о срочных и горящих задачах 🔥\n\n"
                         f"{fmt.hbold('Расскажу о командах, которые во мне заложены:') }\n"
                         f"/add - {fmt.hbold('добавит новую задачу')}, потребуется указать Название, ввести подробное Описание, выбрать Ответственного и поставить срок\n\n"
                         f"/list - выведет {fmt.hbold('5 последних задач')} по трем разным категориям: Новые, На уточнении, Закрытые; подсветит соблюдение сроков и экспортирует все записи в {fmt.hbold('.xlsx-файл')}\n\n"
                         f"/admin - позволяет точечно {fmt.hbold('управлять задачами')}: редактировать, дублировать, возвращать на доработку и закрывать\n\n"
                         f"С основными возможностями ознакомил, надеюсь, что смогу помочь не пропускать сроки 🤝\n\n"
                         f"{fmt.hspoiler('“Время не любит, когда его тратят впустую“ - Генри Форд 👀')}")
    logging.warning(
        f'Отправил сообщение /start | {message.chat.id} {message.from_user.id} {message.from_user.full_name} {message.from_user.username}  {message.from_user.url}')

