from telegram import Update
from telegram.ext import ContextTypes

from services.aporte_service import service


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
            "📷 Ahora envía todas las fotos, videos, documentos o audios que quieras.\n\n"
            "Cuando termines, pulsa «📤 Enviar aporte»."
        )

        return

    # ---------------- ARCHIVOS ----------------

    if estado != "WAITING_MEDIA":
        return

    if update.message.photo:

        service.agregar_archivo(
            user_id,
            update.message.photo[-1].file_id,
            "photo"
        )

        return

    if update.message.video:

        service.agregar_archivo(
            user_id,
            update.message.video.file_id,
            "video"
        )

        return

    if update.message.document:

        service.agregar_archivo(
            user_id,
            update.message.document.file_id,
            "document"
        )

        return

    if update.message.audio:

        service.agregar_archivo(
            user_id,
            update.message.audio.file_id,
            "audio"
        )

        return