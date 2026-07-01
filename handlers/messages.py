import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from services.aporte_manager import manager
from core.album_buffer import AlbumBuffer
from core.panel_manager import PanelManager

album = AlbumBuffer()
panel = PanelManager()


async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    msg = update.message
    user_id = msg.from_user.id
    chat_id = msg.chat_id

    aporte = manager.get_active(user_id)
    if not aporte:
        return

    estado = aporte.estado

    # -------------------------
    # COMENTARIO
    # -------------------------
    if estado == "WAITING_COMMENT":

        manager.set_comentario(user_id, msg.text or "")

        await msg.reply_text(
            "📷 Ahora envía tus archivos.\n\nCuando termines pulsa 'Enviar aporte'."
        )
        return

    if estado != "WAITING_MEDIA":
        return

    media_group_id = msg.media_group_id

    # -------------------------
    # ALBUM
    # -------------------------
    if media_group_id:

        key = (user_id, media_group_id)

        album.add(key, msg)

        async def procesar_album():

            await asyncio.sleep(1.5)

            messages = album.pop_group(key)

            for m in messages:

                if m.photo:
                    manager.agregar_archivo(user_id, m.photo[-1].file_id, "photo")

                elif m.video:
                    manager.agregar_archivo(user_id, m.video.file_id, "video")

                elif m.document:
                    manager.agregar_archivo(user_id, m.document.file_id, "document")

                elif m.audio:
                    manager.agregar_archivo(user_id, m.audio.file_id, "audio")

            await panel.render(user_id, context, chat_id, version=1)

        album.cancel(key)
        task = asyncio.create_task(procesar_album())
        album.set_task(key, task)

        return

    # -------------------------
    # ARCHIVO INDIVIDUAL
    # -------------------------
    if msg.photo:
        manager.agregar_archivo(user_id, msg.photo[-1].file_id, "photo")

    elif msg.video:
        manager.agregar_archivo(user_id, msg.video.file_id, "video")

    elif msg.document:
        manager.agregar_archivo(user_id, msg.document.file_id, "document")

    elif msg.audio:
        manager.agregar_archivo(user_id, msg.audio.file_id, "audio")

    await panel.render(user_id, context, chat_id, version=1)