import logging
from telegram import Update, ForceReply
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

from Controllers import langchain_executor
from Models.dataModels import Chat, Message, SenderEnum

# Configuración del bot
TOKEN = "7000566232:AAGZkZ-8ER6ETqGLtlROifaJU6940wAlzXc"  # Reemplaza esto con el token de tu bot

# Inicializa el historial de chat
chat = Chat()

# Configura el logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, _: CallbackContext) -> None:
    """Enviar un mensaje de inicio cuando se usa el comando /start."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        rf"Hola {user.mention_markdown_v2()}\! Soy el asistente de la Dra\. Mariana, ¿en qué puedo ayudarte hoy?",
        reply_markup=ForceReply(selective=True),
    )


def handle_message(update: Update, _: CallbackContext) -> None:
    """Responder a los mensajes del usuario."""
    user_query = update.message.text
    ai_response = langchain_executor.invoke(query=user_query, chat_history=chat)

    human_message = Message(sender=SenderEnum.HumanMessage, message=user_query)
    ai_message = Message(sender=SenderEnum.AIMessage, message=ai_response)
    chat.messages.extend([human_message, ai_message])

    update.message.reply_text(ai_response)


def main() -> None:
    """Iniciar el bot."""
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    # Comandos
    dispatcher.add_handler(CommandHandler("start", start))

    # Mensajes
    dispatcher.add_handler(
        MessageHandler(filters.text & ~filters.command, handle_message)
    )

    # Iniciar el Bot
    updater.start_polling()

    updater.idle()


if __name__ == "_main_":
    main()
