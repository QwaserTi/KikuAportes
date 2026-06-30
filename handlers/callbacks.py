from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.aporte_manager import manager


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # =====================================================
    # 🆕 NUEVO APORTE
    # =====================================================
    if query.data == "nuevo_aporte":

        manager.iniciar_aporte(user_id)

        await query.message.edit_text(
            "📝 Escribe un comentario para tu aporte:"
        )

        return

    # =====================================================
    # 📤 ENVIAR APORTE
    # =====================================================
    if query.data == "enviar_aporte":

        aporte = manager.get_active(user_id)

        if not aporte:
            await query.message.reply_text("No hay aporte activo.")
            return

        await query.message.reply_text("📤 Aporte enviado correctamente (placeholder)")