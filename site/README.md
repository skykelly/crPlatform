# Life Signals 포털

모든 카테고리·질문의 아티클을 한 사이트에서 보여준다.

- 포털 주소(Claude 아티팩트): https://claude.ai/artifact/FmxvVJQ4gyuPg2kR6fiGjj
- 원본: `site/catalog.json`(카테고리·질문 목록) + 각 질문 폴더의 `article_rN.html`
- 결과물: `site/dist/` (포털 `index.html`, 회차별 아티클 `<카테고리>/<질문 번호(f1, h1 …)>/rN.html`)

## 갱신 방법

1. 질문 폴더에서 `build_records.py` → `render_article.py`로 아티클을 만든다. 새 회차는 `article_r2.html`처럼 번호만 올린다.
2. 새 카테고리나 질문을 열 때는 `catalog.json`에 추가한다. 질문 폴더에 아티클이 있으면 catalog에 없어도 자동으로 포함된다.
3. `python3 site/build_site.py` 를 실행한다. 깨진 내부 링크가 있으면 실패한다.
4. 같은 아티팩트 주소로 다시 게시한다: 진입 페이지는 `site/dist/artifact_index.html`, 아티클 페이지는 `site/dist/manifest.json`의 `pages` 목록을 같은 경로로 함께 올린다.

`site/dist/index.html`은 완전한 HTML 문서라 GitHub Pages 같은 정적 호스팅에도 그대로 쓸 수 있다.

## 통계 대시보드 (`dashboard.html`)

- `build_site.py`가 `site/dashboard.py`를 불러 `data/factbase.sqlite`에서 바로 만든다. 포털과 같은 주소에 `dashboard.html`로 함께 게시한다(manifest에 포함).
- 카드 정의는 `site/dashboard_spec.py`(5개 구분: 인구·가구 / 생애사건 / 생활시간·돌봄 / 주거 / 지출·물가). 식은 표·항목·분류 코드로 적고, 비중·합계·실질화는 빌드 때 계산한다. 그리기는 `dashboard.js`, 모양은 `dashboard.css`.
- 공식 추계(장래가구추계)는 점선과 '공식 추계' 구간으로 실적과 구분한다.
- 카드가 리포트 지표 기록(`data/indicator_map.json`)과 같은 값을 그대로 보여 주면 기록 번호를 자동으로 붙인다.
- '전체 탐색기' 탭은 팩트베이스의 모든 표를 전국·시도 단위로 싣는다(시군구 제외).
- 카드 계열이 비거나 카탈로그 항목이 어느 구분에도 없으면 빌드가 멈춘다. 점검만: `python3 site/dashboard.py`.
- 매월 10일 수집 뒤 다음 포털 재게시(주간 조사) 때 새 값으로 다시 만들어진다.
