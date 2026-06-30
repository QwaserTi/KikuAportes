from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo
)
from telegram.ext import ContextTypes

from config import GROUP_ID, FRIEND_ID
from services.aporte_service import service

import logging

logger = logging.getLogger(__name__)


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    logger.info(f"Botón pulsado: {data}")

    # ---------------- NUEVO APORTE ----------------
    if data == "nuevo_aporte":

        if service.existe_aporte(user_id):
            await query.edit_message_text("⚠️ Ya tienes un aporte en curso.")
            return

        service.iniciar_aporte(user_id)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Omitir comentario", callback_data="skip_comment")]
        ])

        await query.edit_message_text(
            "✍️ Escribe un comentario u omítelo:",
            reply_markup=keyboard
        )

        return

    # ---------------- OMITIR COMENTARIO ----------------
    if data == "skip_comment":

        service.set_comentario(user_id, "")

        await query.edit_message_text(
            "📷 Envía ahora tus archivos.\n\nCuando termines pulsa Enviar aporte.",
            reply_markup=menu_enviar()
        )

        return

    # ---------------- ENVIAR APORTE ----------------
    if data == "enviar_aporte":

        aporte = service.get(user_id)

        if not aporte:
            await query.edit_message_text("⚠️ No hay aporte activo.")
            return

        contador = service.contar_archivos(user_id)

        user = query.from_user
        username = f"@{user.username}" if user.username else "Sin username"

        texto = (
            "📥 NUEVO APORTE\n"
            "━━━━━━━━━━━━━━\n\n"
            f"👤 Nombre: {user.full_name}\n"
            f"🔗 Usuario: {username}\n\n"
            f"📷 Fotos: {contador['photo']}\n"
            f"🎥 Videos: {contador['video']}\n"
            f"📄 Docs: {contador['document']}\n"
            f"🎵 Audio: {contador['audio']}\n\n"
            f"💬 {aporte['comentario'] or 'Sin comentario'}"
        )

        # =====================================================
        # 📤 ENVIAR TEXTO
        # =====================================================
        await context.bot.send_message(chat_id=FRIEND_ID, text=texto)
        await context.bot.send_message(chat_id=GROUP_ID, text=texto)

        # =====================================================
        # 📦 ENVIAR MEDIA (ÁLBUM REAL)
        # =====================================================
        media