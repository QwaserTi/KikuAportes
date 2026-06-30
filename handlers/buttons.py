from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio
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

        archivos = aporte.get("archivos", [])

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
        # 📦 ENVIAR MEDIA (ÁLBUM + SUELTOS BIEN MANEJADO)
        # =====================================================

        if archivos:

            media_group = []

            for archivo in archivos:

                tipo = archivo["tipo"]
                fid = archivo["file_id"]

                if tipo == "photo":
                    media_group.append(InputMediaPhoto(media=fid))

                elif tipo == "video":
                    media_group.append(InputMediaVideo(media=fid))

                elif tipo == "document":
                    media_group.append(InputMediaDocument(media=fid))

                elif tipo == "audio":
                    media_group.append(InputMediaAudio(media=fid))

            # Telegram permite máximo 10 por álbum
            chunks = [media_group[i:i+10] for i in range(0, len(media_group), 10)]

            for chunk in chunks:
                if len(chunk) == 1:
                    # si solo hay 1 archivo, enviar normal
                    m = chunk[0]
                    if isinstance(m, InputMediaPhoto):
                        await context.bot.send_photo(GROUP_ID, m.media)
                    elif isinstance(m, InputMediaVideo):
                        await context.bot.send_video(GROUP_ID, m.media)
                    elif isinstance(m, InputMediaDocument):
                        await context.bot.send_document(GROUP_ID, m.media)
                    elif isinstance(m, InputMediaAudio):
                        await context.bot.send_audio(GROUP_ID, m.media)
                else:
                    await context.bot.send_media_group(
                        chat_id=GROUP_ID,
                        media=chunk
                    )

        # =====================================================
        # 🧹 LIMPIEZA FINAL SEGURA
        # =====================================================
        service.limpiar(user_id)

        await query.edit_message_text("✅ Aporte enviado correctamente")