from unittest.mock import patch, MagicMock
from Controllers.langchain_tools import (
    SendPatientInfo,
    CreateCalendarEvent,
    GoogleCalendarManager,
)
import datetime
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import unittest
import pytest

# pruebas unitarias


def test_send_patient_info():
    tool = SendPatientInfo()
    response = tool._run(
        name="John Doe",
        age=30,
        motive="Consulta de rutina",
        city="Ciudad Prueba",
        details="Detalles adicionales aquí",
    )
    assert (
        response == "Vale, regálame un momento"
    ), "El mensaje de respuesta no es el esperado"


def test_create_calendar_event():
    tool = CreateCalendarEvent()
    test_date = "24-04-2024 09:00 AM"
    response = tool._run(date=test_date, name="John Doe")
    assert (
        "El evento se ha creado correctamente" in response
    ), "El evento no se creó correctamente"


# Pruebas de integración para GoogleCalendarManager
@pytest.fixture
def calendar_manager():
    return GoogleCalendarManager()


def test_add_and_retrieve_event(calendar_manager):
    # Asegurarse de usar un entorno y credenciales seguros y de prueba
    start_time = (
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    ).isoformat() + "Z"
    end_time = (
        datetime.datetime.utcnow() + datetime.timedelta(days=1, hours=1)
    ).isoformat() + "Z"
    calendar_manager.add_event("Test Event", start_time, end_time)
    events = calendar_manager.get_upcoming_events()
    assert any(
        event["summary"] == "Test Event" for event in events
    ), "Event added should be in the upcoming events"


def test_authentication_and_fetch_events(calendar_manager):
    events = calendar_manager.get_upcoming_events()
    assert events is not None, "Should fetch events after authenticating"


@patch("requests.get")
def test_get_upcoming_events(mock_get):
    # Configuración del mock
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "items": [
            {
                "start": {"dateTime": "2024-04-24T09:00:00Z"},
                "summary": "Evento de prueba",
            }
        ]
    }

    calendar_manager = GoogleCalendarManager()
    events = calendar_manager.get_upcoming_events()
    assert events == [
        {"start": {"dateTime": "2024-04-24T09:00:00Z"}, "summary": "Evento de prueba"}
    ], "No se obtuvieron los eventos esperados"


@patch("Models.ConnectionBD.pymongo.MongoClient")
class TestMongoConnection(unittest.TestCase):
    def test_mongo_Connection_success(self, mock_mongo_client):
        mock_client_instance = MagicMock()
        mock_client_instance.server_info.return_value = True
        mock_mongo_client.return_value = mock_client_instance
        assert "Conexión a mongo exitosa"

    def test_mongo_Connection_timeout_error(self, mock_mongo_client):
        mock_client_instance = MagicMock()
        mock_client_instance.server_info.side_effect = ServerSelectionTimeoutError(
            "Tiempo excedido"
        )
        mock_mongo_client.return_value = mock_client_instance
        assert "Tiempo excedido"

    def test_mongo_Connection_failure(self, mock_mongo_client):
        mock_client_instance = MagicMock()
        mock_client_instance.server_info.side_effect = ConnectionFailure(
            "Fallo al conectarse a mongodb"
        )
        mock_mongo_client.return_value = mock_client_instance
        assert "Fallo al conectarse a mongodb"
