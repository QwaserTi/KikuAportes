import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError

from services.aporte_manager import manager


logger = logging.getLogger(__name__)


class PanelManager:
    def __init__(self):
        self.tasks = {}
        self.locks = {}

    def _get_lock(self, user_id):
        lock = self.locks.get(user_id)

        if lock is None:
            lock = asyncio.Lock()
            self.locks[user_id] = lock

        return lock

    def cancel(self, user_id):
        task = self.tasks.pop(user_id, None)

        if task and not task.done():
            task.cancel()

    def schedule(
        self,
        user_id,
        context,
        chat_id,
        delay=2.0,
    ):
        """
        Espera a que el usuario deje de enviar archivos.

        Cada archivo reinicia el temporizador, por lo que, al enviar una
        cantidad grande de media, el panel se recrea una sola vez al final.
        """
        self.cancel(user_id)

        async def delayed_render():
            try:
                await asyncio.sleep(delay)

                await self.render(
                    user_id,
                    context,
                    chat_id,
                )

            except asyncio.CancelledError:
                return

            except Exception:
                logger.exception(
                    "No se pudo actualizar el panel del usuario %s",
                    user_id,
                )

            finally:
                current = self.tasks.get(user_id)

                if current is asyncio.current_task():
                    self.tasks.pop(user_id, None)

        self.tasks[user_id] = asyncio.create_task(
            delayed_render()
        )

    async def render(
        self,
        user_id,
        context,
        chat_id,
    ):
        """
        Borra el panel anterior y crea otro al final del chat.

        Editar un mensaje no cambia su posición dentro de Telegram.
        Por eso se elimina y se vuelve a enviar.
        """
        lock = self._get_lock(user_id)

        async with lock:
            aporte = manager.get_active(user_id)

            if not aporte or aporte.sending:
                return

            contador = manager.contar(user_id)
            total = sum(contador.values())

            comentario = (
                "✅ Añadido"
                if aporte.comentario
                else "⏭ Omitido"
            )

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
                [
                    [
                        InlineKeyboardButton(
                            "📤 Enviar aporte",
                            callback_data="enviar_aporte",
                        )
                    ]
                ]
            )

            old_message_id = manager.get_status(user_id)

            if old_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=old_message_id,
                    )

                except BadRequest as exc:
                    if (
                        "message to delete not found"
                        not in str(exc).lower()
                    ):
                        logger.warning(
                            "Telegram no permitió borrar el panel "
                            "%s del usuario %s: %s",
                            old_message_id,
                            user_id,
                            exc,
                        )

                except TelegramError:
                    logger.warning(
                        "No se pudo borrar el panel %s "
                        "del usuario %s",
                        old_message_id,
                        user_id,
                        exc_info=True,
                    )

            # Se comprueba de nuevo por si el envío comenzó mientras
            # se estaba eliminando el panel anterior.
            aporte = manager.get_active(user_id)

            if not aporte or aporte.sending:
                return

            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=texto,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

            manager.set_status(
                user_id,
                msg.message_id,
            )


panel = PanelManager()