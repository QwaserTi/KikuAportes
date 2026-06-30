import asyncio
from services.aporte_manager import manager


class PanelManager:

    def __init__(self):
        self.tasks = {}

    async def render(self, user_id, context, chat_id, version):
        await asyncio.sleep(1.2)

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
            f"📎 Total: {total}"
        )

        old = manager.get_status(user_id)

        if old:
            try:
                await context.bot.delete_message(chat_id, old)
            except:
                pass

        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=texto,
            parse_mode="HTML"
        )

        manager.set_status(user_id, msg.message_id)