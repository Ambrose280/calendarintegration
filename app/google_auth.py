import os
import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'openid', 
    'https://www.googleapis.com/auth/userinfo.email', 
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.events'
]
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
if not REDIRECT_URI:
    raise ValueError("GOOGLE_REDIRECT_URI environment variable is required")

def get_google_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
        
    return {
        "web": {
            "client_id": client_id,
            "project_id": "schedulerapp",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [REDIRECT_URI]
        }
    }

def get_google_auth_flow():
    config = get_google_client_config()
    if not config:
        return None
        
    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow

def create_google_calendar_event(credentials_dict, booking):
    credentials = Credentials(**credentials_dict)
    service = build('calendar', 'v3', credentials=credentials)
    
    event = {
      'summary': f'Meeting with {booking.client_name}',
      'description': 'Meeting booked via our system.',
      'start': {
        'dateTime': booking.start_time.isoformat() + 'Z',
        'timeZone': 'UTC',
      },
      'end': {
        'dateTime': booking.end_time.isoformat() + 'Z',
        'timeZone': 'UTC',
      },
      'attendees': [
        {'email': booking.client_email},
      ],
      'reminders': {
        'useDefault': False,
        'overrides': [
          {'method': 'email', 'minutes': 24 * 60},
          {'method': 'popup', 'minutes': 10},
        ],
      },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('id')
