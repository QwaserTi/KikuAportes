import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError

from services.aporte_manager import manager


logger = logging.getLogger(__name__)


class PanelManager:
    def __init__(self):
        self.tasks = {}

    def cancel(self, user_id):
        task = self.tasks.pop(user_id, None)
        if task and not task.done():
            task.cancel()

    def schedule(self, user_id, context, chat_id, delay=0.7):
        self.cancel(user_id)

        async def delayed_render():
            try:
                await asyncio.sleep(delay)
                await self.render(user_id, context, chat_id)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.exception("No se pudo actualizar el panel del usuario %s", user_id)
            finally:
                current = self.tasks.get(user_id)
                if current is asyncio.current_task():
                    self.tasks.pop(user_id, None)

        self.tasks[user_id] = asyncio.create_task(delayed_render())

    async def render(self, user_id, context, chat_id):
        aporte = manager.get_active(user_id)
        if not aporte or aporte.sending:
            return

        contador = manager.contar(user_id)
        total = sum(contador.values())
        comentario = "✅ Añadido" if aporte.comentario else "⏭ Omitido"

        texto = (
            "📥 <b>Aporte en progreso</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"💬 Comentario: {comentario}\n\n"
            f"📷 Fotos: {contador['photo']}\n"
            f"🎥 Videos: {contador['video']}\n"
            f"📄 Documentos: {contador['document']}\n"
            f"🎵 Audios: {contador['audio']}\n\n"
            f"📎 Total: {total}\n\n"
            "Envía más archivos o pulsa el botón cuando termines."
        )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]]
        )

        old_message_id = manager.get_status(user_id)
        if old_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=old_message_id,
                    text=texto,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                return
            except BadRequest as exc:
                if "message is not modified" in str(exc).lower():
                    return
            except TelegramError:
                logger.warning(
                    "No se pudo editar el panel %s del usuario %s",
                    old_message_id,
                    user_id,
                    exc_info=True,
                )

        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=texto,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        manager.set_status(user_id, msg.message_id)


panel = PanelManager()
