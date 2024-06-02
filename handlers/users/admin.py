import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_calendar import SimpleCalendar, simple_cal_callback as cal_callback
import aiogram.utils.markdown as fmt
import datetime

from data.config import LIMIT_TASK
from loader import dp
from utils.db_api.db_gino import db
from utils.db_api.schemas.user import Task
from states import ManageTask, CloseTask
from filters import AdminOrPrivateFilter
from math import ceil


@dp.message_handler(Command('admin'), state="*")
async def cmd_admin(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="Редактировать задачу", callback_data="edit_task"),
        InlineKeyboardButton(text="Вернуть на доработку", callback_data="return_task"),
        InlineKeyboardButton(text="Дублировать задачу", callback_data="duplicate_task"),
        InlineKeyboardButton(text="Закрыть задачу", callback_data="close_task")
    )
    await message.answer(f"Данная команда предназначена для точечного управления задачами:\n\n"
                         f"📝 {fmt.hbold('Редактировать задачу')} - позволяет в открытых задачах изменять поля \"Название\", \"Описание\", \"Ответственный\", \"Срок решения\", \"Дата напоминания\" \n\n"
                         f"🔍 {fmt.hbold('Вернуть на доработку')} - используется, чтобы изменить статус недавно завершенных задач на уточнение \n\n"
                         f"🔄 {fmt.hbold('Дублировать задачу')} - создаст дубликат из открытых задач с идентичными полями, только с другой датой завершения и датой напоминания \n\n",
                         reply_markup=keyboard)
    await ManageTask.waiting_for_action.set()
    logging.warning(
        f'Отправил сообщение /admin | {message.chat.id} {message.from_user.id} {message.from_user.full_name} {message.from_user.username}  {message.from_user.url}')


