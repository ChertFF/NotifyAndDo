from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from utils.db_api.schemas.user import User
from utils.db_api.db_gino import db


class UpdateChatUsersMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username
        fullname = message.from_user.full_name
        url = message.from_user.url

        # Проверяем, есть ли пользователь в базе данных
        user = await User.query.where(User.user_id == user_id).where(User.chat_id == chat_id).gino.first()

        # Если пользователя нет в базе данных, добавляем его
        if not user:
            await User.create(chat_id=chat_id, user_id=user_id, t_username=username, t_fullname=fullname, t_url=url)
        else:
            # Если пользователь есть в базе данных, проверяем, нужно ли обновить данные
            if user.t_username != username or user.t_fullname != fullname or user.t_url != url:
                # Обновляем данные
                await user.update(t_username=username, t_fullname=fullname, t_url=url).apply()

