import os
import sys
import django
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
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
    """Get all necessary order details synchronously"""
    try:
        order = Order.objects.select_related('model').get(id=order_id)
        return {
            'id': order.id,
            'model_name': order.model.name,
            'amount': order.amount,
            'created_at': order.created_at,
            'model_id': order.model.id,
            'status': order.status
        }
    except Order.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        return None

@sync_to_async
def get_order_data(order):
    """Synchronously get all order data including photos"""
    try:
        # Get order details
        details = {
            'id': order.id,
            'model_name': order.model.name,
            'amount': order.amount,
            'created_at': order.created_at,
        }
        
        # Get photo paths more efficiently
        photo_paths = []
        photos = order.model.photos.all()[:5]  # Limit to 5 photos per order
        for photo in photos:
            if photo.photo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(photo.photo))
                if os.path.exists(file_path) and os.path.getsize(file_path) < 5_000_000:  # Check file size < 5MB
                    photo_paths.append(file_path)
        
        details['photo_paths'] = photo_paths
        return details
    except Exception as e:
        logger.error(f"Error getting order data: {e}")
        return None
    
from telegram.error import TimedOut   

async def send_message_with_retry(message_func, max_retries=3):
    """Send a message with retry logic"""
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(message_func(), timeout=30)  # 30 second timeout
        except TimedOut:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)  # Wait before retry
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)    

async def create_media_group(photo_paths):
    """Create media group from photo paths"""
    media_group = []
    for path in photo_paths[:10]:  # Limit to 10 photos
        try:
            with open(path, 'rb') as photo_file:
                media_group.append(InputMediaPhoto(media=photo_file.read()))
        except Exception as e:
            logger.error(f"Error reading photo file {path}: {e}")
            continue
    return media_group

from django.conf import settings

@sync_to_async(thread_sensitive=False)
def get_order_photos(model_id):
    """Fetch photo file paths for a model asynchronously"""
    try:
        model = ModelProfile.objects.get(id=model_id)
        photos = model.photos.all()
        photo_paths = []

        for photo in photos:
            if photo.photo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(photo.photo))
                if os.path.exists(file_path):
                    photo_paths.append(file_path)

        return photo_paths
    except Exception as e:
        logger.error(f"Error getting photos for model {model_id}: {e}")
        return []


