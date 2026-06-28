from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import config


# MENÚ PRINCIPAL
MENU = ReplyKeyboardMarkup(
    [["🆕 Nuevo aporte"], ["📖 Instrucciones"]],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *KikuAportes*\n\nBienvenido.\n\nAquí puedes enviar fotos, videos, audios y GIFs (solo contenido casero).\n\n👇 Elige una opción:",
        parse_mode="Markdown",
        reply_markup=MENU
    )


def main():
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("KikuAportes está corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()