from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto, InputMediaVideo

import asyncio
from collections import defaultdict

from services.aporte_service import service


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


album_buffer = defaultdict(list)
album_tasks = {}
panel_tasks = {}


# =====================================================
# PANEL (ANTI-DUPLICADOS + ESTABLE)
# =====================================================
async def procesar_panel(user_id, context, chat_id, version):

    await asyncio.sleep(2)

    if service.get_version(user_id) != version:
        return

    current = service.get(user_id)
    if not current:
        return

    contador = service.contar_archivos(user_id)
    total = sum(contador.values())

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

    old_msg = service.get_status_message(user_id)

    if old_msg:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_msg)
        except:
            pass

    new_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=texto,
        reply_markup=menu_enviar(),
        parse_mode="HTML"
    )

    service.set_status_message(user_id, new_msg.message_id)


# =====================================================
# MAIN HANDLER
# =====================================================
async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    aporte = service.get(user_id)
    if not aporte:
        return

    estado = aporte["estado"]
    msg = update.message

    # ---------------- COMENTARIO ----------------
    if estado == "WAITING_COMMENT":

        service.set_comentario(user_id, msg.text or "")

        await msg.reply_text(
            "📷 Envía tus archivos.\nPuedes mandar fotos, videos, documentos o audios.",
            reply_markup=menu_enviar()
        )
        return

    if estado != "WAITING_MEDIA":
        return

    media_group_id = msg.media_group_id

    # =====================================================
    # 📦 ÁLBUM (SIN REENVIAR AL CHAT)
    # =====================================================
    if media_group_id:

        key = (user_id, media_group_id)
        album_buffer[key].append(msg)

        async def procesar_album():

            await asyncio.sleep(1.2)

            messages = album_buffer.pop(key, [])
            if not messages:
                return

            for m in messages:
                if m.photo:
                    service.agregar_archivo(user_id, m.photo[-1].file_id, "photo")
                elif m.video:
                    service.agregar_archivo(user_id, m.video.file_id, "video")

            version = service.bump_version(user_id)
            await procesar_panel(user_id, context, chat_id, version)

        old = album_tasks.get(key)
        if old:
            old.cancel()

        album_tasks[key] = asyncio.create_task(procesar_album())
        return

    # =====================================================
    # 📎 ARCHIVO NORMAL
    # =====================================================
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

    version = service.bump_version(user_id)

    # cancelar panel anterior si existe
    old_task = panel_tasks.get(user_id)
    if old_task:
        old_task.cancel()

    panel_tasks[user_id] = asyncio.create_task(
        procesar_panel(user_id, context, chat_id, version)
    )