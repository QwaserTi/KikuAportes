from telegram import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from telegram.ext import ContextTypes

from config import GROUP_ID, FRIEND_ID
from services.aporte_manager import manager


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data != "enviar_aporte":
        return

    aporte = manager.get_active(user_id)

    if not aporte:
        await query.edit_message_text("⚠️ No hay aporte activo.")
        return

    contador = manager.contar(user_id)
    user = query.from_user
    username = f"@{user.username}" if user.username else "Sin username"

    texto = (
        "📥 NUEVO APORTE\n"
        "━━━━━━━━━━━━━━\n\n"
        f"👤 Nombre: {user.full_name}\n"
        f"🔗 Usuario: {username}\n\n"
        f"📷 Fotos: {contador['photo']}\n"
        f"🎥 Videos: {contador['video']}\n"
        f"📄 Docs: {contador['document']}\n"
        f"🎵 Audio: {contador['audio']}\n\n"
        f"💬 {aporte.comentario or 'Sin comentario'}"
    )

    # ---------------- TEXTO ----------------
    await context.bot.send_message(chat_id=GROUP_ID, text=texto)
    await context.bot.send_message(chat_id=FRIEND_ID, text=texto)

    # ---------------- MEDIA ----------------
    # ALBUMES PRIMERO
    for album in aporte.albums.values():

        media_group = []

        for f in album:
            if f["tipo"] == "photo":
                media_group.append(InputMediaPhoto(f["file_id"]))
            elif f["tipo"] == "video":
                media_group.append(InputMediaVideo(f["file_id"]))

        if media_group:
            await context.bot.send_media_group(GROUP_ID, media=media_group)

    # ARCHIVOS SUELTOS
    for f in aporte.archivos:

        if f["tipo"] == "photo":
            await context.bot.send_photo(GROUP_ID, f["file_id"])

        elif f["tipo"] == "video":
            await context.bot.send_video(GROUP_ID, f["file_id"])

        elif f["tipo"] == "document":
            await context.bot.send_document(GROUP_ID, f["file_id"])

        elif f["tipo"] == "audio":
            await context.bot.send_audio(GROUP_ID, f["file_id"])

    # ---------------- LIMPIEZA ----------------
    manager.aportes[user_id].pop(manager.active[user_id], None)
    manager.active.pop(user_id, None)

    await query.edit_message_text("✅ Aporte enviado correctamente")