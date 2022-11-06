# импорт типов и состояний из библиотеки aiogram
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BotBlocked, BadRequest

import asyncio

# импорт модулей бота
from states import Form
from loader import dp, bot
from messages import MESSAGES
from conf import CHANNEL
from keyboards import make_a_post_keyboard, cancel_photo_keyboard, confirm_post_keyboard, photo_keyboard, \
    choose_a_post_keyboard


# обрабатываем команды /start /help
@dp.message_handler(commands=['start', 'help'])
async def start_message(message: types.Message):
    await dp.bot.send_message(
        message.chat.id,
        MESSAGES['start'].format(message.from_user.username),
        reply_markup=make_a_post_keyboard
    )
    # добавляем айди пользователя в user_id
    with open('data/users_id.txt', 'r+') as file:
        if not str(message.chat.id) in file.read().split('\n'):
            file.seek(0, 2)
            file.write(str(message.chat.id) + '\n')


# обрабатываем команду /cancel и завершаем любое начатое пользователем действие
@dp.message_handler(commands=['cancel'], state='*')
async def make_a_post_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    elif current_state in ['Form:title', 'Form:description', 'Form:photo']:
        await state.finish()
        await bot.send_message(message.from_user.id, MESSAGES['canceled'], reply_markup=make_a_post_keyboard)
    else:
        await state.finish()
        await bot.send_message(message.from_user.id, MESSAGES['canceled'])


# принимаем первое фото для поста
@dp.message_handler(state=Form.first_photo, content_types=['photo'])
async def set_post_photo_1(message: types.Message, state: FSMContext):
    # проверяем, чтобы в сообщении было только одно фото
    if message.media_group_id:
        return
    async with state.proxy() as data:
        data['photo'] = [message.photo[-1].file_id]
    await bot.send_message(
        message.from_user.id,
        MESSAGES['next_photo'],
        reply_markup=photo_keyboard
    )
    await Form.second_photo.set()


# принимаем второе фото для поста
@dp.message_handler(state=Form.second_photo, content_types='photo')
async def set_post_photo_2(message: types.Message, state: FSMContext):
    # проверяем, чтобы в сообщении было только одно фото
    if message.media_group_id:
        return
    async with state.proxy() as data:
        data['photo'].append(message.photo[-1].file_id)
    await bot.send_message(
        message.from_user.id,
        MESSAGES['next_photo'],
        reply_markup=photo_keyboard
    )
    await Form.third_photo.set()


# принимаем третье фото для поста и представляем пользователю итоговый результат его поста
@dp.message_handler(state=Form.third_photo, content_types='photo')
async def set_post_photo_3(message: types.Message, state: FSMContext):
    # проверяем, чтобы в сообщении было только одно фото
    if message.media_group_id:
        return
    async with state.proxy() as data:
        data['photo'].append(message.photo[-1].file_id)
        photos_ids = data['photo']
        msg = data['message']
    photos = [types.InputMediaPhoto(photo) for photo in photos_ids]
    photos[0].caption = msg
    await bot.send_media_group(message.from_user.id, photos)
    await bot.send_message(message.from_user.id, MESSAGES['confirm_post'], reply_markup=confirm_post_keyboard)


# принимаем описание для поста и филтруем его в зависимости от категории поста
@dp.message_handler(state=Form.description)
async def set_post_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) > 200:
            await bot.send_message(message.from_user.id, MESSAGES['too_long_message'])
            return
        data['message'] = data['message'].replace('description', message.text)
        await Form.first_photo.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_photo'], reply_markup=cancel_photo_keyboard)


# узнаем часы работы организации для рекламы
@dp.message_handler(state=Form.work_time)
async def set_work_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('work_time', message.text)
    await Form.description.set()
    await bot.send_message(message.from_user.id, MESSAGES['ad_description'])


# узнаем название организации
@dp.message_handler(state=Form.organisation)
async def set_post_organisation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('organisation', message.text)
    await Form.contacts.set()
    await bot.send_message(message.from_user.id, MESSAGES['set_contact'])


