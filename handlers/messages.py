from telegram import Update
from telegram.ext import ContextTypes

from services.aporte_service import service
from handlers.buttons import menu_enviar


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

        # crear panel inicial (YA EXISTE EN BUTTONS, solo actualizamos estado)
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