from aiogram import Dispatcher

from loader import dp
from .throttling import ThrottlingMiddleware
from .new_users import UpdateChatUsersMiddleware


if __name__ == "middlewares":
    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(UpdateChatUsersMiddleware())
