import os
import json
import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from datetime import datetime, date
import streamlit.components.v1 as components
import google.auth.transport.requests

# Streamlit 설정 (반드시 최상단에 위치)
st.set_page_config(page_title="Calendar", page_icon="📅", layout="centered")
st.title("📅 스케줄 관리 페이지")

# 클라이언트 비밀 파일 생성
CLIENT_SECRET_FILE = "client_secret.json"
if "google_client_secret" in st.secrets:
    # Streamlit Secrets에서 클라이언트 비밀 정보를 가져와 파일로 저장
    client_secret_data = {
        "installed": {
            "client_id": st.secrets["google_client_secret"]["client_id"],
            "client_secret": st.secrets["google_client_secret"]["client_secret"],
            "auth_uri": st.secrets["google_client_secret"]["auth_uri"],
            "token_uri": st.secrets["google_client_secret"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_client_secret"]["auth_provider_x509_cert_url"],
            "redirect_uris": st.secrets["google_client_secret"]["redirect_uris"],
        }
    }
    with open(CLIENT_SECRET_FILE, "w") as f:
        f.write(json.dumps(client_secret_data))
else:
    st.error("클라이언트 비밀 정보가 Streamlit Secrets에 설정되어 있지 않습니다.")

# 자격 증명 파일 이름
CREDENTIALS_FILE = "google_credentials.json"

# 자격 증명 관련 함수
def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
    }

def save_credentials_to_file(creds):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds_to_dict(creds), f)

def load_credentials_from_file():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                creds_dict = json.load(f)
                creds = google.oauth2.credentials.Credentials(**creds_dict)
                return creds
        except Exception as e:
            st.error(f"자격 증명 파일 로드 중 오류: {e}")
            os.remove(CREDENTIALS_FILE)
    return None

def refresh_credentials(creds):
    if creds and creds.expired and creds.refresh_token:
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        save_credentials_to_file(creds)
    return creds

def logout():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)
        st.success("성공적으로 로그아웃되었습니다.")
        st.experimental_rerun()

def login():
    if not os.path.exists(CLIENT_SECRET_FILE):
        st.error("클라이언트 비밀 파일(client_secret.json)을 찾을 수 없습니다.")
        return None

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    creds = flow.run_local_server(port=0)
    save_credentials_to_file(creds)
    return creds

# 캘린더 일정 관련 함수
def add_event(service, summary, location, description, start_time, end_time, time_zone='Asia/Seoul'):
    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': time_zone,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': time_zone,
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event

def fetch_events(service):
    now = datetime.utcnow().isoformat() + 'Z'
    try:
        events_result = service.events().list(
            calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except google.auth.exceptions.RefreshError:
        st.error("인증이 만료되었습니다. 다시 로그인해주세요.")
        logout()
        return []
    except Exception as e:
        st.error(f"이벤트를 불러오는 중 오류가 발생했습니다: {e}")
        return []

def render_fullcalendar(events, calendar_height=600):
    events_json = [
        {
            'title': event.get('summary', '제목 없음'),
            'start': event['start'].get('dateTime', event['start'].get('date', ''))
        }
        for event in events
    ]
    calendar_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.9.0/main.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.9.0/main.min.js'></script>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            events: {events_json}
          }});
          calendar.render();
        }});
      </script>
    </head>
    <body>
      <div id='calendar'></div>
    </body>
    </html>
    """
    components.html(calendar_html, height=calendar_height)

# Streamlit Session State로 events 관리
if "events" not in st.session_state:
    st.session_state.events = []

# 로그인 상태 확인
creds = load_credentials_from_file()
if creds:
    creds = refresh_credentials(creds)
    service = build('calendar', 'v3', credentials=creds)
    st.success("로그인 상태가 유지되었습니다.")
    if st.button("로그아웃"):
        logout()
else:
    if st.button("로그인"):
        creds = login()
        if creds:
            service = build('calendar', 'v3', credentials=creds)

# 캘린더 일정 렌더링
if creds:
    try:
        st.session_state.events = fetch_events(service)
    except Exception as e:
        st.error(f"이벤트를 불러오는 중 문제가 발생했습니다: {e}")
    render_fullcalendar(st.session_state.events)
