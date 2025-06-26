import streamlit as st
import pandas as pd
import plotly.express as px
import json
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="부산시 전체 현황", layout="wide")
st.title("🚒 부산시 전체 현황")
st.write("\n\n\n\n")

# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv("train.csv", encoding="euc-kr", parse_dates=["tm"])
    df["address_gu"] = df["address_gu"].str.strip()
    return df

df = load_data()


# ─────────────────────────────────────────────────────────────
# 신고건수 지도 시각화
# ─────────────────────────────────────────────────────────────
st.subheader("📊 신고건수 현황")
# GeoJSON 로드
with open("busan_gu_geo.json", encoding="utf-8") as f:
    geojson = json.load(f)

# 신고건수 지도 시각화
# 날짜 선택
df['tm'] = pd.to_datetime(df['tm'])
selected_date = st.date_input("조회를 원하는 날짜를 선택하세요.", datetime.today())
selected_day = pd.to_datetime(selected_date)

# 동별 신고건수 집계
df["sub_address"] = df["sub_address"].str.strip()
df["address_city"] = df["address_city"].str.strip()
df["adm_nm"] = df["address_city"] + " " + df["address_gu"] + " " + df["sub_address"]
dong_counts = df[df["tm"] == selected_day].groupby("adm_nm")["call_count"].sum().reset_index()

# GeoJSON 속성 리스트로 전체 adm_nm 확보
geojson_dong_names = [f["properties"]["adm_nm"] for f in geojson["features"]]
all_dong_df = pd.DataFrame({"adm_nm": geojson_dong_names})

# 병합 → 신고건수 없는 동은 0으로
map_data = all_dong_df.merge(dong_counts, on="adm_nm", how="left")
map_data["call_count"] = map_data["call_count"].fillna(0)

col1, col2 = st.columns([2, 1])  # 지도:그래프 비율 2:1

with col1:
    # Choropleth Map
    fig = px.choropleth_mapbox(
        map_data,
        geojson=geojson,
        locations="adm_nm",
        color="call_count",
        featureidkey="properties.adm_nm",
        mapbox_style="carto-positron",
        center={"lat": 35.1796, "lon": 129.0756},
        zoom=11,
        opacity=0.6,
        title=f"{selected_date} 기준 동별 신고건수"
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 🚨 신고건수 Top 5")


    # TOP 5 동 추출
    top5 = dong_counts.sort_values(by="call_count", ascending=False).head(5)

    # 막대그래프
    bar_fig = px.bar(
        top5,
        x="call_count",
        y="adm_nm",
        orientation="h",
        color="adm_nm",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    bar_fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(autorange="reversed"),
        height=400,
        showlegend=False
    )

    st.plotly_chart(bar_fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# 신고유형(cat) 및 세부유형(sub_cat) 비율 원 그래프
# ─────────────────────────────────────────────────────────────

st.write("\n\n\n\n")
st.subheader("🔎 신고유형별 현황")

cat_day = df[df["tm"] == selected_day].copy()

# 전체 cat 비율 파이 차트
cat_counts = cat_day["cat"].value_counts().reset_index()
cat_counts.columns = ["cat", "count"]

st.markdown("##### 전체 신고 유형 분포")
fig_cat_all = px.pie(
    cat_counts, names="cat", values="count", hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_cat_all.update_traces(textinfo="percent+label")
fig_cat_all.update_layout(height=400)
st.plotly_chart(fig_cat_all, use_container_width=True)

# 각 cat별 sub_cat 비율
st.markdown("##### 세부 신고 유형 분포")

subcat_figs = []
for cat in cat_counts["cat"]:
    sub_df = cat_day[cat_day["cat"] == cat]
    sub_counts = sub_df["sub_cat"].value_counts().reset_index()
    sub_counts.columns = ["sub_cat", "count"]

    fig = px.pie(
        sub_counts, names="sub_cat", values="count", hole=0.5,
        title=f"🔹 {cat} 분포",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(title_font_size=14, height=200, margin=dict(t=30, b=0, l=0, r=0))
    subcat_figs.append(fig)

# 한 줄에 4개의 그래프 표시
cols = st.columns(4)
for i, fig in enumerate(subcat_figs):
    with cols[i % 4]:
        st.plotly_chart(fig, use_container_width=True)




# ─────────────────────────────────────────────────────────────
# 최근 일주일 간 기상 데이터
# ─────────────────────────────────────────────────────────────
st.write("\n\n\n\n")
st.subheader("📈 최근 7일 현황")

# 파생 변수 생성
df["ta_avg"] = (df["ta_min"] + df["ta_max"]) / 2
df["hm_avg"] = (df["hm_min"] + df["hm_max"]) / 2

# 선택 날짜 기준 이전 7일간 필터링
end_date = selected_day - pd.Timedelta(days=1)
start_date = selected_day - pd.Timedelta(days=7)
week_df = df[(df["tm"] >= start_date) & (df["tm"] <= end_date)]

# 평균 계산
weekly_mean = week_df[["ta_avg", "hm_avg", "rn_day", "ws_max"]].mean()
total_mean = df[["ta_avg", "hm_avg", "rn_day", "ws_max"]].mean()

# 비교 테이블 생성
diff_df = pd.DataFrame({
    "지표": ["평균 기온 (℃)", "평균 습도 (%)", "일 강수량 (mm)", "최대 풍속 (m/s)"],
    "최근 7일 평균": weekly_mean.values.round(2),
    "전체 평균": total_mean.values.round(2),
})

# 이상 여부 판단
diff_df["이상 여부"] = [
    "🔺 높음" if w > t else ("🔻 낮음" if w < t else "✅ 정상")
    for w, t in zip(weekly_mean, total_mean)
]

# 레이아웃: 왼쪽 그래프, 오른쪽 표
col1, col2 = st.columns([1.8, 1.2])

with col1:
    st.markdown("<br>", unsafe_allow_html=True)  # 👈 정렬 맞추는 핵심
    fig = px.bar(
        diff_df,
        x="지표",
        y=["최근 7일 평균", "전체 평균"],
        barmode="group",
        height=300,
        width = 200,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        yaxis_title="",
        xaxis_title="",
        showlegend=False  # 범례 제거
    )
    fig.update_yaxes(range=[0, diff_df[["최근 7일 평균", "전체 평균"]].values.max() * 1.3])
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.dataframe(diff_df.set_index("지표"), use_container_width=True)


# ▶ 이상 항목 문장 그룹화 출력
high_items = diff_df[diff_df["이상 여부"] == "🔺 높음"]["지표"].tolist()
low_items = diff_df[diff_df["이상 여부"] == "🔻 낮음"]["지표"].tolist()

if high_items:
    st.warning(f"📍 **{', '.join(high_items)}**가 전체 평균보다 **높습니다.**")
if low_items:
    st.info(f"📍 **{', '.join(low_items)}**가 전체 평균보다 **낮습니다.**")
