from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import GROUP_ID, FRIEND_ID
from services.aporte_service import service
from handlers.messages import service as msg_service  # misma instancia lógica

import logging

logger = logging.getLogger(__name__)


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("🟢 HANDLER BUTTONS EJECUTADO")

    query = update.callback_query

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

        comentario = aporte["comentario"]
        archivos = aporte["archivos"]

        contador = service.contar_archivos(user_id)

        user = query.from_user
        username = f"@{user.username}" if user.username else "Sin username"

        texto = (
            "📥 NUEVO APORTE\n"
            "━━━━━━━━━━━━━━\n\n"
            f"👤 Nombre: {user.full_name}\n"
            f"🔗 Usuario: {username}\n\n"
            f"📎 Archivos:\n"
            f"📷 Fotos: {contador['photo']}\n"
            f"🎥 Videos: {contador['video']}\n"
            f"📄 Docs: {contador['document']}\n"
            f"🎵 Audio: {contador['audio']}\n\n"
            f"💬 {comentario or 'Sin comentario'}"
        )

        # ENVIAR AL AMIGO
        await context.bot.send_message(
            chat_id=FRIEND_ID,
            text=texto
        )

        # ENVIAR AL GRUPO
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=texto
        )

        for archivo in archivos:

            tipo = archivo["tipo"]

            if tipo == "photo":
                await context.bot.send_photo(GROUP_ID, archivo["file_id"])

            elif tipo == "video":
                await context.bot.send_video(GROUP_ID, archivo["file_id"])

            elif tipo == "document":
                await context.bot.send_document(GROUP_ID, archivo["file_id"])

            elif tipo == "audio":
                await context.bot.send_audio(GROUP_ID, archivo["file_id"])

        service.limpiar(user_id)

        await query.edit_message_text("✅ Aporte enviado correctamente")