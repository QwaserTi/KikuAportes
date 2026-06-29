from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from services.aporte_service import AporteService

service = AporteService()


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆕 Nuevo aporte", callback_data="nuevo_aporte")]
    ]

    await update.message.reply_text(
        "💌 Bienvenido a KikuAportes 💌",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- BOTONES ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "nuevo_aporte":

        if service.existe_aporte(user_id):
            await query.edit_message_text("⚠️ Ya tienes un aporte en curso.")
            return

        service.iniciar_aporte(user_id)

        keyboard = [
            [InlineKeyboardButton("⏭ Omitir comentario", callback_data="skip_comment")]
        ]

        await query.edit_message_text(
            "✍️ Escribe un comentario u omítelo:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "skip_comment":

        service.set_comentario(user_id, "")

        await query.edit_message_text("📷 Ahora envía tus archivos.")


# ---------------- MENSAJES ----------------
async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text

    aporte = service.get(user_id)

    if not aporte:
        return

    estado = aporte["estado"]

    # comentario
    if estado == "WAITING_COMMENT":
        service.set_comentario(user_id, text or "")
        await update.message.reply_text("📷 Ahora envía tus archivos.")
        return

    # SOLO MEDIA
    if estado == "WAITING_MEDIA":

        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            service.agregar_archivo(user_id, file_id, "photo")
            await update.message.reply_text("📸 Foto recibida")

        elif update.message.video:
            service.agregar_archivo(user_id, update.message.video.file_id, "video")
            await update.message.reply_text("🎥 Video recibido")

        elif update.message.audio:
            service.agregar_archivo(user_id, update.message.audio.file_id, "audio")
            await update.message.reply_text("🎵 Audio recibido")

        elif update.message.document:
            service.agregar_archivo(user_id, update.message.document.file_id, "document")
            await update.message.reply_text("📄 Documento recibido")


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    # 🔥 FIX IMPORTANTE: separar media de texto correctamente
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document.ALL,
        mensajes
    ))

    app.add_handler(MessageHandler(filters.TEXT, mensajes))

    print("🤖 KikuAportes activo")
    app.run_polling()


if __name__ == "__main__":
    main()