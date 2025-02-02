import logging
import asyncio
import os
from django.conf import settings
from telegram import Bot, InputMediaPhoto

logger = logging.getLogger(__name__)


TOKEN = ""
bot = Bot(token=TOKEN)

def get_absolute_url(relative_path):
    """Генерирует абсолютный URL изображения."""
    return f"{settings.MEDIA_URL}{relative_path.lstrip('/')}"

async def send_telegram_message(chat_id, text):
    """Асинхронная отправка текстового сообщения в Telegram."""
    try:
        logger.info(f"📩 Отправка сообщения в Telegram пользователю {chat_id}")
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"✅ Сообщение успешно отправлено пользователю {chat_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")

async def send_telegram_photos(chat_id, photo_paths):
    """Отправляет фотографии из локальных файлов Django."""
    try:
        if not photo_paths:
            logger.warning(f"⚠️ Нет фотографий для отправки пользователю {chat_id}")
            return

        media = []
        for path in photo_paths[:10]:  # Ограничиваем до 10 фото
            
            # ✅ Убираем дублирующийся `media/`
            relative_path = path.replace(settings.MEDIA_URL, "").lstrip("/")
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)  

            # 📌 **Добавляем логирование пути к файлу**
            logger.info(f"🔍 Проверяем файл: {absolute_path}")

            if os.path.exists(absolute_path):
                with open(absolute_path, 'rb') as photo:
                    media.append(InputMediaPhoto(photo))  # 📌 **Используем файл напрямую**
                    logger.info(f"✅ Файл найден и загружен: {absolute_path}")
            else:
                logger.warning(f"❌ Файл не найден: {absolute_path}")

        if media:
            await bot.send_media_group(chat_id=chat_id, media=media)
            logger.info(f"✅ Фото успешно отправлены пользователю {chat_id}")
        else:
            logger.warning(f"❌ Не удалось загрузить фотографии для {chat_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка отправки фото: {e}")
