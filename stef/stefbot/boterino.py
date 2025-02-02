import logging
from django.core.management import call_command
from django.conf import settings
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from stefbot.models import ModelProfile
from django.core.exceptions import ObjectDoesNotExist

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot command to start interaction
def start(update: Update, context: CallbackContext):
    """Handle the /start command"""
    update.message.reply_text("Hello! I'm your model bot. Use /models to get a list of models.")

# Bot command to show all models
def models(update: Update, context: CallbackContext):
    """Handle the /models command to show available models"""
    try:
        models = ModelProfile.objects.all()  # Fetch models from the database
        if models:
            message = "Available models:\n"
            for model in models:
                message += f"{model.name}: {model.description} - ${model.price}\n"
            update.message.reply_text(message)
        else:
            update.message.reply_text("No models available.")
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        update.message.reply_text("An error occurred while fetching the models.")

# Bot command to show a specific model by ID
def model_details(update: Update, context: CallbackContext):
    """Handle the /model <id> command to show details for a specific model"""
    try:
        model_id = int(context.args[0])
        model = ModelProfile.objects.get(id=model_id)
        message = f"Model: {model.name}\nDescription: {model.description}\nPrice: ${model.price}\n"
        if model.preview_photo:
            message += f"Preview: {model.preview_photo.url}"
        update.message.reply_text(message)
    except IndexError:
        update.message.reply_text("Please provide a model ID after the command. Example: /model 1")
    except ValueError:
        update.message.reply_text("The model ID must be a number.")
    except ObjectDoesNotExist:
        update.message.reply_text("Model not found.")
    except Exception as e:
        logger.error(f"Error fetching model details: {e}")
        update.message.reply_text("An error occurred while fetching the model details.")

# Main function to start the bot
def main():
    """Start the bot"""
    token = settings.TELEGRAM_TOKEN  # Use the token you got from BotFather
    updater = Updater(token)

    # Register the command handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("models", models))
    dispatcher.add_handler(CommandHandler("model", model_details))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
