import streamlit as st
import datetime
import pickle
import os

# 데이터 저장/불러오기 함수
def save_data(data, filename="checklists.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(data, file)

def load_data(filename="checklists.pkl"):
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            return pickle.load(file)
    return {}

# 데이터 로드
if "checklists" not in st.session_state:
    st.session_state.checklists = load_data()

# 페이지 제목
st.title("📅 체크리스트 작성하기")

# 날짜 선택
selected_date = st.date_input("날짜선택", value=datetime.date.today())

# 날짜별 체크리스트 초기화
if selected_date not in st.session_state.checklists:
    st.session_state.checklists[selected_date] = []

# 새 작업 추가
st.text_input(
    "할 일 입력",
    key="new_task",
    on_change=lambda: st.session_state.checklists[selected_date].append({
        "task": st.session_state.new_task,
        "done": False
    })
)

# 작업 리스트 표시
st.write(f"### {selected_date} TODO List")
for i, task in enumerate(st.session_state.checklists[selected_date]):
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.write(f"- {task['task']}")
    with col2:
        if st.checkbox("완료", key=f"done_{selected_date}_{i}", value=task["done"]):
            st.session_state.checklists[selected_date][i]["done"] = True



# 저장 버튼
if st.button("저장"):
    save_data(st.session_state.checklists)
    st.success("할 일을 완료했습니다! 수고하셨습니다:)")


# 완료된 작업 필터링
if st.button("삭제"):
    st.session_state.checklists[selected_date] = [
        task for task in st.session_state.checklists[selected_date] if not task["done"]
    ]
    save_data(st.session_state.checklists)

