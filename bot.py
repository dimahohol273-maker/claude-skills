import asyncio
import logging
import os
import random
from typing import Dict, List

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для FSM
class GiftStates(StatesGroup):
    selecting_gift = State()
    upgrading_gift = State()

# Временное хранилище данных пользователей (в продакшене использовать БД)
user_gifts: Dict[int, List[Dict]] = {}
user_balance: Dict[int, int] = {}  # Баланс звёзд пользователей

# Данные о доступных подарках
AVAILABLE_GIFTS = [
    {"id": 1, "name": "Delicious Cake", "emoji": "🎂", "level": 1, "price": 100},
    {"id": 2, "name": "Green Star", "emoji": "⭐", "level": 1, "price": 150},
    {"id": 3, "name": "Blue Star", "emoji": "💠", "level": 1, "price": 200},
    {"id": 4, "name": "Red Heart", "emoji": "❤️", "level": 1, "price": 250},
    {"id": 5, "name": "Tropical Fish", "emoji": "🐠", "level": 1, "price": 300},
]

def get_main_keyboard():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Мой баланс", callback_data="show_balance"),
        InlineKeyboardButton("🎁 Доступные подарки", callback_data="show_gifts"),
        InlineKeyboardButton("🎒 Мой инвентарь", callback_data="show_inventory"),
        InlineKeyboardButton("⬆️ Апгрейд подарка", callback_data="upgrade_menu"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )
    return keyboard

