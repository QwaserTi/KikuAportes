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


async def procesar_panel(user_id, context, update, version):

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
            await context.bot.delete_message(update.message.chat_id, old_msg)
        except:
            pass

    new_msg = await update.message.reply_text(
        texto,
        reply_markup=menu_enviar(),
        parse_mode="HTML"
    )

    service.set_status_message(user_id, new_msg.message_id)


async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message is None:
        return

    user_id = update.message.from_user.id
    aporte = service.get(user_id)

    if not aporte:
        return

    estado = aporte["estado"]

    # ---------------- COMENTARIO ----------------
    if estado == "WAITING_COMMENT":

        service.set_comentario(user_id, update.message.text or "")

        await update.message.reply_text(
            "📷 Envía tus archivos.\nPuedes mandar fotos, videos, documentos o audios.",
            reply_markup=menu_enviar()
        )
        return

    if estado != "WAITING_MEDIA":
        return

    msg = update.message
    media_group_id = msg.media_group_id

    # =====================================================
    # 📦 ÁLBUM
    # =====================================================
    if media_group_id:

        key = (user_id, media_group_id)
        album_buffer[key].append(msg)

        async def procesar_album():

            await asyncio.sleep(1.5)

            messages = album_buffer.pop(key, [])
            if not messages:
                return

            media = []

            for m in messages:
                if m.photo:
                    fid = m.photo[-1].file_id
                    service.agregar_archivo(user_id, fid, "photo")
                    media.append(InputMediaPhoto(fid))

                elif m.video:
                    fid = m.video.file_id
                    service.agregar_archivo(user_id, fid, "video")
                    media.append(InputMediaVideo(fid))

            if media:
                await context.bot.send_media_group(
                    chat_id=update.message.chat_id,
                    media=media
                )

            version = service.bump_version(user_id)
            await procesar_panel(user_id, context, update, version)

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
    asyncio.create_task(procesar_panel(user_id, context, update, version))