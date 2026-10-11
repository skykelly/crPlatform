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

## 월간 갱신

매월 10일에 공식 공표값과 개정 여부를 점검합니다. 상세 실행 순서는 [월간 갱신 Workflow](outputs/01a1263b-a1e2-7bf1-92f4-1494b204937a/monthly_refresh_workflow.md)를 따릅니다.