@dp.callback_query_handler(state=ManageTask.waiting_for_action)
async def process_action(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    await state.update_data(action=action)
    await state.update_data(page=0)  # Инициализация текущей страницы
    await display_tasks(callback_query, state)



async def display_tasks(callback_query, state):
    data = await state.get_data()
    chat_id = callback_query.message.chat.id
    action = data.get('action')
    page = data.get('page', 0)
    counter_select_pages = data.get('count', 0)
    await state.update_data({'page': page})
    count_tasks = await db.select([db.func.count()]).where(Task.chat_id == chat_id).gino.scalar()

  # Обновляем текущую страницу

    tasks = []

    fields_mapping = {
        "edit_task": "редактировать задачу 📝",
        "duplicate_task": "дублировать задачу 🔄",
        "return_task": "вернуть на уточнение 🔍",
        "close_task": "закрыть задачу 🔍"
    }

    field_name = fields_mapping.get(action)

    if counter_select_pages == 0:
        await callback_query.message.edit_text(f"{fmt.hbold('Ваш выбор:')} {field_name}\n")


    if action == "edit_task":
        tasks = await Task.query.where(Task.status != 'Завершена').where(
            Task.chat_id == callback_query.message.chat.id).order_by(Task.deadline.asc()).offset(
            page * LIMIT_TASK).gino.all()
    elif action == "duplicate_task":
        tasks = await Task.query.where(Task.status != 'Завершена').where(
            Task.chat_id == callback_query.message.chat.id).order_by(Task.deadline.asc()).offset(
            page * LIMIT_TASK).gino.all()
    elif action == "return_task":
        tasks = await Task.query.where(Task.status == 'Завершена').where(
            Task.chat_id == callback_query.message.chat.id).order_by(Task.closed_at.desc()).offset(
            page * LIMIT_TASK).gino.all()
    elif action == "close_task":
        tasks = await Task.query.where(Task.status != 'Завершена').where(
            Task.chat_id == callback_query.message.chat.id).order_by(Task.closed_at.desc()).offset(
            page * LIMIT_TASK).gino.all()

    if not tasks:
        await callback_query.message.answer("Нет задач для редактирования")
        await state.finish()
        return

    # Определяем индексы задач для текущей страницы
    start_index = 0
    nubmer_index = page * LIMIT_TASK
    end_index = LIMIT_TASK
    print(end_index)
    # Получаем задачи для текущей страницы
    tasks_on_page = tasks[start_index:end_index]

    tasks_text = "\n".join([f"№{i + 1 + nubmer_index}. {fmt.hbold(task.name)}\n 📅 {task.deadline}\n 📌 {task.description}\n " for i, task in
                            enumerate(tasks_on_page)])
    tasks_header = f'{fmt.hbold("🔻 Список задач 🔻")}\n\n'

    # Создаем кнопки для выбора задач на текущей странице
    keyboard = InlineKeyboardMarkup(row_width=5)
    for i, task in enumerate(tasks_on_page, start=start_index):
        keyboard.insert(InlineKeyboardButton(text=str(i + 1 + nubmer_index), callback_data=str(task.id)))

    print(len(tasks))
    print(f'длина такса')
    # Добавляем кнопки для переключения страниц
    if page > 0:
        keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="previous_page"))
    if count_tasks > (page + 1) * LIMIT_TASK:
        keyboard.add(InlineKeyboardButton(text="➡️ Далее", callback_data="next_page"))

    if counter_select_pages != 0:
        await callback_query.message.edit_text(f"{tasks_header}{tasks_text}\n{fmt.hbold('Выберите задачу 👇')}", reply_markup=keyboard)
    elif counter_select_pages == 0:
        await callback_query.message.answer(f"{tasks_header}{tasks_text}\n{fmt.hbold('Выберите задачу 👇')}", reply_markup=keyboard)

    if action in ["edit_task", "duplicate_task"]:
        await ManageTask.waiting_for_task_selection.set()
    elif action == "return_task":
        await ManageTask.waiting_for_task_number.set()
    elif action == "close_task":
        await CloseTask.waiting_for_task_number.set()

    logging.warning(
        f'Выбрал пункт {action} в /admin | {callback_query.message.chat.id} {callback_query.from_user.id} '
        f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {action} ')


@dp.callback_query_handler(lambda c: c.data in ["previous_page", "next_page"], state=[ManageTask.waiting_for_task_selection, ManageTask.waiting_for_task_number])
async def change_page(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 0)
    counter_select_pages = data.get('count', 0)

    if callback_query.data == "previous_page":
        page = max(0, page - 1)
    elif callback_query.data == "next_page":
        await state.update_data({'count': counter_select_pages+1})
        page = page + 1

    await state.update_data({'page': page})
    await display_tasks(callback_query, state)


@dp.callback_query_handler(state=ManageTask.waiting_for_task_selection)
async def process_task_selection(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data)
    tasks = await Task.query.where(Task.id == task_id).gino.first()
    print(tasks)

    await callback_query.message.edit_text(
        f"{fmt.hbold('📝 Задача:')} {tasks.name}\n"
        f"{fmt.hbold('📄 Описание задачи:')} {tasks.description}\n"
        f"{fmt.hbold('👤 Ответственный:')} {tasks.responsible}\n"
        f"{fmt.hbold('⏳ Срок решения:')} {tasks.deadline}\n"
        f"{fmt.hbold('🔔 Дата напоминания:')} {tasks.notification_date}\n"
    )

    await state.update_data(task_id=tasks.id)
    action = (await state.get_data()).get('action')
    if action == 'edit_task':
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton(text="Название", callback_data="name"),
            InlineKeyboardButton(text="Описание", callback_data="description"),
            InlineKeyboardButton(text="Ответственный", callback_data="responsible"),
            InlineKeyboardButton(text="Даты завершения и напоминания", callback_data="deadline"),
            InlineKeyboardButton(text="", callback_data="notification_date")
        )
        await callback_query.message.answer("Выберите поле для редактирования:", reply_markup=keyboard)
        await ManageTask.waiting_for_field_selection.set()

    elif action == 'duplicate_task':
        task = tasks
        new_task = await Task.create(
            chat_id=task.chat_id,
            created_by=task.created_by,
            name=task.name,
            description=task.description,
            deadline=task.deadline,  # Мы обновим это поле позже
            responsible=task.responsible,
            notification_date=task.notification_date,  # Мы обновим это поле позже
            status='Новая'
        )
        await state.update_data(new_task_id=new_task.id)
        await callback_query.message.answer(
            f"{fmt.hbold('Выберите новую дату завершения задачи 👇')}\n\n",
            reply_markup=await SimpleCalendar().start_calendar()
        )
        await ManageTask.waiting_for_date.set()


