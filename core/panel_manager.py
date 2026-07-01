import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.aporte_manager import manager


class PanelManager:

    def __init__(self):
        self.tasks = {}

    async def render(self, user_id, context, chat_id, version):

        await asyncio.sleep(1.2)

        # 🔒 protección contra renders antiguos
        current_version = manager.get_active(user_id)
        if not current_version:
            return

        # si el usuario ya cambió estado, no renderizar
        # (evita paneles viejos sobrescribiendo nuevos)
        aporte = manager.get_active(user_id)
        if not aporte:
            return

        contador = manager.contar(user_id)
        total = sum(contador.values())

        texto = (
            "📥 <b>Aporte en progreso</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"💬 Comentario: {'✅' if aporte.comentario else '❌'}\n\n"
            f"📷 Fotos: {contador['photo']}\n"
            f"🎥 Videos: {contador['video']}\n"
            f"📄 Docs: {contador['document']}\n"
            f"🎵 Audios: {contador['audio']}\n\n"
            f"📎 Total: {total}\n\n"
            "Pulsa el botón cuando termines."
        )

        # -------------------------
        # borrar panel anterior
        # -------------------------
        old = manager.get_status(user_id)

        if old:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=old)
            except:
                pass

        # -------------------------
        # BOTÓN CLAVE (ANTES FALTABA)
        # -------------------------
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
        ])

        # -------------------------
        # enviar panel nuevo
        # -------------------------
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=texto,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        manager.set_status(user_id, msg.message_id)