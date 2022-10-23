from aiogram import executor

from loader import dp
from utils import set_default_commands
import handlers


async def on_startup(dispatcher):
    # Устанавливаем дефолтные команды
    await set_default_commands(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
