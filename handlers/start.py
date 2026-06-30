from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.aporte_manager import manager


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Nuevo aporte", callback_data="nuevo_aporte")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "💌 Bienvenido a KikuAportes 💌\n\nPulsa para iniciar un aporte:",
        reply_markup=menu()
    )