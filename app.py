import streamlit as st
import streamlit as st

st.set_page_config(page_title="LOGIS:COPE", page_icon="🏠", layout="wide")

# CSS
st.markdown("""
    <style>
    .main { background-color: #f2f2f2; }
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        margin-top: 100px;
        margin-bottom: 30px;
    }
   .menu-button {
    display: block;
    width: 220px;
    padding: 18px 0;
    margin: 20px auto;
    background-color: #143d66;
    color: white !important;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    border-radius: 15px;
    text-decoration: none;  /* 기본 밑줄 제거 */
    transition: background-color 0.3s ease;
}
    .menu-button:hover {
    background-color: #1b4e85;
    color: white;
    text-decoration: none !important;  /* hover 시에도 밑줄 없음 */
    cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# 제목
st.markdown("<div class='main-title'>LOGIS:COPE</div>", unsafe_allow_html=True)


# 또는 HTML 링크 버튼처럼 보이게 만들고 싶다면 아래 사용
st.markdown("""
<a href="?page=1_1️⃣_Overview" class="menu-button">Overview</a>
<a href="?page=report" class="menu-button">Report</a>
""", unsafe_allow_html=True)