# узнаем контакты для поста и добавляем к описанию
@dp.message_handler(state=Form.contacts)
async def set_post_contact(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('contact', message.text)
    # если пост относится к продажам, то просим юзера прислать фото товара
    if '#продажа' in data['message'] or '#покупка' in data['message']:
        await Form.appeal_time.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_appeal_time'])
        return
    elif '#реклама' in data['message']:
        await Form.work_time.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_work_time'])
        return
    elif '#вопрос' in data['message']:
        await Form.description.set()
        await bot.send_message(message.from_user.id, MESSAGES['question_description'])


# добавляем цену товара
@dp.message_handler(state=Form.price)
async def set_post_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('price', message.text)
    await Form.contacts.set()
    await bot.send_message(message.from_user.id, MESSAGES['set_contact'])


@dp.message_handler(state=Form.sale)
async def set_sale(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('sale', message.text)
    await Form.price.set()
    await bot.send_message(message.from_user.id, MESSAGES['set_price'])


@dp.message_handler(state=Form.buy)
async def set_buy(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('buy', message.text)
    await Form.price.set()
    await bot.send_message(message.from_user.id, MESSAGES['set_price'])


@dp.message_handler(state=Form.appeal_time)
async def set_appeal_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('appeal', message.text)
    await Form.description.set()
    if '#покупка' in data['message']:
        await bot.send_message(message.from_user.id, MESSAGES['purchase_description'])
    elif '#реклама' in data['message']:
        await bot.send_message(message.from_user.id, MESSAGES['ad_description'])
    elif '#продажа' in data['message']:
        await bot.send_message(message.from_user.id, MESSAGES['sale_description'])


@dp.message_handler(state=Form.question)
async def set_question(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = data['message'].replace('question', message.text)
    await Form.contacts.set()
    await bot.send_message(message.from_user.id, MESSAGES['set_contact'])


@dp.message_handler(content_types=['new_chat_members', 'left_chat_member'])
async def del_welcome_message(message: types.Message):
    await bot.delete_message(message.chat.id, message.message_id)


async def delete_message(message: types.Message, time: int):
    await asyncio.sleep(time)
    await bot.delete_message(message.chat.id, message.message_id)


# отлавливаем нажатие на кнопку с соответствующе категорией поста и формируем под него сообщение
@dp.message_handler()
async def make_a_post_command(message: types.Message, state: FSMContext):
    if message.chat.id != CHANNEL:
        its_not_chat = True
    else:
        its_not_chat = False

    if message.text in ['/post', '📢 Создать пост'] and its_not_chat:
        await bot.send_message(message.from_user.id, MESSAGES['choose_a_post'], reply_markup=choose_a_post_keyboard)
    elif message.text == 'Продажа 💲' and its_not_chat:
        async with state.proxy() as data:
            data['message'] = '<b>🧳 sale</b>\n\n' \
                              '<b>💰Цена:</b> price\n' \
                              '<b>📱Контакты:</b> contact\n' \
                              '<b>🕖Время обращения:</b> appeal\n\n' \
                              '<b>📄Описание:</b> description\n\n#продажа'
        await Form.sale.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_sale'])
    elif message.text == 'Покупка 🛒' and its_not_chat:
        async with state.proxy() as data:
            data['message'] = '<b>🧳 buy</b>\n\n' \
                              '<b>💰Цена:</b> price\n' \
                              '<b>📱Контакты:</b> contact\n' \
                              '<b>🕖Время обращения:</b> appeal\n\n' \
                              '<b>📄Описание:</b> description\n\n#покупка'
            data['photo'] = None
        await Form.buy.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_buy'])
    elif message.text == 'Реклама 📺' and its_not_chat:
        async with state.proxy() as data:
            data['message'] = '<b>🏫 organisation</b>\n\n' \
                              '<b>📱Контакты:</b> contact\n' \
                              '<b>🕖Время обращения:</b> work_time\n\n' \
                              '<b>📄Описание:</b> description\n\n#реклама'
            data['photo'] = None
        await Form.organisation.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_organisation'])
    elif message.text == 'Вопрос ❓' and its_not_chat:
        async with state.proxy() as data:
            data['message'] = '<b>❓question</b>\n' \
                              '<b>📱Контакты:</b> contact\n\n' \
                              '<b>📄Описание:</b> description\n\n#вопрос'
            data['photo'] = None
        await Form.question.set()
        await bot.send_message(message.from_user.id, MESSAGES['set_question'])
    else:
        try:
            admins = await bot.get_chat_administrators(message.chat.id)
            admins_ids = [i.user.id for i in admins]
        except BadRequest:
            admins_ids = [message.from_user.id]
        if message.from_user.id not in admins_ids:
            await bot.delete_message(message.chat.id, message.message_id)
            try:
                await bot.send_message(message.from_user.id, MESSAGES['del_message'], reply_markup=make_a_post_keyboard)
            except BotBlocked:
                print('Бот не смог отправить сообщение, так как был заблокирован пользователем.')
            except Exception as e:
                print(e)
            msg = await bot.send_message(message.chat.id, MESSAGES['auto_delete_message'])
            await delete_message(msg, 7)  # здесь вторым аргументом (после msg) передается время удаления сообщения
