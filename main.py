from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, GROUP_ID, FRIEND_ID
from services.aporte_service import AporteService

from datetime import datetime
import json
import os

service = AporteService()

TOPIC_FILE = "topics.json"


import logging
logging.basicConfig(level=logging.INFO)

# ---------------- TOPIC SYSTEM ----------------
def load_topics():
    if os.path.exists(TOPIC_FILE):
        with open(TOPIC_FILE, "r") as f:
            return json.load(f)
    return {}


def save_topics(data):
    with open(TOPIC_FILE, "w") as f:
        json.dump(data, f)


def get_month_key():
    now = datetime.now()
    return f"{now.year}-{now.month}"


async def get_or_create_topic(context):
    topics = load_topics()
    key = get_month_key()

    if key in topics:
        return topics[key]

    now = datetime.now()
    title = f"📦 Aportes {now.strftime('%B %Y')}"

    topic = await context.bot.create_forum_topic(
        chat_id=GROUP_ID,
        name=title
    )

    topic_id = topic.message_thread_id

    topics[key] = topic_id
    save_topics(topics)

    return topic_id


# ---------------- MENU ----------------
def menu_enviar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Enviar aporte", callback_data="enviar_aporte")]
    ])


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

    # NUEVO APORTE
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

    # OMITIR
    elif query.data == "skip_comment":

        service.set_comentario(user_id, "")

        await query.edit_message_text(
            "📷 Ahora envía tus archivos.",
            reply_markup=menu_enviar()
        )

    # ENVIAR
    elif query.data == "enviar_aporte":
    print("DEBUG: ENVIAR APORTE PRESIONADO")

        aporte = service.get(user_id)

        if not aporte:
            await query.edit_message_text("⚠️ No hay aporte activo.")
            return

        comentario = aporte["comentario"]
        archivos = aporte["archivos"]
        total_archivos = len(archivos)

        texto = (
    "📥 NUEVO APORTE\n"
    "━━━━━━━━━━━━━━\n\n"
    f"👤 Nombre: {user.full_name}\n"
    f"🔗 Username: {username}\n"
    f"🆔 ID: {user.id}\n"
    f"👤 Perfil: tg://user?id={user.id}\n\n"
    f"📎 Archivos: {total_archivos}\n\n"
    f"💬 {comentario or 'Sin comentario'}"
)

        topic_id = await get_or_create_topic(context)

        # ENVIAR AL GRUPO
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=texto,
            message_thread_id=topic_id
        )

        for archivo in archivos:
            if archivo["tipo"] == "photo":
                await context.bot.send_photo(GROUP_ID, archivo["file_id"], message_thread_id=topic_id)
            elif archivo["tipo"] == "video":
                await context.bot.send_video(GROUP_ID, archivo["file_id"], message_thread_id=topic_id)
            elif archivo["tipo"] == "audio":
                await context.bot.send_audio(GROUP_ID, archivo["file_id"], message_thread_id=topic_id)
            elif archivo["tipo"] == "document":
                await context.bot.send_document(GROUP_ID, archivo["file_id"], message_thread_id=topic_id)

        # ENVIAR A AMIGO
        await context.bot.send_message(chat_id=FRIEND_ID, text=texto)

        service.limpiar(user_id)

        await query.edit_message_text("✅ Aporte enviado correctamente")


# ---------------- MENSAJES ----------------
async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text

    aporte = service.get(user_id)

    if not aporte:
        return

    estado = aporte["estado"]

    if estado == "WAITING_COMMENT":
        service.set_comentario(user_id, text or "")

        await update.message.reply_text(
            "📷 Ahora envía tus archivos o envía el aporte.",
            reply_markup=menu_enviar()
        )
        return

    if estado == "WAITING_MEDIA":

        if update.message.photo:
            service.agregar_archivo(user_id, update.message.photo[-1].file_id, "photo")
            await update.message.reply_text("📸 Foto recibida", reply_markup=menu_enviar())

        elif update.message.video:
            service.agregar_archivo(user_id, update.message.video.file_id, "video")
            await update.message.reply_text("🎥 Video recibido", reply_markup=menu_enviar())

        elif update.message.audio:
            service.agregar_archivo(user_id, update.message.audio.file_id, "audio")
            await update.message.reply_text("🎵 Audio recibido", reply_markup=menu_enviar())

        elif update.message.document:
            service.agregar_archivo(user_id, update.message.document.file_id, "document")
            await update.message.reply_text("📄 Documento recibido", reply_markup=menu_enviar())


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document.ALL,
        mensajes
    ))

    app.add_handler(MessageHandler(filters.TEXT, mensajes))

    print("🤖 KikuAportes activo")
    app.run_polling()


if __name__ == "__main__":
    main()