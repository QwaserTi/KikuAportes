from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import ContextTypes

from services.aporte_service import service


def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("📩 mensajes() ejecutado")

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
            "Puedes enviar tantos archivos como quieras.\n"
            "Cuando termines pulsa «📤 Enviar aporte».",
            reply_markup=menu_enviar()
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

    elif update.message.video:

        service.agregar_archivo(
            user_id,
            update.message.video.file_id,
            "video"
        )

    elif update.message.document:

        service.agregar_archivo(
            user_id,
            update.message.document.file_id,
            "document"
        )

    elif update.message.audio:

        service.agregar_archivo(
            user_id,
            update.message.audio.file_id,
            "audio"
        )

    else:
        return

    contador = service.contar_archivos(user_id)

    total = (
        contador["photo"] +
        contador["video"] +
        contador["document"] +
        contador["audio"]
    )

    await update.message.reply_text(
        f"✅ Archivo recibido.\n\n"
        f"📎 Archivos acumulados: {total}\n\n"
        "Puedes seguir enviando archivos o pulsar «📤 Enviar aporte».",
        reply_markup=menu_enviar()
    )