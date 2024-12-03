import streamlit as st
import openai

# OpenAI API 키 설정
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OpenAI API 키가 설정되지 않았습니다. secrets.toml 파일을 확인하세요.")
    st.stop()

# Streamlit 세션 상태 초기화
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Streamlit UI 설정
st.set_page_config(page_title="Chatbot", page_icon="🤖")
st.markdown("# 🤖챗봇 상담하기")

# 기존 메시지 렌더링
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("Ask me anything!"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # OpenAI API 호출
    try:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()  # 빈 메시지 박스 생성
            full_response = ""  # 전체 응답 초기화

            response = openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,  # 스트리밍 활성화
            )

            for chunk in response:
                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                full_response += delta
                message_placeholder.markdown(full_response + "▌")  # 스트리밍 중 표시

            message_placeholder.markdown(full_response)  # 최종 응답 표시
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
