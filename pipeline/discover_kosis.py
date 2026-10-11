"""Search KOSIS table metadata without logging the API credential."""

import json
import os
import re
import urllib.parse
import urllib.request

KEY = os.environ.get("KOSIS_API_KEY", "")
if not KEY:
    raise SystemExit("KOSIS_API_KEY missing")

SEARCHES = (
    "시도별 맞벌이 가구",
    "거처의 종류별 점유형태별 가구",
    "시군구별 이동자수",
    "생활시간조사 행동분류별 평균시간",
    "생활시간조사 수면",
    "생활시간조사 가정관리",
    "가계동향조사 가구당 월평균 소비지출",
    "가계동향조사 가전제품",
    "가계동향조사 주택 유지 수선",
)

for term in SEARCHES:
    params = {"method": "getList", "apiKey": KEY, "searchNm": term,
              "orgId": "101", "resultCount": "30", "startCount": "1", "format": "json", "jsonVD": "Y"}
    request = urllib.request.Request(
        "https://kosis.kr/openapi/statisticsSearch.do?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "crPlatform-factbase/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8", errors="replace")
        try:
            rows = json.loads(body)
        except json.JSONDecodeError:
            code = re.search(r'err\s*:\s*"([0-9A-Za-z_-]+)"', body)
            message = re.search(r'errMsg\s*:\s*"([^"\r\n]{0,160})"', body)
            detail = message.group(1).replace(KEY, "[redacted]") if message else body[:180].replace(KEY, "[redacted]")
            print(f"SEARCH {term}: KOSIS error {code.group(1) if code else 'unknown'}: {detail}")
            continue
        if not isinstance(rows, list):
            raise ValueError("non-list response")
        print(f"SEARCH {term}: {len(rows)} results")
        for row in rows:
            print(json.dumps({field: row.get(field) for field in
                              ("ORG_ID", "TBL_ID", "TBL_NM", "STAT_NM", "STRT_PRD_DE", "END_PRD_DE")},
                             ensure_ascii=False))
    except Exception as exc:
        message = str(exc).replace(KEY, "[redacted]")
        message = re.sub(r"apiKey=[^&\s]+", "apiKey=[redacted]", message)
        print(f"SEARCH {term}: {type(exc).__name__}: {message}")
