from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🆕 Nuevo aporte",
            callback_data="nuevo_aporte"
        )]
    ])

    mensaje = (
        "💌 <b>Bienvenido a KikuAportes</b>\n\n"
        "Desde aquí puedes enviar fotos, videos, documentos y audios "
        "de forma sencilla.\n\n"
        "Pulsa <b>🆕 Nuevo aporte</b> para comenzar."
    )

    await update.message.reply_text(
        mensaje,
        parse_mode="HTML",
        reply_markup=keyboard
    )