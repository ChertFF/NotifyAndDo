import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp
from utils.db_api.schemas.user import Task
from states import CloseTask
from loader import db
import aiogram.utils.markdown as fmt


@dp.callback_query_handler(state=CloseTask.waiting_for_task_number)
async def process_task_number(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data)
    tasks = await Task.query.where(Task.id == task_id).gino.first()

    await callback_query.message.edit_text(
        f"{fmt.hbold('📝 Ваш выбор:')} {tasks.name}\n"
        f"{fmt.hbold('📄 Описание задачи:')} {tasks.description}\n"
        f"{fmt.hbold('👤 Ответственный:')} {tasks.responsible}\n"
        f"{fmt.hbold('⏳ Срок решения:')} {tasks.deadline}\n"
    )

    await state.update_data(task_id=tasks.id)
    await callback_query.message.answer(f"{fmt.hbold('Введите детали выполнения (более 10 символов) 👇')}")
    logging.warning(
        f'Закрывает задачу {task_id} X Ожидается ввод данных | {callback_query.message.chat.id} {callback_query.from_user.id} '
        f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {task_id} ')
    await CloseTask.next()


@dp.message_handler(state=CloseTask.waiting_for_closing_details, content_types=types.ContentTypes.TEXT)
async def process_closing_details(message: types.Message, state: FSMContext):
    details = message.text

    if len(details) <= 10:
        await message.answer("Описание слишком короткое, попробуйте снова ❌")
        return

    user_data = await state.get_data()
    task = await Task.get(user_data['task_id'])
    await task.update(status='Завершена', closed_at=db.func.now(), closed_by=message.from_user.id, decision_by_close= details).apply()

    await message.answer(f"Задача {task.name} была завершена ✅")
    await state.finish()
    logging.warning(
        f'Задача была закрыта X Конец /admin | {message.chat.id} {message.from_user.id} '
        f'{message.from_user.full_name} {message.from_user.username} {message.from_user.url} {details}')