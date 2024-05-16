from Controllers.langchain_tools import (
    SendPatientInfo,
)


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
