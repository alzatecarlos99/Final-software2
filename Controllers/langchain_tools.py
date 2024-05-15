from typing import Type, Any, Optional
import smtplib
from email.message import EmailMessage
import pydantic
import pymongo
from langchain_core import (
    tools as langchain_core_tools,
    callbacks as langchain_core_callbacks,
)

from Models.ConnectionBD import MONGO_URI, MONGO_TIEMPO_FUERA
from Models.agenda import GoogleCalendarManager
from Models import dataModels
import datetime as dt


class _PatientInfo(pydantic.BaseModel):
    name: str = pydantic.Field(..., description="Nombre del paciente")
    age: int = pydantic.Field(..., description="Edad del paciente")
    city: str = pydantic.Field(..., description="Ciudad del paciente")
    motive: str = pydantic.Field(..., description="Motivo de la consulta")
    details: str = pydantic.Field(..., description="Detalle de la consulta")


class InfoCalendar(pydantic.BaseModel):
    date: str = pydantic.Field(
        ...,
        description="fecha de inicio de la sesion  debe estar en el formato DD-MM-YYYY hh:mm AM/PM",
    )
    name: str = pydantic.Field(..., description="Nombre del paciente")


class SendPatientInfo(langchain_core_tools.BaseTool):
    """Tool that fetches active deployments."""

    name: str = "send_patient_info_to_professional"
    description: str = (
        "Util cuando el paciente quiere agendar una cita con la doctora, para enviar información"
    )

    # Dirección de correo electrónico del destinatario
    destinatario: str = "carlos_andres.alzate@uao.edu.co"

    args_schema: Type[pydantic.BaseModel] = _PatientInfo
    chat_history: Optional[dataModels.Chat] = None
    return_direct = True

    def _init_(
        self, chat_history: Optional[dataModels.Chat] = None, **kwargs: Any
    ) -> None:
        super()._init_(**kwargs)
        self.chat_history = chat_history

    def enviar_correo(self, remitente: str, mensaje: str) -> None:
        email = EmailMessage()
        email["From"] = remitente
        email["To"] = self.destinatario  # Usar el destinatario fijo
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

    def _run(
        self,
        name: str,
        age: int,
        motive: str,
        city: str,
        details: str,
        run_manager: Optional[
            langchain_core_callbacks.CallbackManagerForToolRun
        ] = None,
    ) -> str:
        # Llamar al método para enviar correo electrónico con la información del paciente
        mensaje = f"Un paciente desea agendar una cita doctora\nInformación del paciente:\nNombre: {name}\nEdad: {age}\nCiudad: {city}\nMotivo: {motive}\nDetalles: {details}"
        self.enviar_correo(
            "alzatecarlos99@gmail.com", mensaje
        )  # Usar el remitente deseado

        # Establecer conexión a la base de datos MongoDB
        try:
            cliente = pymongo.MongoClient(
                MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA
            )
            db = cliente["DatabaseAgents"]
            coleccion = db["Agenda"]

            # Crear el documento a insertar en la colección
            paciente_info = {
                "nombre": name,
                "edad": age,
                "ciudad": city,
                "motivo": motive,
                "detalles": details,
            }

            # Insertar el documento en la colección
            coleccion.insert_one(paciente_info)
            print(
                "Información del paciente insertada en la base de datos correctamente."
            )

        except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
            print("Tiempo excedido " + errorTiempo)
        except pymongo.errors.ConnectionFailure as errorConexion:
            print("Fallo al conectarse a mongodb " + errorConexion)

        finally:
            cliente.close()

        if self.chat_history:

            self.chat_history.status = dataModels.ChatStatus.status2

        return "Vale, regálame un momento"


class CreateCalendarEvent(langchain_core_tools.BaseTool):
    """Tool to create an event in Google Calendar."""

    name: str = "create_google_calendar_event"
    description: str = (
        "Permite a los agentes crear un evento en Google Calendar para el usuario."
    )

    args_schema: Type[pydantic.BaseModel] = InfoCalendar
    chat_history: Optional[dataModels.Chat] = None
    return_direct = True

    def _init_(
        self, chat_history: Optional[dataModels.Chat] = None, **kwargs: Any
    ) -> None:
        super()._init_(**kwargs)
        self.chat_history = chat_history

    def _run(
        self,
        date: str,
        name: str,
    ) -> str:
        calendar_manager = GoogleCalendarManager()
        start_time = dt.datetime.strptime(date, "%d-%m-%Y %I:%M %p")
        end_time = start_time + dt.timedelta(hours=1)

        start_time_ = start_time.isoformat()
        end_time_ = end_time.isoformat()

        # Intenta agregar el evento
        try:
            calendar_manager.add_event(
                summary="Cita psicologica",
                start_time=start_time_,
                end_time=end_time_,
                description="f' Tienes una cita agendada con el paciente{name}",
            )
            print("El evento se ha creado correctamente en Google Calendar.")

            # Guardar la información de la cita en la base de datos
            try:
                cliente = pymongo.MongoClient(
                    MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA
                )
                db = cliente["DatabaseAgents"]
                coleccion = db["citas"]

                citas_info = {
                    "fecha_cita": start_time,  # Usamos el objeto datetime directamente
                    "nombre_paciente": name,
                }

                # Insertar el documento en la colección
                coleccion.insert_one(citas_info)
                print(
                    "Información de la cita insertada en la base de datos correctamente."
                )
            except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
                print("Tiempo excedido " + errorTiempo)
            except pymongo.errors.ConnectionFailure as errorConexion:
                print("Fallo al conectarse a MongoDB " + errorConexion)
            finally:
                cliente.close()

            return "El evento se ha creado correctamente en Google Calendar y la información de la cita se ha guardado en la base de datos."
        except Exception as e:
            return f"No se pudo crear el evento en Google Calendar. Error: {str(e)}"
