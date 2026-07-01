from telegram import Message, Update
from telegram.ext import ContextTypes

from core.panel_manager import panel
from services.aporte_manager import manager


def detectar_tipo(msg: Message):
    if msg.photo:
        return "photo"

    if msg.video:
        return "video"

    if msg.document:
        return "document"

    if msg.audio:
        return "audio"

    return None


async def mensajes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    msg = update.message

    if not msg or not msg.from_user:
        return

    user_id = msg.from_user.id
    aporte = manager.get_active(user_id)

    if not aporte:
        return

    if aporte.sending:
        await msg.reply_text(
            "⏳ Tu aporte se está enviando. Espera a que termine."
        )
        return

    if aporte.estado == "DELIVERY_FAILED":
        await msg.reply_text(
            "⚠️ Hay un envío pendiente. Pulsa «Reintentar envío» "
            "antes de añadir otro aporte."
        )
        return

    tipo = detectar_tipo(msg)

    # Si el usuario envía media mientras se esperaba el comentario,
    # se interpreta que decidió omitirlo.
    if aporte.estado == "WAITING_COMMENT":
        if msg.text:
            manager.set_comentario(
                user_id,
                msg.text,
            )

            await panel.render(
                user_id,
                context,
                msg.chat_id,
            )
            return

        if tipo:
            manager.omitir_comentario(user_id)
        else:
            return

    if aporte.estado != "WAITING_MEDIA":
        return

    if not tipo:
        if msg.text:
            await msg.reply_text(
                "ℹ️ El comentario ya está guardado. Ahora envía "
                "fotos, videos, documentos o audios."
            )
        return

    agregado = manager.agregar_mensaje(
        user_id=user_id,
        source_chat_id=msg.chat_id,
        message_id=msg.message_id,
        tipo=tipo,
        media_group_id=msg.media_group_id,
    )

    if agregado:
        # Cada archivo reinicia el temporizador. Dos segundos después
        # del último archivo, el panel se coloca debajo de toda la media.
        panel.schedule(
            user_id=user_id,
            context=context,
            chat_id=msg.chat_id,
            delay=2.0,
        )