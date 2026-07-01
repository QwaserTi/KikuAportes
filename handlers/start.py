from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


def menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🆕 Nuevo aporte", callback_data="nuevo_aporte")]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "💌 Bienvenido a KikuAportes 💌\n\nPulsa para iniciar un aporte:",
        reply_markup=menu(),
    )