async def handle_confirm_payment(query: Update, order_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        order_details = await get_order_details(order_id)  # Асинхронно получаем данные заказа

        if not order_details:
            await query.answer("⚠️ Заказ не найден", show_alert=True)
            return
        
        admin_chat_id = ""  # ID администратора
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

        # После подтверждения оплаты отправляем и фото, и видео
        order = await get_order_by_id(order_id)
        if order and order.status == 'paid':
            media_paths = await get_media_paths(order.model.id)
            
            if media_paths['photos'] or media_paths['videos']:
                media_group = []
                
                # Add photos to media group
                for path in media_paths['photos']:
                    file_content = await read_file_sync(path)
                    if file_content:
                        media_group.append(InputMediaPhoto(media=file_content))

                # Add videos to media group
                for path in media_paths['videos']:
                    file_content = await read_file_sync(path)
                    if file_content:
                        media_group.append(InputMediaVideo(media=file_content))

                if media_group:
                    # Send media in chunks of 10 (Telegram's limit)
                    for i in range(0, len(media_group), 10):
                        chunk = media_group[i:i + 10]
                        try:
                            await query.message.reply_media_group(media=chunk)
                            if i + 10 < len(media_group):
                                await asyncio.sleep(1)
                        except Exception as e:
                            logger.error(f"Error sending media group after payment: {e}")
                            continue
            
            # Send confirmation message
            await query.message.reply_text(
                "✅ Оплата подтверждена! Все фото и видео материалы доступны выше."
            )
    
    except Exception as e:
        logger.error(f"Ошибка в handle_confirm_payment: {e}")
        await query.answer(
            "⚠️ Произошла ошибка. Попробуйте позже.",
            show_alert=True
        )
        
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
        elif data == 'orders':  # Show first page by default
            await handle_orders(query, page=0)
        elif data.startswith('orders_page_'):  # Handle pagination
            page = int(data.split('_')[-1])
            await handle_orders(query, page)
        elif data.startswith('order_'):
            order_id = int(data.split('_')[1])
            await handle_order_photos(query, order_id)
        elif data.startswith('confirm_payment_'):
            order_id = int(data.split('_')[-1])  # Extract order ID
            await handle_confirm_payment(query, order_id, context)
    except Exception as e:
        logger.error(f"Ошибка при обработке callback: {e}")
        await query.edit_message_text(
            text="⚠️ Произошла ошибка. Попробуйте позже.",
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

ORDERS_PER_PAGE = 5  # Number of orders per page

ORDERS_PER_PAGE = 5  # Number of orders per page

ORDERS_PER_PAGE = 5  # How many orders to show per page

async def handle_orders(query: Update, page: int = 0):
    try:
        await query.answer()
        user_id = query.from_user.id
        orders = await get_user_orders(user_id)  # Get all paid orders

        if not orders:
            await query.message.reply_text(
                "😔 У вас пока нет оплаченных заказов.",
                reply_markup=main_menu()
            )
            return

        total_orders = len(orders)
        total_pages = max(1, (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE)  # Total pages

        # Ensure page is in valid range
        page = max(0, min(page, total_pages - 1))

        # Get the orders for this page
        start_idx = page * ORDERS_PER_PAGE
        end_idx = start_idx + ORDERS_PER_PAGE
        paginated_orders = orders[start_idx:end_idx]

        # Generate buttons
        buttons = [[InlineKeyboardButton(f"📦 Заказ #{order.id}", callback_data=f"order_{order.id}")] for order in paginated_orders]

        # Pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"orders_page_{page - 1}"))
        if end_idx < total_orders:
            pagination_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"orders_page_{page + 1}"))

        if pagination_buttons:
            buttons.append(pagination_buttons)

        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])

        # Check if we can edit the existing message
        try:
            await query.edit_message_text(
                text=f"📦 Ваши оплаченные заказы ({page + 1}/{total_pages}):",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except:
            await query.message.reply_text(
                text=f"📦 Ваши оплаченные заказы ({page + 1}/{total_pages}):",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    except Exception as e:
        logger.error(f"Error in handle_orders: {e}")
        await query.message.reply_text(
            "⚠️ Ошибка загрузки заказов. Попробуйте позже.",
            reply_markup=main_menu()
        )

@sync_to_async
def get_media_paths(model_id):
    """Get photo and video paths synchronously"""
    from stefbot.models import ModelProfile
    try:
        model = ModelProfile.objects.get(id=model_id)
        media_paths = {
            'photos': [],
            'videos': []
        }
        
        # Get photo paths
        for photo in model.photos.all():
            if photo.photo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(photo.photo))
                if os.path.exists(file_path):
                    media_paths['photos'].append(str(file_path))
                    
        # Get video paths
        for video in model.videos.all():
            if video.video:
                file_path = os.path.join(settings.MEDIA_ROOT, str(video.video))
                if os.path.exists(file_path):
                    media_paths['videos'].append(str(file_path))
                    
        return media_paths
    except Exception as e:
        logger.error(f"Error getting media paths: {e}")
        return {'photos': [], 'videos': []}

@sync_to_async
def get_full_order_data(order_id):
    """Get order and related model data synchronously"""
    from stefbot.models import Order
    try:
        order = Order.objects.select_related('model').get(id=order_id)
        return {
            'model_id': order.model.id,
            'exists': True
        }
    except Order.DoesNotExist:
        return {'exists': False}
    except Exception as e:
        logger.error(f"Error getting order data: {e}")
        return {'exists': False}

@sync_to_async
def get_photo_paths(model_id):
    """Get photo paths synchronously"""
    from stefbot.models import ModelProfile
    try:
        model = ModelProfile.objects.get(id=model_id)
        paths = []
        for photo in model.photos.all():
            if photo.photo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(photo.photo))
                if os.path.exists(file_path):
                    paths.append(str(file_path))
        return paths
    except Exception as e:
        logger.error(f"Error getting photo paths: {e}")
        return []

