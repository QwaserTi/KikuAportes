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


def build_panel(aporte):
    contador = service.contar_archivos(aporte["user_id"])

    total = (
        contador["photo"] +
        contador["video"] +
        contador["document"] +
        contador["audio"]
    )

    return (
        "📥 <b>Aporte en progreso</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"💬 Comentario: {'✅' if aporte['comentario'] else '❌'}\n\n"
        f"📷 Fotos: {contador['photo']}\n"
        f"🎥 Videos: {contador['video']}\n"
        f"📄 Documentos: {contador['document']}\n"
        f"🎵 Audios: {contador['audio']}\n\n"
        f"📎 Total: {total}\n\n"
        "Pulsa 📤 Enviar aporte cuando termines."
    )


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

        # crear panel inicial
        texto = (
            "📥 <b>Aporte en progreso</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"💬 Comentario: {'✅' if comentario else '❌'}\n\n"
            "📷 Fotos: 0\n"
            "🎥 Videos: 0\n"
            "📄 Documentos: 0\n"
            "🎵 Audios: 0\n\n"
            "📎 Total: 0\n\n"
            "Pulsa 📤 Enviar aporte cuando termines."
        )

        msg = await update.message.reply_text(
            texto,
            reply_markup=menu_enviar(),
            parse_mode="HTML"
        )

        service.set_status_message(user_id, msg.message_id)

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

    # ---------------- ACTUALIZAR PANEL ----------------

    aporte = service.get(user_id)
    old_msg_id = service.get_status_message(user_id)

    texto = build_panel(aporte)

    # borrar mensaje anterior si existe
    if old_msg_id:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=old_msg_id
            )
        except:
            pass

    # crear nuevo mensaje actualizado
    msg = await update.message.reply_text(
        texto,
        reply_markup=menu_enviar(),
        parse_mode="HTML"
    )

    service.set_status_message(user_id, msg.message_id)