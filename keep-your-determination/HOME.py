import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="centered"
)

# 스타일 추가
st.markdown("""
    <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #003366;
            text-align: center;
            margin-top: 20px;
        }
        .sub-title {
            font-size: 1.2rem;
            color: #666666;
            text-align: center;
            margin-bottom: 30px;
        }
        .button-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 40px;
        }
        .button {
            display: inline-block;
            padding: 15px 30px;
            font-size: 1.2rem;
            text-align: center;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.3s ease;
            cursor: pointer;
        }
        .button:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown('<div class="main-title">📘 작심지킴</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">자격증 공부 관리를 쉽고 체계적으로, 원하시는 기능을 선택하여 이용해보세요!</div>', unsafe_allow_html=True)

# 버튼 섹션
col1, col2, col3, col4 = st.columns(4)

# JavaScript로 페이지 이동
def navigate_to(url):
    st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={url}">
    """, unsafe_allow_html=True)

with col1:
    if st.button("📅 캘린더"):
        navigate_to("https://keepyour-determination.streamlit.app/%EC%BA%98%EB%A6%B0%EB%8D%94")  # 캘린더 페이지로 이동


with col2:
    if st.button("✅ 체크리스트 "):
        navigate_to("https://keepyour-determination.streamlit.app/%EC%B2%B4%ED%81%AC%EB%A6%AC%EC%8A%A4%ED%8A%B8_%EC%9E%91%EC%84%B1")  # 체크리스트 이동

with col3:
    if st.button("🤖 챗봇상담"):
        navigate_to("https://keepyour-determination.streamlit.app/%EC%B1%97%EB%B4%87_%EC%83%81%EB%8B%B4")  # 챗봇 페이지로 이동


with col4:
    if st.button("📕이용방법"):
        navigate_to("https://keepyour-determination.streamlit.app/%EC%9D%B4%EC%9A%A9%EB%B0%A9%EB%B2%95")  # 이용방법 이동
      
