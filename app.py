from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HIRING_FILE = DATA_DIR / "소방공무원_3개년_채용계획.csv"
DUTY_FILE = DATA_DIR / "소방본부_표준업무.csv"

st.set_page_config(
    page_title="소방공무원 채용·조직업무 조회",
    page_icon="🚒",
    layout="wide",
)

@st.cache_data
def load_data():
    hiring = pd.read_csv(HIRING_FILE)
    duty = pd.read_csv(DUTY_FILE)
    hiring["연도"] = hiring["연도"].astype(int)
    return hiring, duty

hiring, duty = load_data()

st.title("🚒 소방공무원 채용·소방본부 조직업무 조회")
st.caption("2024~2026년 채용계획 데이터와 시·도 소방본부의 공통적인 조직·업무를 함께 조회하는 앱")

with st.sidebar:
    st.header("메뉴")
    page = st.radio(
        "조회 기능",
        ["지역·연도별 채용 조회", "소방본부 부서별 업무 조회", "업무로 담당부서 찾기", "데이터 원문"],
    )
    st.divider()
    st.info(
        "※ 조직·업무 정보는 여러 시·도에서 공통적으로 나타나는 기능을 참고해 표준화한 모델입니다. "
        "실제 부서명과 분장사무는 해당 시·도 소방본부의 최신 조직도를 확인해야 합니다."
    )

if page == "지역·연도별 채용 조회":
    st.subheader("📊 지역별·연도별 채용계획 조회")

    regions = [x for x in hiring["시도"].unique() if x != "합계"]
    years = sorted(hiring["연도"].unique())

    c1, c2 = st.columns(2)
    with c1:
        region = st.selectbox("지역 선택", regions, index=regions.index("경기") if "경기" in regions else 0)
    with c2:
        year = st.selectbox("연도 선택", years, index=len(years)-1)

    selected = hiring[(hiring["시도"] == region) & (hiring["연도"] == year)]
    if not selected.empty:
        row = selected.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 채용계획", f"{int(row['총계']):,}명")
        m2.metric("공개경쟁채용", f"{int(row['공개경쟁채용_소계']):,}명")
        m3.metric("경력경쟁채용", f"{int(row['경력경쟁채용_소계']):,}명")
        career_share = (row["경력경쟁채용_소계"] / row["총계"] * 100) if row["총계"] else 0
        m4.metric("경채 비중", f"{career_share:.1f}%")

    st.markdown("#### 선택 지역의 3개년 채용 흐름")
    trend = hiring[hiring["시도"] == region].sort_values("연도")
    fig = px.line(
        trend,
        x="연도",
        y=["총계", "공개경쟁채용_소계", "경력경쟁채용_소계"],
        markers=True,
        labels={"value": "채용인원(명)", "variable": "구분"},
    )
    fig.update_layout(xaxis=dict(dtick=1), legend_title_text="채용구분")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"#### {year}년 지역별 채용규모 비교")
    year_df = hiring[(hiring["연도"] == year) & (~hiring["시도"].isin(["합계"]))].copy()
    year_df = year_df.sort_values("총계", ascending=True)
    fig2 = px.bar(
        year_df,
        x="총계",
        y="시도",
        orientation="h",
        text="총계",
        labels={"총계": "채용인원(명)", "시도": "지역"},
    )
    fig2.update_traces(texttemplate="%{text:,}", textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 상세 데이터")
    st.dataframe(trend, use_container_width=True, hide_index=True)

elif page == "소방본부 부서별 업무 조회":
    st.subheader("🏢 평균적인 시·도 소방본부 부서별 업무 조회")
    st.warning("아래 조직은 실제 특정 시·도의 조직도를 복제한 것이 아니라, 소방본부의 공통 기능을 보기 쉽게 표준화한 참고 모델입니다.")

    departments = sorted(duty["부서"].unique())
    c1, c2 = st.columns([1, 2])
    with c1:
        dept = st.selectbox("부서 선택", departments)
    with c2:
        keyword = st.text_input("부서 내 업무 검색", placeholder="예: 화재예방, 구급, 장비, 정보통신")

    result = duty[duty["부서"] == dept].copy()
    if keyword.strip():
        q = keyword.strip().lower()
        mask = result.astype(str).apply(lambda col: col.str.lower().str.contains(q, na=False)).any(axis=1)
        result = result[mask]

    st.markdown(f"### {dept}")
    if result.empty:
        st.info("조건에 맞는 업무가 없습니다.")
    else:
        for _, r in result.iterrows():
            with st.expander(f"{r['업무분야']} — {r['주요업무'][:35]}...", expanded=True):
                st.write(r["주요업무"])
                st.caption(f"업무 키워드: {r['업무키워드']}")
                st.caption(f"참고: {r['비고']}")

    st.dataframe(result[["부서", "업무분야", "주요업무", "비고"]], use_container_width=True, hide_index=True)

elif page == "업무로 담당부서 찾기":
    st.subheader("🔎 업무명으로 예상 담당부서 찾기")
    st.write("업무 키워드를 입력하면 표준 업무DB에서 관련 부서와 업무를 찾아줍니다.")

    q = st.text_input("업무 키워드", placeholder="예: 소방안전관리자 / 119 신고 / 구급 / 예산 / 화재조사 / 무선통신")

    if q.strip():
        q2 = q.strip().lower()
        # 주요업무, 업무분야, 업무키워드, 부서를 대상으로 검색
        searchable = duty[["부서", "업무분야", "주요업무", "업무키워드"]].astype(str)
        mask = searchable.apply(lambda col: col.str.lower().str.contains(q2, na=False)).any(axis=1)
        found = duty[mask].copy()

        if found.empty:
            # 키워드 묶음을 부분 단어로 재검색
            terms = [t for t in q2.replace(",", " ").split() if t]
            if terms:
                combined = searchable.agg(" ".join, axis=1).str.lower()
                mask = combined.apply(lambda txt: any(t in txt for t in terms))
                found = duty[mask].copy()

        if found.empty:
            st.warning("관련 업무를 찾지 못했습니다. 더 짧은 키워드로 검색해 보세요.")
        else:
            st.success(f"관련 업무 {len(found)}건을 찾았습니다.")
            st.dataframe(found[["부서", "업무분야", "주요업무", "비고"]], use_container_width=True, hide_index=True)
    else:
        st.markdown("**검색 예시**: `소방시설`, `위험물`, `구급`, `화재조사`, `정보통신`, `예산`, `교육`, `특수재난`")

elif page == "데이터 원문":
    st.subheader("🗂 데이터 원문")
    tab1, tab2 = st.tabs(["채용계획 CSV", "표준 조직업무 DB"])
    with tab1:
        st.dataframe(hiring, use_container_width=True, hide_index=True)
        st.download_button(
            "채용계획 CSV 다운로드",
            hiring.to_csv(index=False, encoding="utf-8-sig"),
            file_name="소방공무원_3개년_채용계획.csv",
            mime="text/csv",
        )
    with tab2:
        st.dataframe(duty, use_container_width=True, hide_index=True)
        st.download_button(
            "조직업무 DB 다운로드",
            duty.to_csv(index=False, encoding="utf-8-sig"),
            file_name="소방본부_표준업무.csv",
            mime="text/csv",
        )

st.divider()
st.caption("채용계획: 사용자가 제공한 2024·2025·2026년 소방공무원 채용시험 시행계획 자료를 통합한 CSV 기준")
st.caption("조직업무: 시·도별 실제 명칭·분장 차이를 고려한 공통기능 중심의 참고용 표준화 모델")
