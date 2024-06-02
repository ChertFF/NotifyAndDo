from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

class AdminOrPrivateFilter(BoundFilter):
    key = 'is_admin_or_private'

    def __init__(self, is_admin_or_private):
        self.is_admin_or_private = is_admin_or_private

    async def check(self, obj) -> bool:
        if isinstance(obj, types.Message):
            chat = obj.chat
            user_id = obj.from_user.id
        elif isinstance(obj, types.CallbackQuery):
            chat = obj.message.chat
            user_id = obj.from_user.id
        else:
            return False

        if chat.type == 'private':
            return True

        if chat.type in ['group', 'supergroup']:
            member = await chat.get_member(user_id)
            return member.is_chat_admin()

        return False