import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import aiosqlite

# Токен бота
API_TOKEN = ''

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация базы данных
async def init_db():
    async with aiosqlite.connect('bot_database.db') as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                full_name TEXT,
                phone TEXT,        
                additional_phone TEXT,  
                email TEXT,
                address TEXT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                subcategory TEXT,
                description TEXT,
                file_ids TEXT,
                status TEXT DEFAULT 'В ожидании',
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')
        await conn.commit()

# Состояния для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_additional_phone = State()  # Новое состояние для дополнительного номера
    waiting_for_email = State()
    waiting_for_address = State()

# для создания заявки
class RequestStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_description = State()
    waiting_for_files = State()

# Основная клавиатура с кнопками
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Зарегистрироваться"))
    builder.add(types.KeyboardButton(text="Создать заявку"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Клавиатура для выбора категории
def get_categories_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Компьютер/ноутбук"))
    builder.add(types.KeyboardButton(text="Программное обеспечение"))
    builder.add(types.KeyboardButton(text="Периферийные устройства"))
    builder.add(types.KeyboardButton(text="Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Клавиатура для выбора подкатегории
def get_subcategories_keyboard(category: str):
    builder = ReplyKeyboardBuilder()
    if category == "Компьютер/ноутбук":
        builder.add(types.KeyboardButton(text="Не включается"))
        builder.add(types.KeyboardButton(text="Медленно работает"))
        builder.add(types.KeyboardButton(text="Зависает"))
    elif category == "Программное обеспечение":
        builder.add(types.KeyboardButton(text="Помощь с установкой программ"))
        builder.add(types.KeyboardButton(text="Проверить/почистить от вирусов"))
        builder.add(types.KeyboardButton(text="Не запускается/вылетает программа"))
        builder.add(types.KeyboardButton(text="Установка/переустановка ОС"))
    elif category == "Периферийные устройства":
        builder.add(types.KeyboardButton(text="Подключить/настроить принтер"))
        builder.add(types.KeyboardButton(text="Клавиатура/мышь не работает"))
        builder.add(types.KeyboardButton(text="Проблема с монитором"))
    builder.add(types.KeyboardButton(text="Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Клавиатура с кнопкой "Назад"
def get_back_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Назад"))
    builder.add(types.KeyboardButton(text="Готово"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для помощи участникам СВО и их семьям. Выберите действие:",
        reply_markup=get_main_keyboard()
    )

# Обработчик текстового сообщения "Зарегистрироваться"
@dp.message(lambda message: message.text == "Зарегистрироваться")
async def cmd_register(message: Message, state: FSMContext):
    async with aiosqlite.connect('bot_database.db') as conn:
        cursor = await conn.execute('SELECT * FROM users WHERE user_id = ?', (message.from_user.id,))
        user = await cursor.fetchone()

    if user:
        await message.answer("Вы уже зарегистрированы!", reply_markup=get_main_keyboard())
    else:
        await message.answer("Введите ваше ФИО:", reply_markup=get_back_keyboard())
        await state.set_state(RegistrationStates.waiting_for_full_name)

# Обработчик текстового сообщения "Назад"
@dp.message(lambda message: message.text == "Назад")
async def cmd_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Вы в главном меню.", reply_markup=get_main_keyboard())
        return

    await state.clear()
    await message.answer("Возврат в главное меню.", reply_markup=get_main_keyboard())

# Обработчик текстового сообщения "Готово"
@dp.message(lambda message: message.text == "Готово")
async def cmd_done(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Заявка создана! Мы свяжемся с вами в ближайшее время.", reply_markup=get_main_keyboard())
        return

    user_data = await state.get_data()
    category = user_data.get('category')
    subcategory = user_data.get('subcategory')
    description = user_data.get('description')
    file_ids = user_data.get('file_ids', "")

    if not category or not subcategory or not description:
        await message.answer("Пожалуйста, заполните все данные перед завершением.")
        return

    async with aiosqlite.connect('bot_database.db') as conn:
        try:
            await conn.execute('''
                INSERT INTO requests (user_id, category, subcategory, description, file_ids)
                VALUES (?, ?, ?, ?, ?)
            ''', (message.from_user.id, category, subcategory, description, file_ids))
            await conn.commit()
            await message.answer("Заявка создана! Мы свяжемся с вами в ближайшее время.", reply_markup=get_main_keyboard())
        except Exception as e:
            logging.error(f"Ошибка при сохранении заявки: {e}")
            await message.answer("Произошла ошибка при создании заявки. Пожалуйста, попробуйте снова.")

    await state.clear()

# Обработчик ввода ФИО
@dp.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    if message.text == "Назад":
        await cmd_back(message, state)
        return

    await state.update_data(full_name=message.text)
    await message.answer("Введите ваш номер телефона:", reply_markup=get_back_keyboard())
    await state.set_state(RegistrationStates.waiting_for_phone)

# Обработчик ввода телефона
@dp.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.text == "Назад":
        await cmd_back(message, state)
        return

    await state.update_data(phone=message.text)
    await message.answer("Введите ваш дополнительный номер телефона (если есть):", reply_markup=get_back_keyboard())
    await state.set_state(RegistrationStates.waiting_for_additional_phone)

# Обработчик ввода дополнительного телефона
@dp.message(RegistrationStates.waiting_for_additional_phone)
async def process_additional_phone(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(RegistrationStates.waiting_for_phone)
        await message.answer("Введите ваш номер телефона:", reply_markup=get_back_keyboard())
        return

    await state.update_data(additional_phone=message.text)
    await message.answer("Введите ваш email:", reply_markup=get_back_keyboard())
    await state.set_state(RegistrationStates.waiting_for_email)

# Обработчик ввода email
@dp.message(RegistrationStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(RegistrationStates.waiting_for_additional_phone)
        await message.answer("Введите ваш дополнительный номер телефона (если есть):", reply_markup=get_back_keyboard())
        return

    await state.update_data(email=message.text)
    await message.answer("Введите ваш адрес проживания:", reply_markup=get_back_keyboard())
    await state.set_state(RegistrationStates.waiting_for_address)

# Обработчик ввода адреса
@dp.message(RegistrationStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(RegistrationStates.waiting_for_email)
        await message.answer("Введите ваш email:", reply_markup=get_back_keyboard())
        return

    user_data = await state.get_data()
    full_name = user_data['full_name']
    phone = user_data['phone']
    additional_phone = user_data.get('additional_phone', "")  # Дополнительный номер телефона
    email = user_data['email']
    address = message.text

    async with aiosqlite.connect('bot_database.db') as conn:
        try:
            await conn.execute('''
                INSERT INTO users (user_id, full_name, phone, additional_phone, email, address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message.from_user.id, full_name, phone, additional_phone, email, address))
            await conn.commit()
            await message.answer("Регистрация завершена! Спасибо.", reply_markup=get_main_keyboard())
        except aiosqlite.IntegrityError:
            await message.answer("Вы уже зарегистрированы!", reply_markup=get_main_keyboard())

    await state.clear()

# Обработчик текстового сообщения "Создать заявку"
@dp.message(lambda message: message.text == "Создать заявку")
async def cmd_create_request(message: Message, state: FSMContext):
    await message.answer("Выберите категорию проблемы:", reply_markup=get_categories_keyboard())
    await state.set_state(RequestStates.waiting_for_category)

# Обработчик выбора категории
@dp.message(RequestStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    if message.text == "Назад":
        await cmd_back(message, state)
        return

    if message.text in ["Компьютер/ноутбук", "Программное обеспечение", "Периферийные устройства"]:
        await state.update_data(category=message.text)
        await message.answer("Выберите подкатегорию:", reply_markup=get_subcategories_keyboard(message.text))
        await state.set_state(RequestStates.waiting_for_subcategory)
    else:
        await message.answer("Пожалуйста, выберите категорию из списка.")

# Обработчик выбора подкатегории
@dp.message(RequestStates.waiting_for_subcategory)
async def process_subcategory(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(RequestStates.waiting_for_category)
        await message.answer("Выберите категорию проблемы:", reply_markup=get_categories_keyboard())
        return

    user_data = await state.get_data()
    category = user_data['category']
    subcategories = {
        "Компьютер/ноутбук": ["Не включается", "Медленно работает", "Зависает"],
        "Программное обеспечение": ["Помощь с установкой программ", "Проверить/почистить от вирусов", "Не запускается/вылетает программа", "Установка/переустановка ОС"],
        "Периферийные устройства": ["Подключить/настроить принтер", "Клавиатура/мышь не работает", "Проблема с монитором"]
    }

    if message.text in subcategories[category]:
        await state.update_data(subcategory=message.text)
        await message.answer("Опишите проблему:", reply_markup=get_back_keyboard())
        await state.set_state(RequestStates.waiting_for_description)
    else:
        await message.answer("Пожалуйста, выберите подкатегорию из списка.")

# Обработчик ввода описания
@dp.message(RequestStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(RequestStates.waiting_for_subcategory)
        await message.answer("Выберите подкатегорию:", reply_markup=get_subcategories_keyboard((await state.get_data())['category']))
        return

    await state.update_data(description=message.text)
    await message.answer("При необходимости прикрепите файлы или фотографии. Когда закончите, нажмите 'Готово'.", reply_markup=get_back_keyboard())
    await state.set_state(RequestStates.waiting_for_files)

# Обработчик для прикрепления файлов и фотографий
@dp.message(RequestStates.waiting_for_files)
async def process_files(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(RequestStates.waiting_for_description)
        await message.answer("Опишите проблему:", reply_markup=get_back_keyboard())
        return

    if message.text == "Готово":
        await cmd_done(message, state)
        return

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        await message.answer("Пожалуйста, прикрепите файл или фотографию.")
        return

    user_data = await state.get_data()
    file_ids = user_data.get('file_ids', "")
    file_ids = file_ids + "," + file_id if file_ids else file_id
    await state.update_data(file_ids=file_ids)

    await message.answer("Файл прикреплен. Вы можете прикрепить ещё файлы или нажмите 'Готово'.")

# Запуск бота
async def main():
    await init_db()  # Инициализация базы данных при запуске
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())