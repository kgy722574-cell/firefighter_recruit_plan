# 소방공무원 채용·조직업무 조회앱

Streamlit Community Cloud / GitHub 업로드용 **폴더 없는(flat) 구조**입니다.

## GitHub 저장소 구조

```text
저장소 루트/
├─ app.py
├─ requirements.txt
├─ 소방공무원_3개년_채용계획.csv
├─ 소방본부_표준업무.csv
└─ README.md
```

## Streamlit Community Cloud 배포

- Main file path: `app.py`
- 모든 파일을 GitHub 저장소의 같은 위치(루트)에 업로드하세요.
- CSV 파일명을 변경하지 마세요.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```
