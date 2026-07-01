import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import FRIEND_ID, GROUP_ID
from core.panel_manager import panel
from services.aporte_manager import manager


logger = logging.getLogger(__name__)


def skip_comment_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⏭ Omitir comentario", callback_data="skip_comment")]]
    )


def retry_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Reintentar envío", callback_data="enviar_aporte")]]
    )


def new_aporte_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🆕 Nuevo aporte", callback_data="nuevo_aporte")]]
    )


def split_text(text, limit=4096):
    """Divide texto largo intentando respetar saltos de línea."""
    if len(text) <= limit:
        return [text]

    parts = []
    remaining = text

    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break

        cut = remaining.rfind("\n", 0, limit + 1)
        if cut <= 0:
            cut = limit

        parts.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")

    return parts


def build_summary(user, contador, comentario):
    """Crea la ficha que se envía después de toda la media."""
    username = f"@{user.username}" if user.username else "Sin username"
    total = sum(contador.values())
    comentario_texto = comentario if comentario else "Sin comentario"

    return (
        "📥 APORTE RECIBIDO\n"
        "━━━━━━━━━━━━━━\n\n"
        f"👤 Nombre: {user.full_name}\n"
        f"🔗 Usuario: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"📷 Fotos: {contador['photo']}\n"
        f"🎥 Videos: {contador['video']}\n"
        f"📄 Documentos: {contador['document']}\n"
        f"🎵 Audios: {contador['audio']}\n"
        f"📎 Total: {total}\n\n"
        f"💬 Comentario:\n{comentario_texto}"
    )


async def send_to_destination(
    context,
    user_id,
    destination_id,
    user,
    contador,
):
    """
    Envía primero toda la media y al final la ficha con el comentario.

    El progreso se guarda por destino para que un reintento continúe desde
    donde falló sin repetir los lotes o partes de texto ya completados.
    """
    aporte = manager.get_active(user_id)
    progress = manager.get_delivery_progress(user_id, destination_id)

    if not aporte or not progress:
        raise RuntimeError(
            "El aporte dejó de estar disponible durante el envío"
        )

    if progress["completed"]:
        return

    # Primero se envía toda la media.
    batches = manager.construir_lotes_copia(user_id)

    while progress["batches_sent"] < len(batches):
        index = progress["batches_sent"]
        batch = batches[index]

        copied = await context.bot.copy_messages(
            chat_id=destination_id,
            from_chat_id=batch["source_chat_id"],
            message_ids=batch["message_ids"],
        )

        if len(copied) != len(batch["message_ids"]):
            raise RuntimeError(
                "Telegram omitió uno o más mensajes al copiar el aporte"
            )

        progress["batches_sent"] += 1

    # La ficha y el comentario se envían al final de toda la media.
    summary_parts = split_text(
        build_summary(
            user=user,
            contador=contador,
            comentario=aporte.comentario,
        )
    )

    while progress["summary_parts_sent"] < len(summary_parts):
        index = progress["summary_parts_sent"]

        await context.bot.send_message(
            chat_id=destination_id,
            text=summary_parts[index],
        )

        progress["summary_parts_sent"] += 1

    progress["completed"] = True


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query or not query.from_user or not query.message:
        return

    user_id = query.from_user.id
    data = query.data

    if data == "nuevo_aporte":
        await query.answer()

        manager.iniciar_aporte(user_id)
        manager.set_status(
            user_id,
            query.message.message_id,
        )

        await query.edit_message_text(
            "📝 Escribe un comentario para tu aporte.\n\n"
            "También puedes omitirlo y empezar a enviar archivos.",
            reply_markup=skip_comment_menu(),
        )
        return

    aporte = manager.get_active(user_id)

    if not aporte:
        await query.answer(
            "No hay un aporte activo.",
            show_alert=True,
        )

        await query.edit_message_text(
            "⚠️ No hay un aporte activo.",
            reply_markup=new_aporte_menu(),
        )
        return

    if data == "skip_comment":
        await query.answer("Comentario omitido")

        if aporte.estado == "WAITING_COMMENT":
            manager.omitir_comentario(user_id)

        manager.set_status(
            user_id,
            query.message.message_id,
        )

        await panel.render(
            user_id,
            context,
            query.message.chat_id,
        )
        return

    if data != "enviar_aporte":
        await query.answer()
        return

    if aporte.sending:
        await query.answer(
            "El aporte ya se está enviando.",
            show_alert=True,
        )
        return

    if manager.total(user_id) == 0:
        await query.answer(
            "Envía al menos una foto, video, documento o audio.",
            show_alert=True,
        )
        return

    destinations = list(
        dict.fromkeys([GROUP_ID, FRIEND_ID])
    )

    if any(not destination for destination in destinations):
        await query.answer(
            "Falta configurar un destino en el .env.",
            show_alert=True,
        )
        return

    await query.answer("Enviando aporte…")

    # Se bloquea el aporte antes de cancelar el panel para impedir que
    # aparezca una actualización nueva durante el envío.
    aporte = manager.iniciar_envio(user_id)

    if not aporte:
        return

    panel.cancel(user_id)

    try:
        await query.edit_message_text(
            "⏳ Enviando aporte al grupo y al chat…"
        )
    except TelegramError:
        logger.warning(
            "No se pudo actualizar el mensaje de progreso",
            exc_info=True,
        )

    contador = manager.contar(user_id)
    errors = []

    for destination_id in destinations:
        try:
            await send_to_destination(
                context=context,
                user_id=user_id,
                destination_id=destination_id,
                user=query.from_user,
                contador=contador,
            )
        except Exception as exc:
            logger.exception(
                "Error enviando el aporte del usuario %s al destino %s",
                user_id,
                destination_id,
            )

            errors.append(
                (destination_id, exc)
            )

    if errors:
        manager.terminar_intento_envio(
            user_id,
            completado=False,
        )

        failed_ids = ", ".join(
            str(destination_id)
            for destination_id, _ in errors
        )

        await query.edit_message_text(
            "⚠️ El aporte no pudo completarse en todos los destinos.\n\n"
            f"Destino(s) pendiente(s): {failed_ids}\n"
            "El progreso quedó guardado; al reintentar no se volverán "
            "a enviar los destinos ya completados.",
            reply_markup=retry_menu(),
        )
        return

    manager.terminar_intento_envio(
        user_id,
        completado=True,
    )

    manager.limpiar(user_id)

    await query.edit_message_text(
        "✅ Aporte enviado correctamente al grupo y al chat.",
        reply_markup=new_aporte_menu(),
    )