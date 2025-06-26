import streamlit as st
import pandas as pd
import plotly.express as px
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import joblib
from sklearn.base import BaseEstimator, TransformerMixin



st.set_page_config(page_title="신고건수 조회", layout="wide")
st.title("🚒 신고건수 조회")
st.write("\n\n\n\n")


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.rn_bins = [-0.1, 0, 10, 30, 70, 1000]
        self.rn_labels = ['없음', '약한 비', '보통 비', '강한 비', '매우 강한 비']

    def assign_region_group(self, gu):
        coastal = ['해운대구', '수영구', '영도구', '중구', '동구', '서구', '남구']
        urban = ['부산진구', '동래구', '연제구']
        mountain = ['금정구', '기장군']
        lowland = ['강서구', '북구', '사상구', '사하구']
        if gu in coastal:
            return '해안지역'
        elif gu in urban:
            return '내륙 도심'
        elif gu in mountain:
            return '산지/고지대'
        elif gu in lowland:
            return '하천/저지대'
        else:
            return '기타'

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X['tm'] = pd.to_datetime(X['tm'])
        X['year'] = X['tm'].dt.year
        X['month'] = X['tm'].dt.month
        X['day'] = X['tm'].dt.day
        X['weekday'] = X['tm'].dt.dayofweek
        X['ws_diff'] = X['ws_ins_max'] - X['ws_max']
        X['wind_mean'] = (X['ws_ins_max'] + X['ws_max']) / 2
        X['hm_mean'] = (X['hm_min'] + X['hm_max']) / 2
        X['rn_day'] = X['rn_day'].apply(lambda x: 0 if x < 0 else x)
        X['rn_day_bin'] = pd.cut(X['rn_day'], bins=self.rn_bins, labels=self.rn_labels)
        X['region_group'] = X['address_gu'].apply(self.assign_region_group)
        return X.drop(columns=['tm'])

# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv("train.csv", encoding="euc-kr", parse_dates=["tm"])
    df["address_gu"] = df["address_gu"].str.strip()
    return df

data = load_data()

# 파생변수
data["ta_avg"] = (data["ta_min"] + data["ta_max"]) / 2
data["hm_avg"] = (data["hm_min"] + data["hm_max"]) / 2



# ─────────────────────────────────────────────────────────────
# 신고건수 현황
# ─────────────────────────────────────────────────────────────
st.subheader("📊 신고건수 현황")

# 날짜 & 구 선택
data['tm'] = pd.to_datetime(data['tm'])
col1, col2 = st.columns([1,1])
with col1:
    selected_date = st.date_input("조회를 원하는 날짜를 선택하세요.", datetime.today())
with col2:
    selected_gu = st.selectbox("조회를 원하는 구를 선택하세요.", sorted(data['address_gu'].unique()))
filtered = data[(data['tm'].dt.date == selected_date) & (data['address_gu'] == selected_gu)]

if filtered.empty:
    st.warning("선택한 날짜와 구에 해당하는 데이터가 없습니다.")
else:
    st.markdown(f"#### {selected_date} {selected_gu}")
    col1, col2, col3, col4, col5  = st.columns(5)
    col1.metric("평균 기온 (°C)", round(filtered['ta_avg'].mean(), 1))
    col2.metric("강수량 (mm)", round(filtered['rn_day'].mean(), 1))
    col3.metric("평균 습도 (%)", round(filtered['hm_avg'].mean(), 1))
    col4.metric("최대 풍속 (m/s)", round(filtered['ws_max'].mean(), 1))
    col5.metric("신고건수 합계", int(filtered['call_count'].sum()))

st.markdown("#### 동별 신고 현황")
fig = px.bar(filtered, x='sub_address', y='call_count', color='cat',
             labels={'call_count': '신고건수', 'sub_address': '동'},
             color_discrete_sequence=px.colors.qualitative.Set2)
st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# 기상 데이터 트렌드
# ─────────────────────────────────────────────────────────────
st.write("\n\n\n\n")
st.subheader("📈 날씨 변화 추이")
date_range = st.radio("원하는 기간을 선택하세요.", options=["1주일", "1개월"], horizontal=True)

