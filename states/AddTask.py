from aiogram.dispatcher.filters.state import State, StatesGroup

class AddTask(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_responsible = State()
    waiting_for_deadline = State()
    waiting_for_notification = State()
    waiting_for_specific_notification = State()