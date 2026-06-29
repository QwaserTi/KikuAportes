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

    # ---------------- HANDLERS ----------------
    app.add_handler(CommandHandler("start", start))

    print("🔥 CallbackQueryHandler REGISTRADO")
    app.add_handler(CallbackQueryHandler(buttons))

    app.add_handler(MessageHandler(filters.ALL, mensajes))

    print("🤖 KikuAportes v1.0 activo")

    app.run_polling()


if __name__ == "__main__":
    main()