# 기간 설정
days = 7 if date_range == "1주일" else 30
selected_date = pd.to_datetime(selected_date)
start_date = pd.to_datetime(selected_date - timedelta(days=days))
trend_data = data[(data["tm"] >= start_date) & (data["tm"] <= selected_date) & (data["address_gu"] == selected_gu)]

if trend_data.empty:
    st.warning("해당 기간에 데이터가 없습니다.")
else:
    st.subheader(f"📊 {selected_gu} 최근 {date_range} 기상 지표 변화 추이")

    # 🔸 한 줄에 4개의 그래프로 시각화
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fig1 = px.line(trend_data, x='tm', y='ta_avg', markers=True,
                       labels={'tm': '날짜', 'ta_avg': '평균 기온 (℃)'},
                       color_discrete_sequence=['#1E88E5'])
        fig1.update_layout(height=250, margin=dict(t=30, b=30), xaxis_title=None)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.line(trend_data, x='tm', y='rn_day', markers=True,
                       labels={'tm': '날짜', 'rn_day': '강수량 (mm)'},
                       color_discrete_sequence=['#F4511E'])
        fig2.update_layout(height=250, margin=dict(t=30, b=30), xaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = px.line(trend_data, x='tm', y='hm_avg', markers=True,
                       labels={'tm': '날짜', 'hm_avg': '평균 습도 (%)'},
                       color_discrete_sequence=['#43A047'])
        fig3.update_layout(height=250, margin=dict(t=30, b=30), xaxis_title=None)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.line(trend_data, x='tm', y='ws_max', markers=True,
                       labels={'tm': '날짜', 'ws_max': '최대 풍속 (m/s)'},
                       color_discrete_sequence=['#8E24AA'])
        fig4.update_layout(height=250, margin=dict(t=30, b=30), xaxis_title=None)
        st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# 신고건수 예측
# ─────────────────────────────────────────────────────────────
st.write("\n\n\n\n")
st.subheader("🚨 신고건수 예측")

# 모델 불러오기
@st.cache_resource
def load_model():
    return joblib.load("model_pipeline.pkl")

model = load_model()


# 사용자 입력
st.markdown("날짜, 지역, 기상 정보를 입력하면 신고건수를 예측합니다.")
col1, col2 = st.columns(2)
with col1:
    tm = st.date_input("날짜 선택", value=datetime.today())
    gu_list = sorted(data['address_gu'].unique())
    address_gu = st.selectbox("구 선택", gu_list)
    dong_list = sorted(data[data['address_gu'] == address_gu]['sub_address'].unique())
    sub_address = st.selectbox("동 선택", dong_list)
    ta_max = st.number_input("최고 기온 (℃)", value=28.5)
    ta_min = st.number_input("최저 기온 (℃)", value=20.0)

with col2:
    hm_max = st.number_input("최고 습도 (%)", value=85)
    hm_min = st.number_input("최저 습도 (%)", value=60)
    ws_max = st.number_input("최대 풍속 (m/s)", value=4.2)
    ws_ins_max = st.number_input("순간 최대 풍속 (m/s)", value=6.5)
    rn_day = st.number_input("일 강수량 (mm)", value=12.0)

# 입력 데이터 구성
input_df = pd.DataFrame([{
    "tm": pd.to_datetime(tm),
    "address_gu": address_gu,
    "sub_address": sub_address,
    "ta_max": ta_max,
    "ta_min": ta_min,
    "ta_max_min" : ta_max - ta_min,
    "hm_max": hm_max,
    "hm_min": hm_min,
    "ws_max": ws_max,
    "ws_ins_max": ws_ins_max,
    "rn_day": rn_day
}])

# 예측 실행
st.subheader("\n\n")
if st.button("📊 신고건수 예측하기"):
    try:
        pred = model.predict(input_df)[0]
        st.success(f"🚨 예상 신고건수: **{round(pred)}건**")
    except Exception as e:
        st.error(f"예측 중 오류 발생: {e}")
