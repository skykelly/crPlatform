"""Search KOSIS table metadata without logging the API credential.

결과는 data/discovery/<날짜>.json 에 저장한다(표 ID·표 이름·기관만, 키 없음).
Actions 로그를 볼 수 없는 환경에서도 저장소에서 결과를 읽을 수 있게 하려는 것이다.
기관을 가리지 않고 찾는다(orgId 없음). 수집할 표가 정해지면 factbase.ORG에 기관을 적는다.
"""

import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

KEY = os.environ.get("KOSIS_API_KEY", "")
if not KEY:
    raise SystemExit("KOSIS_API_KEY missing")

ROOT = Path(__file__).resolve().parents[1]

# (검색어, 채우려는 지표·fact)
SEARCHES = (
    ("주거면적별 가구", "H02 면적 구간별 가구 (F·H 평형대 렌즈)"),
    ("사용면적별 가구", "H02 면적 구간별 가구"),
    ("가구원수별 주거면적", "H02 가구 유형×면적"),
    ("건축연도별 주택", "H04 30년 이상 노후주택 (H1-K6)"),
    ("미거주 주택", "H05 빈집 (H1-K7)"),
    ("빈집", "H05 빈집"),
    ("전입사유별 이동자", "L02 이동 사유 (F2-K7)"),
    ("평균 초혼연령", "L03 초혼 연령 (F2-K3)"),
    ("첫째아 출산 모의 평균 연령", "F2-K5"),
    ("부모와 동거", "L05 청년 독립 (F2-K1)"),
    ("소비자물가지수 품목별", "N1-K8 실질화 지수"),
    ("지출목적별 소비자물가지수", "N1-K8 실질화 지수"),
    ("취업시간별 취업자", "T1-K4 주당 근로시간"),
    ("유연근무제 활용", "T1-K5 재택·원격근무"),
    ("생활시간조사 행동분류별", "T1·T2 생활시간 전체 행동"),
    ("가구원수별 가계수지", "N1 가구 유형별 지출"),
    ("가구주연령별 가계수지", "N1 라이프스테이지별 지출"),
    ("온라인쇼핑 상품군별 거래액", "S07 온라인 거래액 (N1-K7)"),
    ("주거실태조사 점유형태", "H03 점유 (H1-K1)"),
    ("소득 대비 주택가격 비율", "H1-K8 PIR"),
    ("소득 대비 임대료 비율", "H1-K2 RIR"),
    ("최저주거기준 미달 가구", "H08 (H1-K4)"),
    ("보육통계 어린이집 이용 아동", "T2-K1 영유아 기관 이용"),
    ("노인장기요양보험 인정자", "L07 장기요양 (T2-K4)"),
    ("아침식사 결식률", "LS01 (T1-K8)"),
    ("유산소 신체활동 실천율", "T1-K9"),
    ("반려동물 양육 가구", "D07 (F1-K8)"),
    ("가구 에너지 소비", "H06 (H2-K3)"),
)
FIELDS = ("ORG_ID", "ORG_NM", "TBL_ID", "TBL_NM", "STAT_ID", "STAT_NM", "STRT_PRD_DE", "END_PRD_DE", "PRD_SE")


def search(term):
    params = {"method": "getList", "apiKey": KEY, "searchNm": term,
              "resultCount": "30", "startCount": "1", "format": "json", "jsonVD": "Y"}
    request = urllib.request.Request(
        "https://kosis.kr/openapi/statisticsSearch.do?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "crPlatform-factbase/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read().decode("utf-8", errors="replace")
    try:
        rows = json.loads(body)
    except json.JSONDecodeError:
        code = re.search(r'err\s*:\s*"([0-9A-Za-z_-]+)"', body)
        message = re.search(r'errMsg\s*:\s*"([^"\r\n]{0,160})"', body)
        detail = message.group(1) if message else body[:180]
        raise ValueError(f"KOSIS error {code.group(1) if code else 'unknown'}: {detail}")
    if isinstance(rows, dict):
        raise ValueError(f"KOSIS error {rows.get('err')}: {str(rows.get('errMsg', ''))[:160]}")
    return [{field: row.get(field) for field in FIELDS if row.get(field) is not None} for row in rows]


def main():
    results = []
    for term, purpose in SEARCHES:
        entry = {"term": term, "purpose": purpose}
        try:
            entry["rows"] = search(term)
            print(f"SEARCH {term}: {len(entry['rows'])} results")
        except Exception as exc:
            message = re.sub(r"apiKey=[^&\s]+", "apiKey=[redacted]", str(exc).replace(KEY, "[redacted]"))
            entry["error"] = f"{type(exc).__name__}: {message}"
            print(f"SEARCH {term}: {entry['error']}")
        results.append(entry)
    out = ROOT / "data" / "discovery" / f"{dt.date.today().isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"searched_at": dt.datetime.now().isoformat(timespec="seconds"), "results": results},
                      ensure_ascii=False, indent=1)
    if KEY in text:
        raise SystemExit("credential leaked into discovery output; not writing")
    out.write_text(text + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
