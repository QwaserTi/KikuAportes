from telegram import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from telegram.ext import ContextTypes

from config import GROUP_ID, FRIEND_ID
from services.aporte_manager import manager


def chunk_list(lst, size=10):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


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

    user = query.from_user
    username = f"@{user.username}" if user.username else "Sin username"

    contador = manager.contar(user_id)

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

    # -------------------------
    # ENVIAR TEXTO
    # -------------------------
    await context.bot.send_message(chat_id=GROUP_ID, text=texto)
    await context.bot.send_message(chat_id=FRIEND_ID, text=texto)

    # -------------------------
    # RECONSTRUIR MEDIA EN ORDEN
    # -------------------------
    media = []

    # Álbumes primero (en orden de llegada)
    for album in aporte.albums.values():
        album_media = []

        for f in album:
            if f["tipo"] == "photo":
                album_media.append(InputMediaPhoto(f["file_id"]))
            elif f["tipo"] == "video":
                album_media.append(InputMediaVideo(f["file_id"]))

        if album_media:
            media.append(album_media)

    # Archivos sueltos después
    for f in aporte.archivos:

        if f["tipo"] == "photo":
            media.append([InputMediaPhoto(f["file_id"])])

        elif f["tipo"] == "video":
            media.append([InputMediaVideo(f["file_id"])])

        elif f["tipo"] == "document":
            media.append([InputMediaDocument(f["file_id"])])

        elif f["tipo"] == "audio":
            media.append([InputMediaAudio(f["file_id"])])

    # -------------------------
    # ENVÍO ORDENADO
    # -------------------------
    for group in media:

        if len(group) == 1:
            m = group[0]

            if isinstance(m, InputMediaPhoto):
                await context.bot.send_photo(GROUP_ID, m.media)
            elif isinstance(m, InputMediaVideo):
                await context.bot.send_video(GROUP_ID, m.media)
            elif isinstance(m, InputMediaDocument):
                await context.bot.send_document(GROUP_ID, m.media)
            elif isinstance(m, InputMediaAudio):
                await context.bot.send_audio(GROUP_ID, m.media)

        else:
            await context.bot.send_media_group(
                chat_id=GROUP_ID,
                media=group
            )

    # -------------------------
    # LIMPIEZA FINAL
    # -------------------------
    manager.aportes[user_id].pop(manager.active[user_id], None)
    manager.active.pop(user_id, None)

    await query.edit_message_text("✅ Aporte enviado correctamente")