@dp.callback_query_handler(state=ManageTask.waiting_for_task_number)
async def process_task_number(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data)
    task = await Task.query.where(Task.id == task_id).gino.first()

    await task.update(status='На уточнении').apply()
    await callback_query.message.edit_text(f"Задача {task.name} возвращена на доработку 🗿")
    await state.finish()
    logging.warning(
        f'Вернул задачу {task_id} на уточнение  | {callback_query.message.chat.id} {callback_query.from_user.id} '
        f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {task_id} ')


@dp.callback_query_handler(state=ManageTask.waiting_for_field_selection)
async def process_field_selection(callback_query: types.CallbackQuery, state: FSMContext):
    field = callback_query.data
    await state.update_data(field=field)
    user_data = await state.get_data()
    task_id = user_data.get('task_id')
    task = await Task.get(task_id)
    today = datetime.date.today()

    fields_mapping = {
        "name": "название",
        "description": "описание",
        "responsible": "ответственного",
        "deadline": "дату завершения и дату напоминания",
    }

    field_name = fields_mapping.get(callback_query.data)
    if field_name:
        await callback_query.message.edit_text(
            f"{fmt.hbold('Ваш выбор:')} изменить {field_name}")
        logging.warning(
            f'Редактирует поле {field_name} в задаче {task_id} X Ожидается ввод данных | {callback_query.message.chat.id} {callback_query.from_user.id} '
            f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url}')

    if field in ["deadline"]:
        await callback_query.message.answer(
            f"{fmt.hbold('Выберите новую дату завершения задачи👇')}\n\n",
            reply_markup=await SimpleCalendar().start_calendar()
        )
        await ManageTask.waiting_for_date.set()

    else:
        await callback_query.message.answer(f"{fmt.hbold('Введите новое значение 👇')}")
        await ManageTask.waiting_for_new_value.set()


@dp.message_handler(state=ManageTask.waiting_for_new_value, content_types=types.ContentTypes.TEXT)
async def process_new_value(message: types.Message, state: FSMContext):
    new_value = message.text
    user_data = await state.get_data()
    task_id = user_data.get('task_id')
    action = user_data.get('action')
    field = user_data.get('field')

    if action == 'edit_task' and task_id:
        task = await Task.get(task_id)
        update_data = {field: new_value}
        await task.update(**update_data).apply()
        await message.answer(f"Задача {task.name} успешно обновлена ✅")
        await state.finish()

    logging.warning(
        f'Редактирует поле {field} в задаче {task_id} на значение {new_value} X Конец /admin | {message.chat.id} {message.from_user.id} '
        f'{message.from_user.full_name} {message.from_user.username} {message.from_user.url} {task_id} {field} {new_value}')


@dp.callback_query_handler(cal_callback.filter(), state=ManageTask.waiting_for_date)
async def process_date_selection(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)

    if selected:
        date = date.date()
        today = datetime.date.today()

        if date < today:
            await callback_query.message.edit_text(
                f"{fmt.hbold('[1/2] Выбор даты завершения')}\n\n"
                f"{fmt.hbold('Дата завершения задачи не может быть в прошлом! Пожалуйста, выберите дату заново 👇')}",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            logging.warning(
                f'Выбрал дату в прошлом X Ожидается ввод с календаря deadline X Ожидается ввод данных | {callback_query.message.chat.id} {callback_query.from_user.id} '
                f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data}')
            return

        await state.update_data(deadline=date)
        await callback_query.message.edit_text(
            f"{fmt.hbold('[1/2] Выбор даты завершения')}\n\n"
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
            f"{fmt.hbold('[2/2] Выбор даты напоминания')}\n\n"
            f"{fmt.hbold('Выберите дату напоминания 👇')}",
            reply_markup=keyboard
        )
        await ManageTask.waiting_for_notification_choice.set()
        logging.warning(
            f'Выбрал дату успешно X Ожидается ввод с клавиатуры notification | {callback_query.message.chat.id} {callback_query.from_user.id} '
            f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data}')


@dp.callback_query_handler(state=ManageTask.waiting_for_notification_choice)
async def process_notification(callback_query: types.CallbackQuery, state: FSMContext):
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
        await ManageTask.waiting_for_specific_notification.set()

    await callback_query.message.edit_text(
        f"{fmt.hbold('[2/2] Выбор даты напоминания')}\n\n"
        f"{fmt.hbold('Ваш выбор:')} {notification_text}"
    )

    logging.warning(
        f'Выбрал дату успешно X Ожидается ввод с календаря notification | {callback_query.message.chat.id} {callback_query.from_user.id} '
        f'{callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_data}')


@dp.callback_query_handler(cal_callback.filter(), state=ManageTask.waiting_for_specific_notification)
async def process_specific_notification_date(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
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
    task_id = user_data.get('task_id')
    task = await Task.get(task_id)
    deadline = user_data['deadline']
    action = user_data['action']

    fields_mapping = {
        "edit_task": "обновлена",
        "duplicate_task": "продублирована"
    }

    field_name = fields_mapping.get(action)

    await task.update(deadline=user_data['deadline']).apply()
    await task.update(notification_date=notification_date).apply()

    msg = f'Задача успешно {field_name} 🤝'
    await callback_query.message.answer(
        f"{fmt.hbold(msg)}\n\n"
        # f"{fmt.hbold('📝 Название: ')}{user_data['name']}\n"
        # f"{fmt.hbold('📄 Описание: ')}{user_data['description']}\n"
        # f"{fmt.hbold('👤 Ответственный: ')}{user_data['responsible']}\n"
        f"{fmt.hbold('📅 Срок решения: ')}{user_data['deadline']}\n"
        f"{fmt.hbold('🔔 Напоминание: ')}{notification_date}"
    )
    await state.finish()
    logging.warning(
        f'Задача {task_id} успешно {field_name} X Конец /add | {callback_query.message.chat.id} {callback_query.from_user.id} {callback_query.from_user.full_name} {callback_query.from_user.username} {callback_query.from_user.url} {callback_query.data} ')
