from aiogram.dispatcher.filters.state import State, StatesGroup

class CloseTask(StatesGroup):
    waiting_for_task_number = State()
    waiting_for_closing_details = State()