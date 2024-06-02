from aiogram.dispatcher.filters.state import State, StatesGroup


class ManageTask(StatesGroup):
    waiting_for_action = State()
    waiting_for_task_selection = State()
    waiting_for_task_number = State()
    waiting_for_field_selection = State()
    waiting_for_date = State()
    waiting_for_new_value = State()
    waiting_for_notification_choice = State()
    waiting_for_specific_notification = State()
    current_page = State()

