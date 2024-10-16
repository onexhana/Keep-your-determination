import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import datetime
import streamlit.components.v1 as components
import os
import json
import google.auth.transport.requests

CREDENTIALS_FILE = "google_credentials.json"  # 자격 증명 파일 이름

# 자격 증명(토큰)을 딕셔너리로 변환
def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

# 자격 증명 파일로 저장
def save_credentials_to_file(creds):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds_to_dict(creds), f)

# 자격 증명을 파일에서 불러오기
def load_credentials_from_file():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds_dict = json.load(f)
            creds = google.oauth2.credentials.Credentials(**creds_dict)
            return creds
    return None

# 자격 증명 갱신 함수
def refresh_credentials(creds):
    if creds and creds.expired and creds.refresh_token:
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        save_credentials_to_file(creds)  # 갱신된 자격 증명 다시 저장
    return creds

# 로그아웃 함수: 파일에서 자격 증명 삭제
def logout():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)
        st.success("성공적으로 로그아웃되었습니다.")
        st.experimental_rerun()  # 로그아웃 후 페이지를 새로고침

# 구글 로그인 함수
def login():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        "C:\chat-gpt-prg\keep-your-determination\client_secret_529596907303-g8ml5thjfis3grspuqm01sc7jjjr18f9.apps.googleusercontent.com.json", 
        scopes=['https://www.googleapis.com/auth/calendar'])
    creds = flow.run_local_server(port=0)
    
    save_credentials_to_file(creds)  # 로그인 후 자격 증명을 파일로 저장
    return creds

# 일정 추가 함수
def add_event(service, event_summary, event_location, event_description, start_time, end_time, time_zone='Asia/Seoul'):
    event = {
        'summary': event_summary,
        'location': event_location,
        'description': event_description,
        'start': {
            'dateTime': start_time,
            'timeZone': time_zone,  # 한국 시간대로 설정
        },
        'end': {
            'dateTime': end_time,
            'timeZone': time_zone,  # 한국 시간대로 설정
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event

# 일정 불러오기 함수
def fetch_events(service):
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

# FullCalendar를 사용한 캘린더 UI 함수
def render_fullcalendar(events, calendar_height=600):
    events_json = [{'title': event['summary'], 'start': event['start'].get('dateTime', event['start'].get('date'))} for event in events]
    
    # CSS 스타일을 Streamlit에 삽입 (글씨체와 크기 조정)
    st.markdown("""
        <style>
        .fc {
            font-family: 'Arial', sans-serif;
            font-size: 16px;
        }
        </style>
    """, unsafe_allow_html=True)

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

# 페이지 설정 및 제목 설정
st.set_page_config(page_title="캘린더", page_icon="📅")  # 페이지 타이틀과 아이콘 설정
st.title('캘린더 페이지')  # 페이지 제목

# 자격 증명 로드 및 로그인 상태 유지
creds = load_credentials_from_file()
if creds:
    creds = refresh_credentials(creds)  # 만료된 자격 증명 갱신
    service = build('calendar', 'v3', credentials=creds)
    st.success("로그인 상태가 유지되었습니다.")
    if st.button('로그아웃'):
        logout()  # 로그아웃 기능 추가
else:
    if st.button('로그인'):
        creds = login()
        service = build('calendar', 'v3', credentials=creds)

# 이벤트 가져오기 및 캘린더 렌더링
if creds:
    events = fetch_events(service)
    calendar_height = 600  # 기본 캘린더 높이 설정
    render_fullcalendar(events, calendar_height)

# 일정 수정 UI
with st.expander("기존 일정 수정"):
    if events:
        selected_event = st.selectbox('수정할 이벤트 선택', events, format_func=lambda e: e['summary'] if 'summary' in e else '제목 없음')
        new_title = st.text_input('새로운 이벤트 제목', selected_event['summary'])
        if st.button("이벤트 수정"):
            update_event(service, selected_event['id'], new_title)
            st.success('이벤트가 수정되었습니다.')
            events = fetch_events(service)  # 수정된 후 최신 이벤트 목록을 다시 불러오기
            render_fullcalendar(events, calendar_height)  # 수정된 내용 반영하여 다시 렌더링
    else:
        st.warning("수정할 이벤트가 없습니다.")

# 일정 추가 UI
with st.expander("새로운 일정 추가"):
    event_summary = st.text_input("일정 제목", "")
    event_location = st.text_input("일정 장소", "")
    event_description = st.text_area("일정 설명", "")
    start_time = st.text_input("시작 시간 (YYYY-MM-DDTHH:MM:SS)", "2024-10-08T10:00:00")
    end_time = st.text_input("종료 시간 (YYYY-MM-DDTHH:MM:SS)", "2024-10-08T11:00:00")
    time_zone = 'Asia/Seoul'  # 한국 시간대 기본 적용

    if st.button("일정 추가"):
        created_event = add_event(service, event_summary, event_location, event_description, start_time, end_time, time_zone)
        st.success(f"일정이 성공적으로 추가되었습니다: {created_event.get('htmlLink')}")
        events.append(created_event)  # 추가한 이벤트를 바로 반영
        render_fullcalendar(events, calendar_height)  # 추가된 내용 반영하여 다시 렌더링
