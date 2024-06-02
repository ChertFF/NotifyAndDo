import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp
from utils.db_api.schemas.user import Task
from states import AddTask
from aiogram_calendar import SimpleCalendar, simple_cal_callback as cal_callback
import aiogram.utils.markdown as fmt
from loader import db
import datetime


@dp.message_handler(Command('add'), state="*")
async def cmd_add(message: types.Message):
    await message.answer(f"{fmt.hbold('[1/5] Добавление новой задачи')}\n\n"
                         f"Рекомендуется дать короткое название задаче (2-3 слова).\n"
                         f"Описать подробно суть можно будет на следующем шаге.\n\n"
                         f"{fmt.hbold('Введите название задачи 👇')}")
    await AddTask.waiting_for_name.set()
    logging.warning(
        f'Отправил сообщение /add X Ожидается ввод с клавиатуры name | {message.chat.id} {message.from_user.id} {message.from_user.full_name} {message.from_user.username} {message.from_user.url} {message.text}')



@dp.message_handler(state=AddTask.waiting_for_name, content_types=types.ContentTypes.TEXT)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"{fmt.hbold('[2/5] Добавление новой задачи')}\n\n"
                         f"{fmt.hbold('Введите подробное описание задачи 👇')}")
    await AddTask.next()
    logging.warning(
        f'Отправил сообщение X Ожидается ввод с клавиатуры description | {message.chat.id} {message.from_user.id} {message.from_user.full_name} {message.from_user.username} {message.from_user.url} {message.text}')


@dp.message_handler(state=AddTask.waiting_for_description, content_types=types.ContentTypes.TEXT)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(f"{fmt.hbold('[3/5] Добавление новой задачи')}\n\n"
                         f"{fmt.hbold('Введите ответственного 👇')}")
    await AddTask.next()
    logging.warning(
        f'Отправил сообщение X Ожидается ввод с клавиатуры responsible | {message.chat.id} {message.from_user.id} {message.from_user.full_name} {message.from_user.username} {message.from_user.url} {message.text}')


@dp.message_handler(state=AddTask.waiting_for_responsible, content_types=types.ContentTypes.TEXT)
async def process_responsible(message: types.Message, state: FSMContext):
    await state.update_data(responsible=message.text)
    await message.answer(f"{fmt.hbold('[4/5] Добавление новой задачи')}\n\n"
                         f"{fmt.hbold('Выберите дату завершения задачи 👇')}",
                         reply_markup=await SimpleCalendar().start_calendar())
    await AddTask.next()
    logging.warning(
        f'Отправил сообщение X Ожидается ввод с календаря deadline | {message.chat.id} {message.from_user.id} {message.from_user.full_name} {message.from_user.username} {message.from_user.url} {message.text}')


@dp.callback_query_handler(cal_callback.filter(), state=AddTask.waiting_for_deadline)
async def process_deadline(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)

    if selected:
        date = date.date()
        today = datetime.date.today()

        if date < today:
            await callback_query.message.edit_text(
                f"{fmt.hbold('[4/5] Добавление новой задачи')}\n\n"
                f"{fmt.hbold('Дата завершения задачи не может быть в прошлом! Пожалуйста, выберите дату заново 👇')}",
                reply_markup=await SimpleCalendar().start_calendar())
            logging.warning(
                f'Выбрал дату в прошлом X Ожидается ввод с календаря deadline | {callback_query.message.chat.id} {callback_query.from_user.id} {callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data} ')
            return

        await state.update_data(deadline=date)
        await callback_query.message.edit_text(
            f"{fmt.hbold('[4/5] Добавление новой задачи')}\n\n"
            f"{fmt.hbold('Ваш выбор:')} {date}"
        )

        # Определяем доступные варианты напоминаний в зависимости от срока задачи
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("День в день", callback_data="notify_same_day"))

        delta_days = (date - today).days
        if delta_days >= 3:
            keyboard.add(InlineKeyboardButton("За 3 дня", callback_data="notify_3_days"))
        if delta_days >= 7:
            keyboard.add(InlineKeyboardButton("За неделю", callback_data="notify_week"))
        keyboard.add(InlineKeyboardButton("В определенную дату", callback_data="notify_specific_date"))

        await callback_query.message.answer(
            f"{fmt.hbold('[5/5] Добавление новой задачи')}\n\n"
            f"{fmt.hbold('Выберите дату напоминания 👇')}",
            reply_markup=keyboard
        )
        await AddTask.next()
        logging.warning(
            f'Выбрал дату успешно X Ожидается ввод с клавиатуры notification | {callback_query.message.chat.id} {callback_query.from_user.id} {callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data} ')


