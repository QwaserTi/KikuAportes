from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import asyncio

from services.aporte_service import service


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    user_id = update.message.from_user.id

    aporte = service.get(user_id)

    if aporte is None:
        return

    estado = aporte["estado"]

    # ---------------- COMENTARIO ----------------
    if estado == "WAITING_COMMENT":

        comentario = update.message.text or ""

        service.set_comentario(user_id, comentario)

        await update.message.reply_text(
            "📷 Ahora envía tus archivos.\n\nPuedes enviar fotos, videos, documentos o audios.",
            reply_markup=menu_enviar()
        )

        return

    # ---------------- ARCHIVOS ----------------
    if estado != "WAITING_MEDIA":
        return

    msg = update.message

    if msg.photo:
        service.agregar_archivo(user_id, msg.photo[-1].file_id, "photo")

    elif msg.video:
        service.agregar_archivo(user_id, msg.video.file_id, "video")

    elif msg.document:
        service.agregar_archivo(user_id, msg.document.file_id, "document")

    elif msg.audio:
        service.agregar_archivo(user_id, msg.audio.file_id, "audio")

    else:
        return

    # ---------------- DEBOUNCE SYSTEM ----------------

    async def update_panel():

        await asyncio.sleep(2)

        current = service.get(user_id)
        if not current:
            return

        contador = service.contar_archivos(user_id)

        total = (
            contador["photo"] +
            contador["video"] +
            contador["document"] +
            contador["audio"]
        )

        texto = (
            "📥 <b>Aporte en progreso</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"💬 Comentario: {'✅' if current['comentario'] else '❌'}\n\n"
            f"📷 Fotos: {contador['photo']}\n"
            f"🎥 Videos: {contador['video']}\n"
            f"📄 Documentos: {contador['document']}\n"
            f"🎵 Audios: {contador['audio']}\n\n"
            f"📎 Total: {total}\n\n"
            "Pulsa 📤 Enviar aporte cuando termines."
        )

        old_msg_id = service.get_status_message(user_id)

        if old_msg_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=old_msg_id
                )
            except:
                pass

        new_msg = await update.message.reply_text(
            texto,
            reply_markup=menu_enviar(),
            parse_mode="HTML"
        )

        service.set_status_message(user_id, new_msg.message_id)

    # cancelar anterior y crear nuevo debounce
    task = asyncio.create_task(update_panel())
    service.set_timer(user_id, task)