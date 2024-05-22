import smtplib
from email.message import EmailMessage
import pymongo
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from Controllers import langchain_executor
from Models.ConnectionBD import MONGO_URI, MONGO_TIEMPO_FUERA
from Models.dataModels import Chat, Message, SenderEnum


# Reemplaza 'TU_TOKEN_DE_BOT_AQUI' con el token de tu bot de Telegram
BOT_TOKEN = "7000566232:AAGZkZ-8ER6ETqGLtlROifaJU6940wAlzXc"

# Crea una instancia de la clase Chat para almacenar el historial de la conversación
chat = Chat()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    human_message = Message(sender=SenderEnum.HumanMessage, message=user_query)
    chat.messages.append(human_message)

    ai_response = langchain_executor.invoke(query=user_query, chat_history=chat)
    ai_message = Message(sender=SenderEnum.AIMessage, message=ai_response)
    chat.messages.append(ai_message)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)


async def enviar_correo_datos_paciente(paciente_info):
    # Dirección de correo electrónico del destinatario
    destinatario = "carlos_andres.alzate@uao.edu.co"

    mensaje = f"Un paciente desea agendar una cita doctora\nInformación del paciente:\nNombre: {paciente_info.name}\nEdad: {paciente_info.age}\nCiudad: {paciente_info.city}\nMotivo: {paciente_info.motive}\nDetalles: {paciente_info.details}"
    remitente = "alzatecarlos99@gmail.com"  # Usar el remitente deseado

    email = EmailMessage()
    email["From"] = remitente
    email["To"] = destinatario
    email["Subject"] = "Agendamiento de cita"
    email.set_content(mensaje)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(
            remitente, "wnhl mxyk hkpv xhlz"
        )  # Aquí deberías usar una contraseña segura o almacenarla de forma segura
        server.send_message(email)
        server.quit()
        print("Correo enviado correctamente.")
    except Exception as e:
        print("Error al enviar el correo:", str(e))


async def guardar_datos_paciente(paciente_info):
    # Establecer conexión a la base de datos MongoDB
    try:
        cliente = pymongo.MongoClient(
            MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA
        )
        db = cliente["DatabaseAgents"]
        coleccion = db["Agenda"]

        # Crear el documento a insertar en la colección
        paciente_info_dict = paciente_info.dict()

        # Insertar el documento en la colección
        coleccion.insert_one(paciente_info_dict)
        print("Información del paciente insertada en la base de datos correctamente.")

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        print("Tiempo excedido " + str(errorTiempo))

    except pymongo.errors.ConnectionFailure as errorConexion:
        print("Fallo al conectarse a mongodb " + str(errorConexion))

    finally:
        cliente.close()


async def guardar_datos_cita(citas_info):
    # Establecer conexión a la base de datos MongoDB
    try:
        cliente = pymongo.MongoClient(
            MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA
        )
        db = cliente["DatabaseAgents"]
        coleccion = db["citas"]

        # Crear el documento a insertar en la colección
        citas_info_dict = citas_info.dict()

        # Insertar el documento en la colección
        coleccion.insert_one(citas_info_dict)
        print("Información de la cita insertada en la base de datos correctamente.")

    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        print("Tiempo excedido " + str(errorTiempo))

    except pymongo.errors.ConnectionFailure as errorConexion:
        print("Fallo al conectarse a mongodb " + str(errorConexion))

    finally:
        cliente.close()

    return "Se ha agendado su cita de manera exitosa,feliz dia."


if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    print("Bot iniciado...")
    application.run_polling()
