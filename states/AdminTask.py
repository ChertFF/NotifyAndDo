from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminTask(StatesGroup):
    choose_action = State()
    waiting_for_task_number = State()
    waiting_for_new_value = State()