@dp.callback_query_handler(state=AddTask.waiting_for_notification)
async def process_notification(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    deadline = user_data['deadline']
    notification_date = None
    notification_text = ""

    if callback_query.data == "notify_same_day":
        notification_date = deadline
        notification_text = "день в день"
        await save_task_and_finish(callback_query, state, notification_date)

    elif callback_query.data == "notify_3_days":
        notification_date = deadline - datetime.timedelta(days=3)
        notification_text = "за 3 дня"
        await save_task_and_finish(callback_query, state, notification_date)

    elif callback_query.data == "notify_week":
        notification_date = deadline - datetime.timedelta(days=7)
        notification_text = "за неделю"
        await save_task_and_finish(callback_query, state, notification_date)

    elif callback_query.data == "notify_specific_date":
        await callback_query.message.answer(f"{fmt.hbold('Выберите дату напоминания 👇')}",
                                            reply_markup=await SimpleCalendar().start_calendar())
        notification_text = "в определенную дату"
        await AddTask.waiting_for_specific_notification.set()

    await callback_query.message.edit_text(
        f"{fmt.hbold('[5/5] Добавление новой задачи')}\n\n"
        f"{fmt.hbold('Ваш выбор:')} {notification_text}"
    )
    logging.warning(
        f'Выбрал дату успешно X Ожидается ввод с календаря notification | {callback_query.message.chat.id} {callback_query.from_user.id} {callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_query.data} ')



@dp.callback_query_handler(cal_callback.filter(), state=AddTask.waiting_for_specific_notification)
async def process_specific_notification_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    today = datetime.date.today()

    if selected:
        date = date.date()  # Приведение к типу date
        if date < today:
            await callback_query.message.edit_text(
                f"{fmt.hbold('Дата напоминания не может быть в прошлом! Пожалуйста, выберите дату заново 👇')}",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            logging.warning(
                f'Выбрал дату напоминания в прошлом X Ожидается ввод с календаря notification | {callback_query.message.chat.id} {callback_query.from_user.id} '
                f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data} ')
            return
        user_data = await state.get_data()
        deadline = user_data['deadline']
        if date > deadline:
            await callback_query.message.edit_text(
                f"{fmt.hbold('Дата напоминания не может быть позже даты завершения задачи! Пожалуйста, выберите дату заново 👇')}",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            logging.warning(
                f'Выбрал дату напоминания позже дедлайна X Ожидается ввод с календаря notification | {callback_query.message.chat.id} {callback_query.from_user.id} '
                f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data} ')
            return
        await save_task_and_finish(callback_query, state, date)


async def save_task_and_finish(callback_query, state, notification_date):
    user_data = await state.get_data()
    task = await Task.create(
        chat_id=callback_query.message.chat.id,
        created_by=callback_query.from_user.id,
        name=user_data['name'],
        description=user_data['description'],
        deadline=user_data['deadline'],
        responsible=user_data['responsible'],
        notification_date=notification_date
    )

    await callback_query.message.answer(
        f"{fmt.hbold('Задача добавлена 🤝')}\n\n"
        f"{fmt.hbold('📝 Название: ')}{user_data['name']}\n"
        f"{fmt.hbold('📌 Описание: ')}{user_data['description']}\n"
        f"{fmt.hbold('👤 Ответственный: ')}{user_data['responsible']}\n\n"
        f"{fmt.hbold('📅 Срок решения: ')}{user_data['deadline']}\n"
        f"{fmt.hbold('🔔 Напоминание: ')}{notification_date}"
    )
    await state.finish()

    logging.warning(
        f'Создал задачу X Конец /add | {callback_query.message.chat.id} {callback_query.from_user.id} {callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_query.data} ')
    return
