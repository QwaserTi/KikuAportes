import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, validate_config
from handlers.buttons import buttons
from handlers.messages import mensajes
from handlers.start import start


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Error no controlado procesando una actualización", exc_info=context.error)


MEDIA_FILTER = filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document.ALL
PRIVATE_MESSAGES = filters.ChatType.PRIVATE & (filters.TEXT | MEDIA_FILTER)


def main():
    validate_config()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        CallbackQueryHandler(
            buttons,
            pattern="^(nuevo_aporte|skip_comment|enviar_aporte)$",
        )
    )
    app.add_handler(MessageHandler(PRIVATE_MESSAGES & ~filters.COMMAND, mensajes))
    app.add_error_handler(error_handler)

    logger.info("KikuAportes activo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
