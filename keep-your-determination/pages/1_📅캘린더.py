import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, date
import streamlit.components.v1 as components
import os
from google.auth.transport.requests import Request

# Google Client Secret 파일 생성
def create_client_secret_file():
    client_secret_content = st.secrets["google"]["client_secret"]
    client_secret_path = "client_secret.json"
    with open(client_secret_path, "w") as f:
        f.write(client_secret_content)
    return client_secret_path

# Google Credentials 파일 생성
def create_credentials_file():
    credentials_content = st.secrets["google"]["credentials"]
    credentials_path = "google_credentials.json"
    with open(credentials_path, "w") as f:
        f.write(credentials_content)
    return credentials_path

# 동적으로 파일 생성
CLIENT_SECRET_FILE = create_client_secret_file()
CREDENTIALS_FILE = create_credentials_file()

# Streamlit 설정
st.set_page_config(page_title="캘린더", page_icon="📅", layout="centered")
st.title("📅 Google Calendar 관리")

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
        with open(CREDENTIALS_FILE, "r") as f:
            creds_dict = json.load(f)
            return Credentials(**creds_dict)
    return None

def refresh_credentials(creds):
    try:
        if creds and creds.expired and creds.refresh_token:
            request = Request()
            creds.refresh(request)
            save_credentials_to_file(creds)
    except Exception as e:
        st.error(f"자격 증명을 새로고침하는 중 오류 발생: {e}")
    return creds

def logout():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)
        st.success("성공적으로 로그아웃되었습니다.")
        st.experimental_rerun()

def login():
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        creds = flow.run_local_server(port=0)
        save_credentials_to_file(creds)
        return creds
    except Exception as e:
        st.error(f"로그인 중 오류 발생: {e}")
        return None

# 캘린더 일정 관련 함수
def add_event(service, summary, location, description, start_time, end_time, time_zone='Asia/Seoul'):
    try:
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
        return service.events().insert(calendarId='primary', body=event).execute()
    except Exception as e:
        st.error(f"일정 추가 중 오류 발생: {e}")

def update_event(service, event_id, summary, start_time, end_time, time_zone='Asia/Seoul'):
    try:
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': time_zone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': time_zone,
            },
        }
        return service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    except Exception as e:
        st.error(f"일정 수정 중 오류 발생: {e}")

def delete_event(service, event_id):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        st.error(f"일정 삭제 중 오류 발생: {e}")

def fetch_events(service):
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        return events_result.get('items', [])
    except Exception as e:
        st.error(f"이벤트를 가져오는 중 오류 발생: {e}")
        return []

def render_fullcalendar(events, calendar_height=600):
    try:
        events_json = [{'title': event['summary'], 'start': event['start'].get('dateTime', event['start'].get('date'))} for event in events]
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
    except Exception as e:
        st.error(f"캘린더 렌더링 중 오류 발생: {e}")

# 로그인 상태 확인
creds = load_credentials_from_file()
if creds:
    creds = refresh_credentials(creds)
    if creds:
        service = build('calendar', 'v3', credentials=creds)
        st.success("로그인 상태 유지 중")
        if st.button("로그아웃"):
            logout()
else:
    service = None
    if st.button("로그인"):
        creds = login()
        if creds:
            service = build('calendar', 'v3', credentials=creds)

# 일정 추가/수정/삭제 UI
if service:
    events = fetch_events(service)
    render_fullcalendar(events)
    
    # 새 일정 추가
    with st.expander("새 일정 추가"):
        event_summary = st.text_input("일정 제목", "")
        event_location = st.text_input("일정 장소", "")
        event_description = st.text_area("일정 설명", "")
        start_date = st.date_input("시작 날짜", value=date.today())
        start_time = st.text_input("시작 시간 (HH:MM)", value="09:00")
        end_date = st.date_input("종료 날짜", value=date.today())
        end_time = st.text_input("종료 시간 (HH:MM)", value="10:00")

        if st.button("일정 추가"):
            try:
                start_datetime = datetime.combine(start_date, datetime.strptime(start_time, "%H:%M").time())
                end_datetime = datetime.combine(end_date, datetime.strptime(end_time, "%H:%M").time())
                add_event(service, event_summary, event_location, event_description, start_datetime, end_datetime)
                st.success("일정이 추가되었습니다.")
                events = fetch_events(service)
                render_fullcalendar(events)
            except Exception as e:
                st.error(f"일정 추가 중 오류 발생: {e}")

    # 일정 수정
    with st.expander("기존 일정 수정"):
        if events:
            selected_event = st.selectbox(
                "수정할 이벤트 선택",
                events,
                format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음'
            )
            new_title = st.text_input("새로운 제목", selected_event['summary'])
            new_start_time = st.text_input("새로운 시작 시간 (HH:MM)", "09:00")
            new_end_time = st.text_input("새로운 종료 시간 (HH:MM)", "10:00")
            if st.button("일정 수정"):
                try:
                    start_time = datetime.strptime(new_start_time, "%H:%M")
                    end_time = datetime.strptime(new_end_time, "%H:%M")
                    update_event(service, selected_event['id'], new_title, start_time, end_time)
                    st.success("일정이 수정되었습니다.")
                    events = fetch_events(service)
                    render_fullcalendar(events)
                except Exception as e:
                    st.error(f"일정 수정 중 오류 발생: {e}")
        else:
            st.warning("수정 가능한 일정이 없습니다.")

    # 일정 삭제
    with st.expander("기존 일정 삭제"):
        if events:
            selected_event = st.selectbox(
                "삭제할 이벤트 선택",
                events,
                format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음'
            )
            if st.button("이벤트 삭제"):
                try:
                    delete_event(service, selected_event['id'])
                    st.success("일정이 삭제되었습니다.")
                    events = fetch_events(service)
                    render_fullcalendar(events)
                except Exception as e:
                    st.error(f"일정 삭제 중 오류 발생: {e}")
        else:
            st.warning("삭제 가능한 일정이 없습니다.")
