from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Order, ModelPhoto
import asyncio
import threading
import logging
import os
from telegram import InputMediaPhoto
from .utils import send_telegram_message, bot  # Используем `bot` для отправки сообщений напрямую

logger = logging.getLogger(__name__)

# Глобальный event loop для фоновых задач
loop = asyncio.new_event_loop()
threading.Thread(target=loop.run_forever, daemon=True).start()

def get_local_photo_path(photo):
    """Возвращает полный путь к файлу изображения."""
    if not photo:
        return None
    return os.path.join(settings.MEDIA_ROOT, str(photo))  # Абсолютный путь к файлу

async def send_order_confirmation(telegram_id, message, photo_paths):
    """Асинхронно отправляет сообщение и фото (все сразу одним сообщением)."""
    try:
        await send_telegram_message(telegram_id, message)

        media_group = []
        for photo_path in photo_paths:
            if os.path.exists(photo_path):  # Проверяем, существует ли файл
                with open(photo_path, "rb") as photo_file:
                    media_group.append(InputMediaPhoto(media=photo_file.read()))
            else:
                logger.warning(f"❌ Файл {photo_path} не найден!")

        if media_group:
            await bot.send_media_group(chat_id=telegram_id, media=media_group)
        else:
            logger.warning("❌ Нет доступных фото для отправки.")
    
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")

@receiver(post_save, sender=Order)
def notify_user_on_payment(sender, instance, created, **kwargs):
    """Отправляет пользователю подтверждение оплаты и фото заказа."""
    if instance.status == 'paid' and not created:
        telegram_user = instance.user
        message = f"✅ Ваш заказ {instance.id} был оплачен успешно! Получите фото ниже:"

        logger.info(f"📩 Отправка уведомления пользователю {telegram_user.telegram_id}")

        # Получаем фото модели и их локальные пути
        photos = ModelPhoto.objects.filter(model=instance.model)
        photo_paths = [get_local_photo_path(photo.photo.name) for photo in photos if photo.photo]

        if not photo_paths:
            logger.warning(f"❌ Нет доступных фото для заказа {instance.id}")

        # Запускаем задачу в фоновом event loop
        asyncio.run_coroutine_threadsafe(
            send_order_confirmation(telegram_user.telegram_id, message, photo_paths), loop
        )
