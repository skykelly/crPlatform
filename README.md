# Korea Customer / Life Fact Base

한국 고객의 생활 변화와 Home & Living 수요를 분석하기 위한 공식 통계 기반 리서치 저장소입니다.

## 구성

- `sites/korea-life-fact-base/` — 배포 가능한 정적 리서치 웹페이지
- `outputs/01a1263b-a1e2-7bf1-92f4-1494b204937a/` — Core Fact Catalog, 1차 Fact Dataset, 월간 갱신 Workflow

## 운영 원칙

- KOSIS·국가데이터처·국토교통부 등 1차 공식 출처를 우선 사용합니다.
- Actual과 Official Projection은 별도 관측치로 보관합니다.
- 통계표 ID, 단위, 지역 범위, 수집일, QA 이슈를 함께 기록합니다.
- 현장 보도는 생활 조건을 이해하기 위한 사례로만 사용하며, 통계적 대표성의 근거로 쓰지 않습니다.

## 웹페이지

정적 파일은 `sites/korea-life-fact-base/dist/index.html`입니다. 웹페이지는 지표 대시보드, 사건, 해석, 전망 탭으로 구성됩니다.

## 데이터 파이프라인

- `data/factbase.sqlite` — 39개 Catalog 항목과 84,592개 공식 관측치의 기준 DB. 기존 엑셀을 손상시키지 않고 옮겼습니다.
- `pipeline/factbase.py` — KOSIS 공식 API 수집, Actual/Official Projection 분리, 중복·결측·개정 검증, 웹용 JSON 생성.
- `sites/korea-life-fact-base/dist/data/dashboard.json` — DB에서 생성한 공개 대시보드 데이터. 웹페이지는 공개 GitHub `main`의 이 파일을 먼저 읽고, 연결 실패 시 배포된 저장본을 사용합니다.
- `data/raw/YYYY-MM-DD/` — 실제 값이 변경된 실행의 KOSIS API 응답 원문. 인증키는 저장하지 않습니다.

첫 적재는 `python -m pip install openpyxl==3.1.5` 후 `python pipeline/factbase.py bootstrap`으로 재현할 수 있습니다. 이미 DB가 있으면 덮어쓰지 않습니다. 검증과 웹 데이터 재생성은 `python -m unittest discover -s tests -v`, `python pipeline/factbase.py check`, `python pipeline/factbase.py build` 순서입니다.

## 자동 실행

[GitHub Actions](.github/workflows/factbase-refresh.yml)가 매월 10일 09:30(서울)에 실행됩니다. 수동 실행도 가능합니다. 저장소 Settings → Secrets and variables → Actions에 `KOSIS_API_KEY`를 등록해야 합니다. KOSIS [공식 활용신청](https://kosis.kr/openapi/)에서 발급한 키를 사용하고, 키를 이 저장소나 채팅에 붙여 넣지 마세요.

실행 순서: 테스트 → 기존 DB 확인 → 8개 공식 표 API 조회 → 중복·분류·상태 검사 → 개정 이력 기록 → DB 및 웹 JSON 생성 → 변경이 있을 때만 `main`에 커밋. 수집 또는 검증 실패 시 후속 커밋 단계가 실행되지 않습니다. 공식 전망 표의 수치가 바뀌면 추계 버전 확인이 필요하므로 자동 반영하지 않고 실행을 실패시킵니다. 웹은 공개 GitHub JSON을 읽으므로 승인된 커밋이 반영되면 다음 페이지 조회부터 최신 값을 보여줍니다. 소스 코드나 기사 해석은 이 데이터 파이프라인이 자동 수정하지 않습니다.

현재 API 인증키가 등록되지 않아 실시간 재수집은 검증 전입니다. 자세한 운영 규칙은 [월간 갱신 Workflow](outputs/01a1263b-a1e2-7bf1-92f4-1494b204937a/monthly_refresh_workflow.md)를 참조하세요.
