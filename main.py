import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온을 숫자로 변환
    df["평균기온"] = pd.to_numeric(
        df["평균기온"],
        errors="coerce"
    )

    # 날짜 또는 평균기온이 없는 행 제거
    df = df.dropna(subset=["날짜", "평균기온"])

    return df


# -----------------------------
# 페이지 제목
# -----------------------------
st.title("🌡️ 서울의 100년 기온 변화")
st.markdown(
    "서울의 일별 기온 데이터를 바탕으로 **연평균 기온의 변화**를 살펴봅니다."
)

try:
    df = load_data()

    # -----------------------------
    # 연도 추출
    # -----------------------------
    df["연도"] = df["날짜"].dt.year

    # 연도별 평균기온 계산
    yearly = (
        df.groupby("연도")["평균기온"]
        .mean()
        .reset_index()
    )

    yearly.columns = ["연도", "연평균기온"]

    # 소수점 정리
    yearly["연평균기온"] = yearly["연평균기온"].round(2)

    # -----------------------------
    # 완전한 연도만 사용
    # -----------------------------
    # 각 연도의 데이터 개수가 충분한지 확인하기 위해
    # 해당 연도에 300일 이상 자료가 있는 경우를 완전한 연도로 간주
    day_count = (
        df.groupby("연도")["날짜"]
        .count()
        .reset_index(name="자료일수")
    )

    yearly = yearly.merge(day_count, on="연도")

    complete_years = yearly[yearly["자료일수"] >= 300].copy()

    # 가장 최근 100개 연도 선택
    last_100 = complete_years.tail(100).copy()

    # -----------------------------
    # 기본 정보
    # -----------------------------
    if len(last_100) == 0:
        st.error("분석할 기온 데이터가 없습니다.")
        st.stop()

    start_year = int(last_100["연도"].min())
    end_year = int(last_100["연도"].max())

    first_temp = float(last_100.iloc[0]["연평균기온"])
    last_temp = float(last_100.iloc[-1]["연평균기온"])
    change = last_temp - first_temp

    # -----------------------------
    # 상단 요약
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "분석 기간",
            f"{start_year}~{end_year}년"
        )

    with col2:
        st.metric(
            f"{start_year}년 연평균",
            f"{first_temp:.1f} °C"
        )

    with col3:
        st.metric(
            f"{end_year}년 연평균",
            f"{last_temp:.1f} °C",
            delta=f"{change:+.1f} °C"
        )

    st.divider()

    # -----------------------------
    # 그래프
    # -----------------------------
    fig = go.Figure()

    # 연평균 기온 선
    fig.add_trace(
        go.Scatter(
            x=last_100["연도"],
            y=last_100["연평균기온"],
            mode="lines+markers",
            name="연평균 기온",
            line=dict(
                width=3
            ),
            marker=dict(
                size=5
            ),
            hovertemplate=
                "<b>%{x}년</b><br>" +
                "연평균 기온: %{y:.1f} °C" +
                "<extra></extra>"
        )
    )

    # 10년 이동평균선
    last_100["10년 이동평균"] = (
        last_100["연평균기온"]
        .rolling(window=10, min_periods=1)
        .mean()
    )

    fig.add_trace(
        go.Scatter(
            x=last_100["연도"],
            y=last_100["10년 이동평균"],
            mode="lines",
            name="10년 이동평균",
            line=dict(
                width=4,
                dash="dash"
            ),
            hovertemplate=
                "<b>%{x}년</b><br>" +
                "10년 이동평균: %{y:.1f} °C" +
                "<extra></extra>"
        )
    )

    fig.update_layout(
        title="서울 연평균 기온의 100년 변화",
        xaxis_title="연도",
        yaxis_title="연평균 기온 (°C)",
        hovermode="x unified",
        height=600,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(
            l=40,
            r=40,
            t=90,
            b=40
        )
    )

    fig.update_xaxes(
        dtick=10,
        showgrid=True
    )

    fig.update_yaxes(
        showgrid=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -----------------------------
    # 해석
    # -----------------------------
    st.subheader("📌 데이터에서 확인하기")

    if change > 0:
        st.success(
            f"{start_year}년의 연평균 기온은 {first_temp:.1f} °C, "
            f"{end_year}년은 {last_temp:.1f} °C로, "
            f"두 시점 사이에 약 {change:.1f} °C 높아졌습니다."
        )
    elif change < 0:
        st.info(
            f"{start_year}년의 연평균 기온은 {first_temp:.1f} °C, "
            f"{end_year}년은 {last_temp:.1f} °C로, "
            f"두 시점 사이에 약 {abs(change):.1f} °C 낮아졌습니다."
        )
    else:
        st.info(
            "분석 시작 연도와 마지막 연도의 연평균 기온이 거의 같습니다."
        )

    st.caption(
        "※ 연평균 기온은 해당 연도의 일별 평균기온을 평균하여 계산했습니다. "
        "연간 300일 이상 자료가 있는 연도만 분석에 포함했습니다."
    )

    # -----------------------------
    # 데이터 표
    # -----------------------------
    with st.expander("연도별 데이터 보기"):
        display_df = last_100[
            ["연도", "연평균기온", "자료일수"]
        ].copy()

        display_df.columns = [
            "연도",
            "연평균 기온 (°C)",
            "자료 일수"
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
