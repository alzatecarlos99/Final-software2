
from Controllers.langchain_tools import SendPatientInfo, CreateCalendarEvent
def test_send_patient_info():
    tool = SendPatientInfo()
    response = tool._run(
        name="John Doe",
        age=30,
        motive="Consulta de rutina",
        city="Ciudad Prueba",
        details="Detalles adicionales aquí"
    )
    assert response == "Vale, regálame un momento", "El mensaje de respuesta no es el esperado"

def test_create_calendar_event():
    tool = CreateCalendarEvent()
    test_date = "24-04-2024 09:00 AM"
    response = tool._run(
        date=test_date,
        name="John Doe"
    )
    assert "El evento se ha creado correctamente" in response, "El evento no se creó correctamente"
