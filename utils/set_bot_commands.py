from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("add", "Добавить задачу"),
            types.BotCommand("admin", "Управление"),
            types.BotCommand("list", "Список задач"),
        ]
    )
