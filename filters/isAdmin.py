from aiogram.dispatcher.filters import BoundFilter
from aiogram import types
from data.config import ADMINS


class IsAdmin(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        return str(message.from_user.id) in ADMINS