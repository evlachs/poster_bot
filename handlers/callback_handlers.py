# импорт типов и состояний из библиотеки aiogram
from aiogram import types
from aiogram.dispatcher import FSMContext

# импорт модулей бота
from loader import dp, bot
from states import Form
from messages import MESSAGES
from conf import CHANNEL
from keyboards import confirm_post_keyboard, make_a_post_keyboard, photo_keyboard


# ловим нажатие на кнопку отмены фото под постом и обрабатываем децствие
@dp.callback_query_handler(lambda c: c.data == 'cancel_photo', state=Form.first_photo)
async def cancel_photo(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['photo'] = None
        msg = data['message']
    await bot.send_message(callback_query.from_user.id, MESSAGES['confirm_post'])
    await bot.send_message(callback_query.from_user.id, msg, reply_markup=confirm_post_keyboard)


# отмена любого начатого действия через команду /cancel
@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    current_state = await state.get_state()
    if current_state is None:
        return
    elif current_state in ['Form:title', 'Form:description', 'Form:photo']:
        await state.finish()
        await bot.send_message(callback_query.from_user.id, MESSAGES['canceled'], reply_markup=make_a_post_keyboard)
    else:
        await state.finish()
        await bot.send_message(callback_query.from_user.id, MESSAGES['canceled'])


# если пользователь добавил в пост менее трех фотографий, то завершаем процесс добавления по нажатию на кнопку
@dp.callback_query_handler(lambda c: c.data == 'finish_photo', state=[Form.second_photo, Form.third_photo])
async def finish_photo_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        photos_ids = data['photo']
        msg = data['message']
    if len(photos_ids) > 1:
        photos = [types.InputMediaPhoto(photo) for photo in photos_ids]
        photos[0].caption = msg
        await bot.send_media_group(callback_query.from_user.id, photos)
    else:
        await bot.send_photo(callback_query.from_user.id, photos_ids[0], msg)
    await bot.send_message(callback_query.from_user.id, MESSAGES['confirm_post'], reply_markup=confirm_post_keyboard)


# принимаем кнопку отправить пост и публикуем его в группу
@dp.callback_query_handler(lambda c: c.data == 'confirm_post', state='*')
async def confirm_post(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    async with state.proxy() as data:
        photos_ids = data['photo']
        msg = data['message']
    # прежде чем отправить, проверяем пост на "плохие слова"
    with open('data/bad_words.txt', 'r', encoding='utf-8') as file:
        bad_words = file.read().split(', ')
    for bw in bad_words:
        # если плохое слово обнаружено - отменяем публикацию и просим юзера создать пост заново
        if bw in msg.lower():
            await bot.send_message(callback_query.from_user.id, MESSAGES['bad_words'])
            await state.finish()
            return
    if photos_ids and len(photos_ids) > 1:
        photos = [types.InputMediaPhoto(photo) for photo in photos_ids]
        photos[0].caption = msg
        await bot.send_media_group(CHANNEL, photos)
    elif photos_ids and len(photos_ids) == 1:
        await bot.send_photo(CHANNEL, photos_ids[0], msg)
    else:
        await bot.send_message(CHANNEL, msg)
    await bot.send_message(callback_query.from_user.id, MESSAGES['post_confirmed'])
    await state.finish()
