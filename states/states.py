# импортируем состояния из библиотеки для создания класса форм
from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    description = State()
    price = State()
    organisation = State()
    contacts = State()
    work_time = State()
    first_photo = State()
    second_photo = State()
    third_photo = State()
    sale = State()
    appeal_time = State()
    buy = State()
    question = State()
