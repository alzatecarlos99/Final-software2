import datetime as dt
import os.path
from pprint import pprint
from typing import Optional
import pytz
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError  # Importar RefreshError

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarManager:
    def __init__(self):
        self._token_file = "../token.json"
        self._creds = self._authenticate()

    def _authenticate(self) -> Credentials:
        creds = None

        if os.path.exists(self._token_file):
            creds = Credentials.from_authorized_user_file(self._token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:  # Utilizar la excepción importada
                    print("El token ha expirado o ha sido revocado. Reautenticando...")
                    creds = self._reauthenticate()
            else:
                creds = self._reauthenticate()

        # Guardar las credenciales para la próxima ejecución
        with open(self._token_file, "w") as token:
            token.write(creds.to_json())

        return creds

    def _reauthenticate(self) -> Credentials:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open(self._token_file, "w") as token:
            token.write(creds.to_json())
        return creds

    def get_upcoming_events(
        self,
        max_results: int = 10,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
    ):
        token = self._creds.token
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {"Authorization": f"Bearer {token}"}
        time_min = time_min or dt.datetime.utcnow().isoformat() + "Z"
        time_max = (
            time_max
            or (dt.datetime.now() + dt.timedelta(days=3))
            .replace(hour=23, minute=59, second=0, microsecond=0)
            .isoformat()
            + "Z"
        )

        response = requests.get(
            url,
            headers=headers,
            params={
                "maxResults": max_results,
                "timeMin": time_min,
                "timeMax": time_max,
            },
        )
        if response.status_code == 200:
            events = response.json().get("items", [])
            if not events:
                print("No upcoming events found.")
            else:
                print("Upcoming events:")
                for event in events:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    print(f"{start} - {event['summary']}")
                return events
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def get_free_busy_agenda(
        self, time_min: Optional[str] = None, time_max: Optional[str] = None
    ):
        token = self._creds.token
        url = "https://www.googleapis.com/calendar/v3/freeBusy"
        headers = {"Authorization": f"Bearer {token}"}
        time_min = (
            time_min or dt.datetime.now(pytz.timezone("America/Bogota")).isoformat()
        )
        time_max = (
            time_max
            or (dt.datetime.now() + dt.timedelta(days=3))
            .replace(hour=23, minute=59, second=0, microsecond=0)
            .isoformat()
            + "Z"
        )

        response = requests.post(
            url,
            headers=headers,
            json={
                "timeMin": time_min,
                "timeMax": time_max,
                "timeZone": "America/Bogota",
                "items": [{"id": "primary"}],
            },
        )
        if response.status_code == 200:
            pprint(response.json())
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def add_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
    ):
        token = self._creds.token
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {"Authorization": f"Bearer {token}"}

        event_body = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "America/Bogota"},
            "end": {"dateTime": end_time, "timeZone": "America/Bogota"},
        }

        if description:
            event_body["description"] = description

        response = requests.post(url, headers=headers, json=event_body)

        if response.status_code == 200:
            print("Event added successfully.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
