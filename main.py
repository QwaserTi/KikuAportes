from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN

# handlers
from handlers.start import start
from handlers.buttons import buttons
from handlers.messages import mensajes


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    # ---------------- START ----------------
    app.add_handler(CommandHandler("start", start))

    print("🔥 CallbackQueryHandler REGISTRADO")

    # ---------------- CALLBACKS ----------------
    app.add_handler(
    CallbackQueryHandler(
        buttons,
        pattern="^(nuevo_aporte|skip_comment|enviar_aporte)$"
    )
)

    # ---------------- MENSAJES ----------------
    app.add_handler(
        MessageHandler(
            filters.TEXT |
            filters.PHOTO |
            filters.VIDEO |
            filters.AUDIO |
            filters.Document.ALL,
            mensajes
        )
    )

    print("🤖 KikuAportes 2.0 activo")

    app.run_polling()


if __name__ == "__main__":
    main()