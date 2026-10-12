"""<QNO> R<N> 4유형 기록 생성 + 규칙 검증. 출력: 같은 폴더 records.jsonl
실행: python3 build_records.py  (검증 오류가 있으면 exit 1)
"""
import sys
from pathlib import Path

Q, R = "<QNO>", "R1"
# 출처 사전: key → url·publisher·date·grade (A 공식 1차 / B 언론·연구기관 / C 출처 불명)
SRC = {
    "kosis_x": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_XXXX&conn_path=I2", "publisher": "국가데이터처 KOSIS (통계표명)", "date": "2026-10-10", "grade": "A"},
    "news_y": {"url": "https://example.com/article", "publisher": "언론사 (국가데이터처 2026 OO 통계 인용)", "date": "2026-07-28", "grade": "B"},
}
def src(*keys): return [dict(SRC[k], key=k) for k in keys]

base = dict(question=Q, question_version="v1.0", first_seen=R, last_seen=R, status="유효", replaces=None, check_flags=[])
records = []
def add(**kw):
    r = dict(base); r.update(kw); records.append(r)

# ---------- 지표 (M): indicator(K번호)·value·unit·as_of·region·definition·prev_value·representative ----------
add(id=f"{Q}-M-001", type="지표", indicator=f"{Q}-K1", importance=3, representative=True,
    statement="2025년 1인가구는 일반가구의 36.6%로 1년 전보다 0.5%p 늘었다.",
    value=36.6, unit="%", as_of="2025", region="KR", definition="인구주택총조사 등록센서스, 일반가구 기준", prev_value=36.1,
    extra={"series": {"2020": 31.7, "2025": 36.6}}, sources=src("kosis_x"), verified=True)

# ---------- 사건 (E): date·actor ----------
add(id=f"{Q}-E-001", type="사건", importance=2, date="2026-07-28", actor="국가데이터처",
    statement="국가데이터처가 2025 인구주택총조사 등록센서스 결과를 발표했다.", sources=src("news_y"), verified=True)

# ---------- 해석 (I): target·direction(강화|약화|중립)·basis ----------
add(id=f"{Q}-I-001", type="해석", importance=3, target="가구 소형화", direction="강화",
    statement="가구는 계속 작아지고 있다. …", basis=[f"{Q}-M-001"])

# ---------- 세부 전망 (F): due·condition·method(관찰 가능한 판정 방법)·basis·forecast_status·result ----------
add(id=f"{Q}-F-001", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 1인가구 비중은 37% 이상일 것이다.", due="2027-08-31", condition="없음",
    method="국가데이터처 2026 인구주택총조사 등록센서스 발표값 확인", basis=[f"{Q}-M-001"])

# ---------- 메인 질문 시나리오 (낙관·비관 각 1개, milestones·signposts) ----------
add(id=f"{Q}-F-101", type="전망", importance=3, forecast_status="진행 중", scenario="낙관", result=None,
    statement="2027년 말까지 …", milestones=[{"by": "2027-08", "text": "…"}],
    due="2027-12-31", condition="…", method="세 가지 중 두 가지 이상 충족 시 적중: (1) … (2) … (3) …",
    basis=[f"{Q}-M-001"], signposts=[{"id": f"{Q}-F-001", "on_hit": "낙관", "on_miss": "비관"}])
add(id=f"{Q}-F-102", type="전망", importance=3, forecast_status="진행 중", scenario="비관", result=None,
    statement="2027년 말까지 …", milestones=[{"by": "2027-08", "text": "…"}],
    due="2027-12-31", condition="없음", method="낙관 조건 중 하나 이하 충족 시 적중",
    basis=[f"{Q}-M-001"], signposts=[{"id": f"{Q}-F-001", "on_miss": "비관"}])

# ---------- 공통 마무리: patches.jsonl 적용 → 검증 → records.jsonl ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from validate import finish
finish(records, Path(__file__).parent)
