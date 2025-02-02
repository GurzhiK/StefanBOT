import os
import sys
import django
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from asgiref.sync import sync_to_async

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stef.settings')
django.setup()

from stefbot.models import TelegramUser, ModelProfile, Order

# Токен бота
TOKEN = ""
DEFAULT_PHOTO_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-vVoi9lNzf3WaVV2cAHQSFcBqQtZu4pPWaw&s"

# Функции работы с БД
@sync_to_async
def get_or_create_user(telegram_id, username):
    return TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={'username': username}
    )

@sync_to_async
def get_all_models():
    return list(ModelProfile.objects.all())

@sync_to_async
def get_model_by_id(model_id):
    return ModelProfile.objects.filter(id=model_id).first()

@sync_to_async
def get_model_photos(model_id):
    model = ModelProfile.objects.filter(id=model_id).first()
    return list(model.photos.all()) if model else []

@sync_to_async
def get_user_orders(telegram_id):
    return list(Order.objects.filter(user__telegram_id=telegram_id, status='paid'))

@sync_to_async
def create_order(user, model, amount):
    """Создает новый заказ и сохраняет его в базе данных."""
    return Order.objects.create(
        user=user,
        model=model,
        amount=amount,
        status='pending'
    )

@sync_to_async
def get_order_by_id(order_id):
    return Order.objects.filter(id=order_id).first()

# Главное меню
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Модели", callback_data='models')],
        [InlineKeyboardButton("👤 Профиль", callback_data='profile')],
        [InlineKeyboardButton("🔧 Тех. поддержка", url='https://t.me/tech_support_bot')],
        [InlineKeyboardButton("📦 Заказы", callback_data='orders')]
    ])

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, _ = await get_or_create_user(update.effective_user.id, update.effective_user.username)
    await update.message.reply_photo(
        photo=DEFAULT_PHOTO_URL,
        caption="Добро пожаловать в агентство знакомств 🔞",
        reply_markup=main_menu()
    )

@sync_to_async
def get_order_details(order_id):
    """Асинхронно получает детали заказа (модель и сумму)"""
    order = Order.objects.filter(id=order_id).select_related('model').first()
    if order:
        return {
            "id": order.id,
            "model_name": order.model.name,
            "amount": order.amount
        }
    return None

async def handle_confirm_payment(query: Update, order_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        order_details = await get_order_details(order_id)  # Асинхронно получаем данные заказа

        if not order_details:
            await query.answer("⚠️ Заказ не найден", show_alert=True)
            return
        
        admin_chat_id = ""  # Укажите реальный chat_id администратора
        user = query.from_user
        admin_message = (
            f"🆕 Новый платеж!\n"
            f"Пользователь: @{user.username} (ID: {user.id})\n"
            f"Заказ ID: {order_details['id']}\n"
            f"Модель: {order_details['model_name']}\n"
            f"Сумма: {order_details['amount']} RUB\n"
            "Пожалуйста, проверьте платеж и обновите статус заказа в админ-панели."
        )
        
        # Отправляем сообщение админу
        await context.bot.send_message(chat_id=admin_chat_id, text=admin_message)
        
        # Уведомляем пользователя
        await query.answer(
            "✅ Администратор уведомлен. После проверки ваш заказ будет подтвержден.",
            show_alert=True
        )
    
    except Exception as e:
        logger.error(f"Ошибка в handle_confirm_payment: {e}")
        await query.answer(
            "⚠️ Произошла ошибка. Попробуйте позже.",
            show_alert=True
        )
        
# Обработчик callback-кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == 'models':
            await handle_models_list(query)
        elif data.startswith('model_'):
            model_id = int(data.split('_')[1])
            await handle_model_details(query, model_id)
        elif data == 'back_to_main':
            await handle_back_to_main(query)
        elif data.startswith('buy_'):
            model_id = int(data.split('_')[1])
            await handle_purchase(query, model_id, context)
        elif data == 'orders':
            await handle_orders(query)
        elif data.startswith('confirm_payment_'):
            order_id = int(data.split('_')[2])
            await handle_confirm_payment(query, order_id, context)
    except Exception as e:
        logger.error(f"Ошибка при обработке callback: {e}")
        await query.edit_message_caption(
            caption="⚠️ Произошла ошибка. Попробуйте позже.",
            reply_markup=main_menu()
        )

async def handle_models_list(query):
    models = await get_all_models()

    if not models:
        await query.edit_message_caption(
            caption="😔 Модели не найдены",
            reply_markup=main_menu()
        )
        return

    buttons = [[InlineKeyboardButton(m.name, callback_data=f'model_{m.id}')] for m in models]
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])

    await query.edit_message_media(
        media=InputMediaPhoto(media=DEFAULT_PHOTO_URL, caption="Выберите модель:"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_model_details(query, model_id):
    model = await get_model_by_id(model_id)

    if not model:
        await query.edit_message_caption(
            caption="⚠️ Модель не найдена",
            reply_markup=main_menu()
        )
        return

    buttons = [
        [InlineKeyboardButton("🛒 Купить", callback_data=f'buy_{model.id}')],
        [InlineKeyboardButton("◀️ Назад", callback_data='models')]
    ]

    try:
        with open(model.preview_photo.path, 'rb') as photo_file:
            await query.message.reply_photo(
                photo=photo_file,
                caption=f"🔥 {model.name}\n\n{model.description}\n\n💵 Цена: {model.price} RUB",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except FileNotFoundError:
        await query.edit_message_caption(
            caption="⚠️ Фото модели недоступно",
            reply_markup=main_menu()
        )

async def handle_back_to_main(query):
    await query.edit_message_media(
        media=InputMediaPhoto(media=DEFAULT_PHOTO_URL, caption="Главное меню"),
        reply_markup=main_menu()
    )

async def handle_purchase(query, model_id, context):
    model = await get_model_by_id(model_id)
    if model:
        user, _ = await get_or_create_user(query.from_user.id, query.from_user.username)
        order = await create_order(user, model, model.price)
        
        message = (
            f"✅ Вы выбрали: {model.name}\n\n"
            f"💵 **Цена**: {model.price} RUB\n\n"
            "Переведите сумму на один из следующих реквизитов:\n\n"
            "💰 **СБП**: +79991234567\n"
            "💳 **Карта**: 4276 1234 5678 9012\n\n"
            "После перевода нажмите кнопку '✅ Оплатил'."
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Оплатил", callback_data=f'confirm_payment_{order.id}')],
            [InlineKeyboardButton("◀️ Назад", callback_data=f'model_{model.id}')],
        ]
        
        await query.edit_message_caption(
            caption=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_caption(
            caption="⚠️ Модель не найдена",
            reply_markup=main_menu()
        )

async def handle_orders(query):
    user_id = query.from_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        await query.edit_message_caption(
            caption="😔 У вас пока нет оплаченных заказов.",
            reply_markup=main_menu()
        )
        return
    
    for order in orders:
        photos = await get_model_photos(order.model.id)
        if photos:
            media_group = [InputMediaPhoto(media=photo.photo.url) for photo in photos]
            await query.message.reply_media_group(media=media_group)
        await query.message.reply_text(
            f"✅ Ваш заказ на {order.model.name} подтверждён!",
            reply_markup=main_menu()
        )

# Запуск бота
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.run_polling()