def get_gifts_keyboard():
    """Клавиатура с доступными подарками"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for gift in AVAILABLE_GIFTS:
        keyboard.add(InlineKeyboardButton(
            f"{gift['emoji']} {gift['name']} - {gift['price']} ⭐",
            callback_data=f"buy_{gift['id']}"
        ))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
    return keyboard

def get_inventory_keyboard(user_id: int):
    """Клавиатура с инвентарем пользователя"""
    gifts = user_gifts.get(user_id, [])
    keyboard = InlineKeyboardMarkup(row_width=1)

    if gifts:
        for idx, gift in enumerate(gifts):
            keyboard.add(InlineKeyboardButton(
                f"{gift['emoji']} {gift['name']} (Lvl {gift['level']})",
                callback_data=f"view_gift_{idx}"
            ))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
    return keyboard

def get_upgrade_keyboard(user_id: int):
    """Клавиатура для апгрейда"""
    gifts = user_gifts.get(user_id, [])
    keyboard = InlineKeyboardMarkup(row_width=1)

    if gifts:
        for idx, gift in enumerate(gifts):
            keyboard.add(InlineKeyboardButton(
                f"{gift['emoji']} {gift['name']} (Lvl {gift['level']})",
                callback_data=f"select_gift_{idx}"
            ))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
    return keyboard

def get_chance_keyboard(gift_idx: int, gift_level: int):
    """Клавиатура выбора шанса апгрейда"""
    chances = [10, 20, 30, 50, 75]

    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []

    for chance in chances:
        buttons.append(InlineKeyboardButton(
            f"{chance}% шанс",
            callback_data=f"upgrade_{gift_idx}_{chance}"
        ))

    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.row(buttons[i], buttons[i + 1])
        else:
            keyboard.add(buttons[i])

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="upgrade_menu"))
    return keyboard

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    if user_id not in user_gifts:
        user_gifts[user_id] = []
    if user_id not in user_balance:
        user_balance[user_id] = 100  # Начальный баланс 100 звёзд

    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🎁 Добро пожаловать в бот управления Telegram подарками!\n\n"
        f"💰 Ваш баланс: {user_balance[user_id]} ⭐\n\n"
        "Здесь вы можете:\n"
        "• Покупать подарки\n"
        "• Улучшать их уровень (с шансом провала!)\n"
        "• Управлять своей коллекцией\n\n"
        "Выберите действие:"
    )

    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 <b>Помощь по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/gifts - Доступные подарки\n"
        "/inventory - Ваш инвентарь\n"
        "/upgrade - Апгрейд подарка\n"
        "/help - Эта справка\n\n"
        "<b>Как использовать:</b>\n"
        "1. Купите подарки из списка доступных\n"
        "2. Улучшайте их уровень за звезды ⭐\n"
        "3. Собирайте коллекцию редких подарков\n\n"
        "Чем выше уровень подарка, тем он ценнее!"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.message_handler(commands=['gifts'])
async def cmd_gifts(message: types.Message):
    """Обработчик команды /gifts"""
    text = "🎁 <b>Доступные подарки:</b>\n\nВыберите подарок для покупки:"
    await message.answer(text, parse_mode="HTML", reply_markup=get_gifts_keyboard())

@dp.message_handler(commands=['inventory'])
async def cmd_inventory(message: types.Message):
    """Обработчик команды /inventory"""
    user_id = message.from_user.id
    gifts = user_gifts.get(user_id, [])

    if not gifts:
        text = "🎒 Ваш инвентарь пуст.\n\nКупите подарки с помощью /gifts"
    else:
        text = f"🎒 <b>Ваш инвентарь:</b>\n\nВсего подарков: {len(gifts)}"

    await message.answer(text, parse_mode="HTML", reply_markup=get_inventory_keyboard(user_id))

@dp.message_handler(commands=['upgrade'])
async def cmd_upgrade(message: types.Message):
    """Обработчик команды /upgrade"""
    user_id = message.from_user.id
    gifts = user_gifts.get(user_id, [])

    if not gifts:
        text = "⬆️ У вас нет подарков для апгрейда.\n\nСначала купите подарки с помощью /gifts"
    else:
        text = "⬆️ <b>Апгрейд подарка</b>\n\nВыберите подарок для улучшения:"

    await message.answer(text, parse_mode="HTML", reply_markup=get_upgrade_keyboard(user_id))

@dp.callback_query_handler(lambda c: c.data == "show_balance")
async def show_balance(callback_query: types.CallbackQuery):
    """Показать баланс"""
    user_id = callback_query.from_user.id
    if user_id not in user_balance:
        user_balance[user_id] = 100

    balance = user_balance[user_id]
    gifts_count = len(user_gifts.get(user_id, []))

    text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"⭐ Звёзд: <b>{balance}</b>\n"
        f"🎁 Подарков: {gifts_count}\n\n"
        f"Используйте звёзды для покупки и улучшения подарков!"
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback_query: types.CallbackQuery):
    """Возврат в главное меню"""
    text = "🏠 Главное меню\n\nВыберите действие:"
    await callback_query.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "show_gifts")
async def show_gifts(callback_query: types.CallbackQuery):
    """Показать доступные подарки"""
    text = "🎁 <b>Доступные подарки:</b>\n\nВыберите подарок для покупки:"
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=get_gifts_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "show_inventory")
async def show_inventory(callback_query: types.CallbackQuery):
    """Показать инвентарь"""
    user_id = callback_query.from_user.id
    gifts = user_gifts.get(user_id, [])

    if not gifts:
        text = "🎒 Ваш инвентарь пуст.\n\nКупите подарки!"
    else:
        text = f"🎒 <b>Ваш инвентарь:</b>\n\nВсего подарков: {len(gifts)}"

    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=get_inventory_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "upgrade_menu")
async def upgrade_menu(callback_query: types.CallbackQuery):
    """Меню апгрейда"""
    user_id = callback_query.from_user.id
    gifts = user_gifts.get(user_id, [])

    if not gifts:
        text = "⬆️ У вас нет подарков для апгрейда.\n\nСначала купите подарки!"
    else:
        text = "⬆️ <b>Апгрейд подарка</b>\n\nВыберите подарок для улучшения:"

    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=get_upgrade_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "show_help")
async def show_help(callback_query: types.CallbackQuery):
    """Показать помощь"""
    help_text = (
        "📖 <b>Помощь по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/gifts - Доступные подарки\n"
        "/inventory - Ваш инвентарь\n"
        "/upgrade - Апгрейд подарка\n"
        "/help - Эта справка\n\n"
        "<b>Как использовать:</b>\n"
        "1. Купите подарки из списка доступных\n"
        "2. Улучшайте их уровень за звезды ⭐\n"
        "3. Собирайте коллекцию редких подарков\n\n"
        "Чем выше уровень подарка, тем он ценнее!"
    )
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
    await callback_query.message.edit_text(help_text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("buy_"))
async def buy_gift(callback_query: types.CallbackQuery):
    """Покупка подарка"""
    gift_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    # Инициализация баланса если нет
    if user_id not in user_balance:
        user_balance[user_id] = 100

    # Найти подарок
    gift = next((g for g in AVAILABLE_GIFTS if g['id'] == gift_id), None)
    if not gift:
        await callback_query.answer("❌ Подарок не найден!", show_alert=True)
        return

    # Проверка баланса
    if user_balance[user_id] < gift['price']:
        await callback_query.answer(
            f"❌ Недостаточно звёзд! Нужно: {gift['price']} ⭐, у вас: {user_balance[user_id]} ⭐",
            show_alert=True
        )
        return

    # Списать звёзды
    user_balance[user_id] -= gift['price']

    # Добавить подарок в инвентарь
    if user_id not in user_gifts:
        user_gifts[user_id] = []

    new_gift = gift.copy()
    user_gifts[user_id].append(new_gift)

    text = (
        f"✅ Подарок куплен!\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"Уровень: {gift['level']}\n"
        f"Потрачено: {gift['price']} ⭐\n\n"
        f"💰 Остаток звёзд: <b>{user_balance[user_id]}</b> ⭐\n\n"
        f"Подарок добавлен в ваш инвентарь!"
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎒 Мой инвентарь", callback_data="show_inventory"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")
    )

    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer("🎉 Покупка успешна!")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("select_gift_"))
async def select_gift_for_upgrade(callback_query: types.CallbackQuery):
    """Выбор подарка и шанса для апгрейда"""
    idx = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id

    if user_id not in user_gifts or idx >= len(user_gifts[user_id]):
        await callback_query.answer("❌ Подарок не найден!", show_alert=True)
        return

    gift = user_gifts[user_id][idx]

    text = (
        f"⬆️ <b>Апгрейд подарка</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"Текущий уровень: {gift['level']}\n"
        f"Следующий уровень: {gift['level'] + 1}\n\n"
        f"💰 Ваш баланс: {user_balance.get(user_id, 100)} ⭐\n\n"
        f"🎲 Выберите шанс успеха:\n"
        f"• 10% - низкий шанс\n"
        f"• 20% - небольшой шанс\n"
        f"• 30% - средний шанс\n"
        f"• 50% - хороший шанс\n"
        f"• 75% - высокий шанс\n\n"
        f"⚠️ Апгрейд <b>бесплатный</b>, но при провале уровень не изменится!"
    )

    await callback_query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_chance_keyboard(idx, gift['level'])
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("upgrade_") and len(c.data.split("_")) == 3)
async def upgrade_gift(callback_query: types.CallbackQuery):
    """Апгрейд подарка с выбранным шансом (бесплатно)"""
    parts = callback_query.data.split("_")
    idx = int(parts[1])
    chance = int(parts[2])
    user_id = callback_query.from_user.id

    # Инициализация баланса если нет
    if user_id not in user_balance:
        user_balance[user_id] = 100

    if user_id not in user_gifts or idx >= len(user_gifts[user_id]):
        await callback_query.answer("❌ Подарок не найден!", show_alert=True)
        return

    gift = user_gifts[user_id][idx]

    # Проверка успеха (без списания звёзд)
    is_success = random.randint(1, 100) <= chance

    if is_success:
        # Успешный апгрейд
        old_level = gift['level']
        gift['level'] += 1

        text = (
            f"✅ <b>АПГРЕЙД УСПЕШЕН!</b>\n\n"
            f"{gift['emoji']} <b>{gift['name']}</b>\n"
            f"Уровень: {old_level} → <b>{gift['level']}</b>\n\n"
            f"🎲 Выбранный шанс: {chance}%\n"
            f"💵 Ваш баланс: <b>{user_balance[user_id]}</b> ⭐\n\n"
            f"🎉 Поздравляем с улучшением!"
        )
        alert_text = "✨ Успех! Уровень повышен!"
    else:
        # Провал апгрейда
        text = (
            f"❌ <b>АПГРЕЙД ПРОВАЛИЛСЯ!</b>\n\n"
            f"{gift['emoji']} <b>{gift['name']}</b>\n"
            f"Уровень остался: <b>{gift['level']}</b>\n\n"
            f"🎲 Выбранный шанс: {chance}%\n"
            f"💵 Ваш баланс: <b>{user_balance[user_id]}</b> ⭐\n\n"
            f"😢 Не повезло! Попробуйте ещё раз!"
        )
        alert_text = "💔 Не повезло!"

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"select_gift_{idx}"),
        InlineKeyboardButton("⬆️ Выбрать другой подарок", callback_data="upgrade_menu"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data="show_inventory"),
        InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")
    )

    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer(alert_text, show_alert=True)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("view_gift_"))
async def view_gift(callback_query: types.CallbackQuery):
    """Просмотр подарка"""
    idx = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id

    if user_id not in user_gifts or idx >= len(user_gifts[user_id]):
        await callback_query.answer("❌ Подарок не найден!", show_alert=True)
        return

    gift = user_gifts[user_id][idx]
    upgrade_cost = gift['level'] * 50

    text = (
        f"🎁 <b>Информация о подарке</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n\n"
        f"📊 Уровень: {gift['level']}\n"
        f"💰 Стоимость апгрейда: {upgrade_cost} ⭐\n"
        f"🆔 Позиция в инвентаре: #{idx + 1}"
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("⬆️ Улучшить", callback_data=f"upgrade_{idx}"),
        InlineKeyboardButton("◀️ Назад к инвентарю", callback_data="show_inventory")
    )

    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback_query.answer()

if __name__ == "__main__":
    logger.info("Бот запускается...")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)