@sync_to_async
def read_file_sync(path):
    """Read file synchronously"""
    try:
        with open(path, 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return None      

@sync_to_async(thread_sensitive=False)
def get_order_photos(model_id):
    """Fetch photo file paths for a model asynchronously"""
    try:
        model = ModelProfile.objects.get(id=model_id)  # ✅ Fetch model safely
        photos = model.photos.all()  # ✅ Get all related photos

        photo_paths = []
        for photo in photos:
            if photo.photo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(photo.photo))
                if os.path.exists(file_path):
                    photo_paths.append(file_path)

        return photo_paths
    except Exception as e:
        logger.error(f"Error getting photos for model {model_id}: {e}")
        return []

import pathlib

@sync_to_async
def fetch_order_photos(model_id):
    """Asynchronously fetch photo paths for a model"""
    from stefbot.models import ModelProfile
    try:
        model = ModelProfile.objects.get(id=model_id)
        photos = model.photos.all()
        photo_paths = []

        for photo in photos:
            if photo.photo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(photo.photo))
                if os.path.exists(file_path):
                    logger.info(f"✅ Found file: {file_path}")
                    photo_paths.append(str(file_path))
                else:
                    logger.warning(f"❌ Missing file: {file_path}")

        return photo_paths
    except Exception as e:
        logger.error(f"Error fetching photos for model {model_id}: {e}")
        return []

async def read_photo_file(path):
    """Asynchronously read photo file"""
    try:
        path_obj = pathlib.Path(path)
        if path_obj.exists() and path_obj.is_file():
            # Use asyncio.to_thread for Python 3.9+ or run_in_executor for older versions
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: open(str(path_obj), 'rb').read())
    except Exception as e:
        logger.error(f"Error reading photo file {path}: {e}")
        return None

async def handle_order_photos(query, order_id):
    """Handle order photos and videos viewing"""
    try:
        # Get order data
        order_data = await get_full_order_data(order_id)
        
        if not order_data['exists']:
            await query.answer("⚠️ Заказ не найден", show_alert=True)
            return

        # Get media paths
        media_paths = await get_media_paths(order_data['model_id'])
        
        if not media_paths['photos'] and not media_paths['videos']:
            await query.answer("⚠️ Медиафайлы не найдены", show_alert=True)
            return

        # Process photos
        media_group = []
        
        # Add photos to media group
        for path in media_paths['photos']:
            file_content = await read_file_sync(path)
            if file_content:
                media_group.append(InputMediaPhoto(media=file_content))

        # Add videos to media group
        for path in media_paths['videos']:
            file_content = await read_file_sync(path)
            if file_content:
                media_group.append(InputMediaVideo(media=file_content))

        if not media_group:
            await query.answer("⚠️ Не удалось загрузить медиафайлы", show_alert=True)
            return

        # Send media in chunks of 10 (Telegram's limit)
        for i in range(0, len(media_group), 10):
            chunk = media_group[i:i + 10]
            try:
                await query.message.reply_media_group(media=chunk)
                # Add small delay between chunks if needed
                if i + 10 < len(media_group):
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error sending media group: {e}")
                continue

        await query.answer("✅ Медиафайлы загружены")

    except Exception as e:
        logger.error(f"Error in handle_order_photos for order {order_id}: {e}")
        await query.answer("⚠️ Произошла ошибка при загрузке медиафайлов", show_alert=True)


# Запуск бота
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.run_polling()
