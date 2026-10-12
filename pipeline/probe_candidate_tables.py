"""Inspect classification and item metadata of candidate KOSIS tables.

pipeline/candidates.json 의 표마다 분류(OBJ)·항목(ITM)·기간(PRD) 메타데이터를 받아
data/discovery/probe_<날짜>.json 에 저장한다. 값 자체는 받지 않고, 키는 저장하지 않는다.
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


def meta(table, org, kind):
    params = {"method": "getMeta", "type": kind, "apiKey": KEY, "orgId": org,
              "tblId": table, "format": "json", "jsonVD": "Y"}
    request = urllib.request.Request("https://kosis.kr/openapi/statisticsData.do?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "crPlatform-factbase/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read().decode("utf-8", errors="replace")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        code = re.search(r'err\s*:\s*"([0-9A-Za-z_-]+)"', body)
        raise ValueError(f"KOSIS error {code.group(1) if code else 'non-JSON'}")


def main():
    spec = json.loads((ROOT / "pipeline" / "candidates.json").read_text(encoding="utf-8"))
    out = []
    for item in spec["tables"]:
        entry = dict(item)
        for kind in ("OBJ", "ITM", "PRD"):
            try:
                result = meta(item["tbl"], item.get("org", "101"), kind)
                if isinstance(result, list) and kind == "ITM":
                    # 분류별 코드·이름 전체 (분류값이 많아도 이름만 남긴다)
                    groups = {}
                    for row in result:
                        groups.setdefault(row.get("OBJ_ID") or row.get("OBJ_NM") or "", []).append(
                            [row.get("ITM_ID"), row.get("ITM_NM"), row.get("UP_ITM_ID")])
                    entry["items"] = groups
                elif isinstance(result, list):
                    entry[kind.lower()] = result[:60]
                else:
                    entry[kind.lower() + "_error"] = str(result)[:200]
            except Exception as exc:
                entry[kind.lower() + "_error"] = f"{type(exc).__name__}: {str(exc).replace(KEY, '[redacted]')[:160]}"
        out.append(entry)
        print(f"PROBE {item['tbl']}: {', '.join(k for k in entry if k not in item)}")
    path = ROOT / "data" / "discovery" / f"probe_{dt.date.today().isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if KEY in text:
        raise SystemExit("credential leaked into probe output; not writing")
    path.write_text(text + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
