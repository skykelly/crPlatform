# 딥리서치 회차 하위 에이전트 지시서 (Life Signals)

질문 하나를 맡아 백지 조사 → 4유형 기록 → 아티클까지 만든다. 본 세션이 검증·포털·커밋을 한다.

## 읽을 것 (이 순서)
1. 맡은 질문 폴더의 `request_rN.md` 전문과 `indicators.json`
2. `tools/templates/build_records.py`, `tools/templates/render_article.py` (형식 견본)
3. `lib/article.py` 머리말(cfg 키), `lib/judge.py`의 맡은 척도 정의(방향×속도 / 주도 주체 / 영향 순위 / 채택 4단계)
4. `lib/validate.py` 머리말(검증 규칙)

이전 회차 아티클·판정은 보지 않는다(백지 조사).

## 할 일
1. **조사:** WebSearch·WebFetch로 요청서 범위를 조사한다. 원문(정부 보도자료, KOSIS 표, 연구기관 보고서, 주요 언론)을 직접 열어 수치·날짜를 확인한다.
2. **팩트베이스 우선:** `indicators.json`에 `factbase` ID가 있는 지표는 `data/factbase.sqlite`(읽기 전용, KOSIS 공식 API로 수집)에서 먼저 값을 찾는다.
   ```python
   import sqlite3; c = sqlite3.connect("data/factbase.sqlite")
   c.execute("select dataset_id,measure_name,dimension_2_name,dimension_3_name,year,value_raw,unit,source_url,retrieved_at from observations "
             "where fact_id like ? and geography_code='00' and actual_projection='Actual' order by year", ("D01%",)).fetchall()
   ```
   - 출처는 `{"url": source_url, "publisher": "국가데이터처 KOSIS (표 ID·표 이름)", "date": retrieved_at, "grade": "A"}`, `verified=True`, definition에 "팩트베이스(KOSIS API) 값"이라 적는다.
   - 팩트베이스 H02(주거면적)·H03(점유형태) 매핑은 정정 대기 중이라 표 이름·항목을 꼭 확인하고, 어긋나면 공식 발표로 대체하며 `check_flags`에 남긴다.
   - 비율은 DB의 분자·분모로 직접 계산해도 된다(definition에 계산식). DB에 없거나 더 최신 공표가 있으면 공식 발표로 보완한다.
   - 먼저 `python3 tools/factbase_sync.py`를 돌려 `data/sync_report.md`의 DB 시계열을 본다. DB에 있는 연도의 값은 역산하지 않는다. 가계동향 세부 항목(S08~S15)과 생활시간 행동분류 전체(LS09)도 DB에 있다.
3. **발표 시기:** 지표마다 발표 주기와 최근·다음 발표 시기를 조사해 `indicators.json`의 `release`에 한 줄로 적는다(예: "연 1회, 7월 말 · 2025년 기준 2026-07-28 발표 · 다음 2027년 7월"). 모르면 "확인 필요"를 그대로 둔다.
4. **기록 작성 (`build_records.py`):** 견본 형식 그대로. 목표 규모
   - 지표: 추적 지표마다 대표값 1개 이상(가능하면 시계열 `extra.series`와 `prev_value`) — 판정에 필요한 3~5년 추세가 보이게
   - 사건: 최근 12개월 제도·발표·출시·정책 3~10개 (주체·일자)
   - 해석: 5~7개 (대상·방향·basis)
   - 세부 전망: 5~6개 (관찰 가능한 method, 대개 다음 공식 통계 발표로 판정. due는 2026-12 ~ 2027-12)
   - 메인 시나리오: 낙관·비관 각 1개(2027년 말 기준, milestones 3개, signposts로 세부 전망 연결)
5. **판정:** `lib/judge.py` 기준표대로 판정하고 근거 기록을 단다. 직접 재는 수치가 없으면 `prov=True`(잠정).
6. **아티클 (`render_article.py`):** 견본 cfg를 채운다. LENS는 라이프스테이지 5개, SIZE_LENS는 평형대 3개(60㎡ 이하 / 60~100㎡ / 100㎡ 초과) 모두(근거 없으면 빈 목록). 구간별 가구 수는 팩트베이스 H02와 H1-K3 기록을 쓴다.
7. **실행:** 질문 폴더에서 `python3 build_records.py` → `python3 render_article.py`. 둘 다 오류 없이 끝나야 한다.
8. **요약 파일 `research_r1_summary.md`:** 조사 범위, 주요 출처 목록(링크), 열지 못한 원문, 다음 간단 조사에서 먼저 찾을 것. 저장소가 공개라 남의 글 문장을 옮겨 적지 않는다(요약과 링크만).

## 규칙
- 출처 등급 A = 1차·공식 통계, B = 주요 언론·연구기관·공시, C = 블로그·출처 불명. **C는 단독 근거로 쓰지 않고 verified=False.**
- 원문을 직접 연 값만 `verified=True`. 수치·날짜를 지어내지 않는다. 정의가 다른 값은 병기하고 `check_flags`에 '확인 필요: 사유'.
- 해석은 basis 없으면, 전망은 due·method·basis 없으면 만들지 않는다. 해석·전망은 원문 미확인 사실을 근거로 쓰지 않는다.
- 문장: 짧은 보고체 한국어. 줄표(—)로 문장을 잇지 않는다. 비유·과장 없음. 약어는 처음에 풀어 쓴다(예: 소득 대비 임대료 비율(RIR)).
- 아티클 본문에는 사실과 기준만 쓴다. "조사 결과", "검증 결과에 따르면" 같은 과정 문구를 넣지 않는다.
- 기사 문장을 그대로 옮기지 않는다. 15단어 이상 인용 금지. 기록 문장은 직접 다시 쓴다.
- 맡은 질문 폴더 밖의 파일은 고치지 않는다(`data/factbase.sqlite`는 읽기만). git 커밋·푸시·게시 금지.

## 돌려줄 것 (최종 메시지, 짧게)
기록 수(유형별), 한 줄 답, 판정 요약, 추적 지표 확보 n/m과 빈 지표, 원문 미확인·확인 필요 목록, 한계(열지 못한 원문 등).
