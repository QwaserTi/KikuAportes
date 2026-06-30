from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import asyncio
from collections import defaultdict

from services.aporte_service import service


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


# 🔥 BUFFER PARA ÁLBUMES
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

    # ---------------- SOLO MEDIA ----------------
    if estado != "WAITING_MEDIA":
        return

    msg = update.message
    media_group_id = msg.media_group_id

    # =====================================================
    # 🔥 1. DETECCIÓN DE ÁLBUM
    # =====================================================
    if media_group_id:

        key = (user_id, media_group_id)
        album_buffer[key].append(msg)

        async def procesar_album():

            await asyncio.sleep(1.5)

            messages = album_buffer.pop(key, [])

            if not messages:
                return

            # guardar archivos del álbum
            for m in messages:

                if m.photo:
                    service.agregar_archivo(user_id, m.photo[-1].file_id, "photo")

                elif m.video:
                    service.agregar_archivo(user_id, m.video.file_id, "video")

            # actualizar panel UNA sola vez
            version = service.bump_version(user_id)
            await procesar_panel(user_id, context, update, version)

        # cancelar tarea previa del mismo álbum
        old_task = album_tasks.get(key)
        if old_task and not old_task.done():
            old_task.cancel()

        task = asyncio.create_task(procesar_album())
        album_tasks[key] = task

        return

    # =====================================================
    # 🔥 2. MEDIA NORMAL (NO ÁLBUM)
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

    # =====================================================
    # 🔥 3. DEBOUNCE NORMAL
    # =====================================================

    version = service.bump_version(user_id)

    asyncio.create_task(procesar_panel(user_id, context, update, version))