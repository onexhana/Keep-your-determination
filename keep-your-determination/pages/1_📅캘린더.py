import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from datetime import datetime, date, time
import streamlit.components.v1 as components
import os
import json
import google.auth.transport.requests

# 자격 증명 파일 이름
CREDENTIALS_FILE = "google_credentials.json"

# Streamlit 설정
st.set_page_config(page_title="Calendar", page_icon="📅", layout="centered")
st.title("📅 스케줄 관리 페이지")

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
            creds = google.oauth2.credentials.Credentials(**creds_dict)
            return creds
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
        st.write('<script>window.location.reload()</script>', unsafe_allow_html=True)

def login():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        "C:\chat-gpt-prg\keep-your-determination\client_secret_529596907303-j96e1i1hsf6mmtsj5nas3t110v4fvpup.apps.googleusercontent.com.json", 
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
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    return events_result.get('items', [])

def render_fullcalendar(events, calendar_height=600):
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
        service = build('calendar', 'v3', credentials=creds)

# 캘린더 일정 렌더링
if creds:
    events = fetch_events(service)
    render_fullcalendar(events)

# 일정 추가 UI
if creds:
    with st.expander("새로운 일정 추가"):
        event_summary = st.text_input("일정 제목", "")
        event_location = st.text_input("일정 장소", "")
        event_description = st.text_area("일정 설명", "")
        
        start_date = st.date_input("시작 날짜", value=date.today())
        start_time_str = st.text_input("시작 시간 (HH:MM)", value=datetime.now().strftime("%H:%M"))
        end_date = st.date_input("종료 날짜", value=date.today())
        end_time_str = st.text_input("종료 시간 (HH:MM)", value=(datetime.now().replace(hour=(datetime.now().hour + 1))).strftime("%H:%M"))

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요.")
            start_time, end_time = None, None

        if start_time and end_time:
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            if st.button("일정 추가"):
                created_event = add_event(service, event_summary, event_location, event_description, start_datetime, end_datetime)
                st.success(f"일정이 성공적으로 추가되었습니다! 시작: {start_datetime}, 종료: {end_datetime}")
                events = fetch_events(service)
                render_fullcalendar(events)


# 기존 일정 수정 UI
with st.expander("기존 일정 수정"):
    if events:
        selected_event = st.selectbox(
            '수정할 일정 선택',
            events,
            format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음',
            key="edit_event_select"
        )

        new_title = st.text_input('새로운 일정 제목', selected_event['summary'], key="edit_event_title")

        # 시작 날짜와 시간
        start_datetime_str = selected_event['start'].get('dateTime', selected_event['start'].get('date'))
        start_datetime = datetime.fromisoformat(start_datetime_str)
        start_date = st.date_input("수정 시작 날짜", value=start_datetime.date(), key="edit_start_date")
        start_time_str = st.text_input("수정 시작 시간 (HH:MM)", value=start_datetime.strftime("%H:%M"), key="edit_start_time")

        # 종료 날짜와 시간
        end_datetime_str = selected_event['end'].get('dateTime', selected_event['end'].get('date'))
        end_datetime = datetime.fromisoformat(end_datetime_str)
        end_date = st.date_input("수정 종료 날짜", value=end_datetime.date(), key="edit_end_date")
        end_time_str = st.text_input("수정 종료 시간 (HH:MM)", value=end_datetime.strftime("%H:%M"), key="edit_end_time")

        try:
            # 입력된 시간 변환
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요.")
            start_time, end_time = None, None

        if start_time and end_time:
            new_start_datetime = datetime.combine(start_date, start_time)
            new_end_datetime = datetime.combine(end_date, end_time)

            if st.button("일정 수정"):
                # 수정된 일정 생성
                updated_event = {
                    'summary': new_title,
                    'start': {
                        'dateTime': new_start_datetime.isoformat(),
                        'timeZone': 'Asia/Seoul',
                    },
                    'end': {
                        'dateTime': new_end_datetime.isoformat(),
                        'timeZone': 'Asia/Seoul',
                    },
                }
                service.events().update(calendarId='primary', eventId=selected_event['id'], body=updated_event).execute()
                st.success('일정가 수정되었습니다.')

                # 최신 일정 목록 다시 불러오기
                events = fetch_events(service)
                render_fullcalendar(events)
    else:
        st.warning("수정할 일정가 없습니다.")


# Streamlit Session State로 events 관리
if "events" not in st.session_state:
    st.session_state.events = []  # 초기화

# 일정 삭제 UI
with st.expander("기존 일정 삭제"):
    if creds:  # 로그인 여부 확인
        try:
            # 이벤트 목록 가져오기
            st.session_state.events = fetch_events(service)
        except Exception as e:
            st.error(f"이벤트를 불러오는 중 문제가 발생했습니다: {e}")
            st.session_state.events = []  # 오류 발생 시 빈 리스트로 초기화

        if st.session_state.events:  # 가져온 이벤트가 있을 경우
            selected_event = st.selectbox(
                '삭제할 이벤트 선택',
                st.session_state.events,
                format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음',
                key="delete_event_select"
            )

            if st.button("이벤트 삭제"):
                try:
                    # 선택한 이벤트 삭제
                    service.events().delete(calendarId='primary', eventId=selected_event['id']).execute()
                    st.success(f"'{selected_event['summary']}' 이벤트가 삭제되었습니다.")

                    # 최신 이벤트 목록 다시 가져오기
                    st.session_state.events = fetch_events(service)
                    render_fullcalendar(st.session_state.events)
                except Exception as e:
                    st.error(f"이벤트 삭제 중 오류가 발생했습니다: {e}")
        else:
            st.warning("삭제할 이벤트가 없습니다.")
    else:
        st.warning("로그인이 필요합니다. 먼저 로그인하세요.")
