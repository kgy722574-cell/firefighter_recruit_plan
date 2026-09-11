from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="소방공무원 채용·조직업무 조회",
    page_icon="🚒",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
HIRING_FILE = BASE_DIR / "소방공무원_3개년_채용계획.csv"
DUTY_FILE = BASE_DIR / "소방본부_표준업무.csv"

# ------------------------------------------------------------
# 데이터 로딩: Streamlit Cloud에서 파일 경로 문제를 안전하게 처리
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    p = Path(path)
    # 엑셀에서 저장한 CSV(utf-8-sig)와 일반 utf-8을 모두 처리
    try:
        return pd.read_csv(p, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(p, encoding="utf-8")


def require_file(path: Path, label: str) -> None:
    """필수 파일이 없을 때 긴 traceback 대신 이해하기 쉬운 안내를 표시한다."""
    if not path.is_file():
        st.error(f"필수 데이터 파일을 찾을 수 없습니다: **{label}**")
        st.code(str(path))
        st.markdown(
            "GitHub 저장소가 아래 구조인지 확인하세요.\n\n"
            "```text\n"
            "저장소 루트/\n"
            "├─ app.py\n"
            "├─ requirements.txt\n"
            "└─ data/\n"
            "   ├─ 소방공무원_3개년_채용계획.csv\n"
            "   └─ 소방본부_표준업무.csv\n"
            "```"
        )
        st.stop()


require_file(HIRING_FILE, HIRING_FILE.name)
require_file(DUTY_FILE, DUTY_FILE.name)

try:
    hiring = load_csv(str(HIRING_FILE))
    duty = load_csv(str(DUTY_FILE))
except Exception as e:
    st.error("데이터 파일을 읽는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()

# ------------------------------------------------------------
# 데이터 유효성 검사
# ------------------------------------------------------------
required_hiring_cols = {
    "연도", "시도", "총계",
    "공개경쟁채용_소계", "공개경쟁채용_남성", "공개경쟁채용_여성",
    "경력경쟁채용_소계", "경력경쟁채용_남성", "경력경쟁채용_여성", "경력경쟁채용_양성",
}
required_duty_cols = {"부서", "업무분야", "주요업무", "업무키워드", "비고"}

missing_hiring = required_hiring_cols - set(hiring.columns)
missing_duty = required_duty_cols - set(duty.columns)

if missing_hiring:
    st.error(f"채용계획 CSV에 필요한 컬럼이 없습니다: {sorted(missing_hiring)}")
    st.stop()
if missing_duty:
    st.error(f"조직업무 CSV에 필요한 컬럼이 없습니다: {sorted(missing_duty)}")
    st.stop()

hiring["연도"] = pd.to_numeric(hiring["연도"], errors="coerce").astype("Int64")
hiring = hiring.dropna(subset=["연도"]).copy()
hiring["연도"] = hiring["연도"].astype(int)

numeric_cols = [
    "총계", "공개경쟁채용_소계", "공개경쟁채용_남성", "공개경쟁채용_여성",
    "경력경쟁채용_소계", "경력경쟁채용_남성", "경력경쟁채용_여성", "경력경쟁채용_양성",
]
for col in numeric_cols:
    hiring[col] = pd.to_numeric(hiring[col], errors="coerce").fillna(0).astype(int)

# ------------------------------------------------------------
# 화면
# ------------------------------------------------------------
st.title("🚒 소방공무원 채용·소방본부 조직업무 조회")
st.caption(
    "2024~2026년 소방공무원 채용계획과 평균적인 시·도 소방본부의 부서별 업무를 한 화면에서 조회합니다."
)

with st.sidebar:
    st.header("메뉴")
    page = st.radio(
        "조회 기능",
        [
            "지역·연도별 채용 조회",
            "소방본부 부서별 업무 조회",
            "업무로 담당부서 찾기",
            "데이터 원문",
            "배포 점검",
        ],
    )
    st.divider()
    st.info(
        "조직·업무 정보는 여러 시·도 소방본부에서 공통적으로 나타나는 기능을 기준으로 표준화한 참고 모델입니다. "
        "실제 부서명과 분장사무는 해당 시·도 소방본부 최신 조직도를 확인해야 합니다."
    )

if page == "지역·연도별 채용 조회":
    st.subheader("📊 지역별·연도별 채용계획 조회")

    regions = [x for x in hiring["시도"].dropna().unique().tolist() if x != "합계"]
    years = sorted(hiring["연도"].unique().tolist())

    c1, c2 = st.columns(2)
    with c1:
        default_region_idx = regions.index("경기") if "경기" in regions else 0
        region = st.selectbox("지역 선택", regions, index=default_region_idx)
    with c2:
        year = st.selectbox("연도 선택", years, index=len(years) - 1)

    selected = hiring[(hiring["시도"] == region) & (hiring["연도"] == year)]
    if selected.empty:
        st.warning("선택한 지역·연도 조합의 데이터가 없습니다.")
    else:
        row = selected.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 채용계획", f"{int(row['총계']):,}명")
        m2.metric("공개경쟁채용", f"{int(row['공개경쟁채용_소계']):,}명")
        m3.metric("경력경쟁채용", f"{int(row['경력경쟁채용_소계']):,}명")
        career_share = row["경력경쟁채용_소계"] / row["총계"] * 100 if row["총계"] else 0
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
    st.warning(
        "아래 조직은 특정 시·도의 실제 조직도를 복제한 것이 아니라, 소방본부의 공통 기능을 보기 쉽게 표준화한 참고 모델입니다."
    )

    departments = sorted(duty["부서"].dropna().unique().tolist())
    c1, c2 = st.columns([1, 2])
    with c1:
        dept = st.selectbox("부서 선택", departments)
    with c2:
        keyword = st.text_input("부서 내 업무 검색", placeholder="예: 화재예방, 구급, 장비, 정보통신")

    result = duty[duty["부서"] == dept].copy()
    if keyword.strip():
        q = keyword.strip().lower()
        mask = result.astype(str).apply(
            lambda col: col.str.lower().str.contains(q, na=False, regex=False)
        ).any(axis=1)
        result = result[mask]

    st.markdown(f"### {dept}")
    if result.empty:
        st.info("조건에 맞는 업무가 없습니다.")
    else:
        for _, r in result.iterrows():
            preview = str(r["주요업무"])
            if len(preview) > 35:
                preview = preview[:35] + "..."
            with st.expander(f"{r['업무분야']} — {preview}", expanded=True):
                st.write(r["주요업무"])
                st.caption(f"업무 키워드: {r['업무키워드']}")
                st.caption(f"참고: {r['비고']}")

    st.dataframe(result[["부서", "업무분야", "주요업무", "비고"]], use_container_width=True, hide_index=True)

elif page == "업무로 담당부서 찾기":
    st.subheader("🔎 업무명으로 예상 담당부서 찾기")
    st.write("업무 키워드를 입력하면 표준 업무DB에서 관련 부서와 업무를 찾아줍니다.")

    q = st.text_input(
        "업무 키워드",
        placeholder="예: 소방안전관리자 / 119 신고 / 구급 / 예산 / 화재조사 / 무선통신",
    )

    if q.strip():
        q2 = q.strip().lower()
        searchable = duty[["부서", "업무분야", "주요업무", "업무키워드"]].astype(str)
        mask = searchable.apply(
            lambda col: col.str.lower().str.contains(q2, na=False, regex=False)
        ).any(axis=1)
        found = duty[mask].copy()

        if found.empty:
            terms = [t for t in q2.replace(",", " ").split() if t]
            if terms:
                combined = searchable.agg(" ".join, axis=1).str.lower()
                mask = combined.apply(lambda txt: any(t in txt for t in terms))
                found = duty[mask].copy()

        if found.empty:
            st.warning("관련 업무를 찾지 못했습니다. 더 짧은 키워드로 검색해 보세요.")
        else:
            st.success(f"관련 업무 {len(found)}건을 찾았습니다.")
            st.dataframe(
                found[["부서", "업무분야", "주요업무", "비고"]],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.markdown("**검색 예시**: `소방시설`, `위험물`, `구급`, `화재조사`, `정보통신`, `예산`, `교육`, `특수재난`")

elif page == "데이터 원문":
    st.subheader("🗂 데이터 원문")
    tab1, tab2 = st.tabs(["채용계획 CSV", "표준 조직업무 DB"])

    with tab1:
        st.dataframe(hiring, use_container_width=True, hide_index=True)
        st.download_button(
            "채용계획 CSV 다운로드",
            hiring.to_csv(index=False).encode("utf-8-sig"),
            file_name="소방공무원_3개년_채용계획.csv",
            mime="text/csv",
        )

    with tab2:
        st.dataframe(duty, use_container_width=True, hide_index=True)
        st.download_button(
            "조직업무 DB 다운로드",
            duty.to_csv(index=False).encode("utf-8-sig"),
            file_name="소방본부_표준업무.csv",
            mime="text/csv",
        )

elif page == "배포 점검":
    st.subheader("🛠 Streamlit Community Cloud 배포 점검")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("채용 CSV", "정상" if HIRING_FILE.is_file() else "없음")
        st.code(str(HIRING_FILE))
    with c2:
        st.metric("업무 CSV", "정상" if DUTY_FILE.is_file() else "없음")
        st.code(str(DUTY_FILE))

    st.markdown("#### 현재 앱 기준 경로")
    st.code(str(BASE_DIR))

    st.markdown("#### data 폴더 파일 목록")
    if DATA_DIR.exists():
        st.write([p.name for p in DATA_DIR.iterdir() if p.is_file()])
    else:
        st.warning("data 폴더가 없습니다.")

    st.success("이 화면에서 두 CSV가 모두 '정상'으로 표시되면 파일 경로 문제는 없습니다.")

st.divider()
st.caption("채용계획: 2024·2025·2026년 소방공무원 채용시험 시행계획 자료를 통합한 CSV 기준")
st.caption("조직업무: 시·도별 실제 명칭·분장 차이를 고려한 공통기능 중심의 참고용 표준화 모델")
