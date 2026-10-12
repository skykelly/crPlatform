#!/usr/bin/env python3
"""설정 파일(pipeline/official_tables.json)로 KOSIS 표를 받아 팩트베이스에 넣는다.

- 표마다 독립적으로 받는다. 한 표가 실패해도 나머지는 저장하고, 실패는 요약에 남긴다.
- 지역 분류(geo)는 전국 코드 하나만 받고 저장하지 않는다(geography_code='00').
- 나머지 분류는 dimension_2(첫째), dimension_3(둘째 이후를 '|'로 연결)에 코드·이름을 넣는다.
- 숫자가 아닌 값('-', 'X' 등)은 건너뛴다.

실행: python3 pipeline/official_tables.py                 # API (KOSIS_API_KEY 필요)
      python3 pipeline/official_tables.py --from-raw data/raw/<날짜>
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from factbase import API, ROOT, check, connect, ensure_catalog, insert_row, normalized_value, source_url

SPEC = Path(__file__).resolve().parent / "official_tables.json"
NUMERIC = re.compile(r"-?\d+(\.\d+)?")


def load_spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))["tables"]


def fetch(t, key, today):
    end = str(today.year) if t["prd"] != "M" else today.strftime("%Y%m")
    params = {"method": "getList", "apiKey": key, "orgId": t["org"], "tblId": t["tbl"],
              "itmId": t["itm"], "prdSe": t["prd"], "startPrdDe": str(t["start"]).replace(".", ""), "endPrdDe": end,
              "format": "json", "jsonVD": "Y"}
    for i, code in enumerate(t["objL"], 1):
        params[f"objL{i}"] = code
    request = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "crPlatform-factbase/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        body = response.read().decode("utf-8", errors="replace")
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        code = re.search(r'err\s*:\s*"([0-9A-Za-z_-]+)"', body)
        msg = re.search(r'errMsg\s*:\s*"([^"]{0,160})"', body)
        raise ValueError(f"KOSIS error {code.group(1) if code else 'non-JSON'}: {(msg.group(1) if msg else '').replace(key, '[redacted]')}")
    if isinstance(result, dict):
        raise ValueError(f"KOSIS error {result.get('err')}: {str(result.get('errMsg', ''))[:160]}")
    if not result:
        raise ValueError("no rows")
    return result


def map_rows(t, items, today_iso):
    n = len(t["objL"])
    geo = t.get("geo")
    keep = set(t.get("keep_items") or [])
    rows, months = [], set()
    for item in items:
        if item.get("TBL_ID") != t["tbl"]:
            raise ValueError(f"{t['tbl']}: wrong table in response")
        if any(item.get(f"C{i}") for i in range(n + 1, 9)):
            raise ValueError(f"{t['tbl']}: unexpected extra classification")
        if keep and item.get("ITM_ID") not in keep:
            continue
        period = str(item.get("PRD_DE", ""))
        if t["prd"] == "M":
            if not re.fullmatch(r"\d{6}|\d{4}\.\d{2}", period):
                raise ValueError(f"{t['tbl']}: unexpected period {period}")
            months.add(period[-2:])
        elif not re.fullmatch(r"\d{4}", period):
            raise ValueError(f"{t['tbl']}: unexpected period {period}")
        year = int(period[:4])
        if not 1990 <= year <= 2052:
            raise ValueError(f"{t['tbl']}: unexpected year {year}")
        value = normalized_value(item.get("DT"))
        if not NUMERIC.fullmatch(value):
            continue
        dims = [(str(item.get(f"C{i}") or ""), str(item.get(f"C{i}_NM") or "").strip()) for i in range(1, n + 1)]
        if geo is not None:
            if dims[geo][0] != t["objL"][geo]:
                raise ValueError(f"{t['tbl']}: non-national geography {dims[geo][0]}")
            dims.pop(geo)
        d2 = dims[0] if dims else ("", "")
        rest = dims[1:]
        d3 = ("|".join(c for c, _ in rest), "|".join(nm for _, nm in rest)) if rest else ("", "")
        rows.append(dict(fact_id=t["fact"], driver=t["driver"], topic=t["topic"], dataset_id=t["tbl"],
                         actual_projection="Actual", year=year, geography_code="00", geography_name="전국",
                         dimension_2_code=d2[0], dimension_2_name=d2[1], dimension_3_code=d3[0], dimension_3_name=d3[1],
                         measure_code=str(item.get("ITM_ID") or ""), measure_name=str(item.get("ITM_NM") or "").strip(),
                         value_raw=value, unit=str(item.get("UNIT_NM") or ""), source_url=source_url(t["tbl"]),
                         retrieved_at=today_iso))
    if len(months) > 1:
        raise ValueError(f"{t['tbl']}: several months per year {sorted(months)}; one survey month expected")
    keys = [(r["year"], r["dimension_2_code"], r["dimension_3_code"], r["measure_code"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{t['tbl']}: duplicate observations")
    if not rows:
        raise ValueError(f"{t['tbl']}: no numeric rows")
    return rows


def update_catalog(conn, t, rows):
    rec = conn.execute("SELECT record_json FROM catalog WHERE fact_id=?", (t["fact"],)).fetchone()
    if not rec:
        return
    data = json.loads(rec[0])
    ids = [x.strip() for x in str(data.get("Table ID 또는 데이터 식별자") or "").split(" / ") if x.strip() and not x.startswith("미정")]
    label = f"{t['tbl']} {t['title']}"
    if not any(x.startswith(t["tbl"]) for x in ids):
        ids.append(label)
    data["Table ID 또는 데이터 식별자"] = " / ".join(ids)
    data["최신 데이터 기준연도"] = max(r["year"] for r in rows)
    if not data.get("원본 URL"):
        data["원본 URL"] = source_url(t["tbl"])
    conn.execute("UPDATE catalog SET record_json=? WHERE fact_id=?", (json.dumps(data, ensure_ascii=False), t["fact"]))


def run(responses, today_iso, save_raw):
    spec = {t["tbl"]: t for t in load_spec()}
    staged, summary = {}, {}
    for tbl, items in responses.items():
        try:
            staged[tbl] = map_rows(spec[tbl], items, today_iso)
            summary[tbl] = {"rows": len(staged[tbl])}
        except Exception as exc:
            summary[tbl] = {"error": str(exc)[:200]}
    conn = connect()
    try:
        check(conn)
        changes = 0
        with conn:
            ensure_catalog(conn)
            for tbl, rows in staged.items():
                for row in rows:
                    changes += insert_row(conn, row, revisions=True)
                update_catalog(conn, spec[tbl], rows)
            check(conn)
        if changes and save_raw:
            directory = ROOT / "data" / "raw" / today_iso
            directory.mkdir(parents=True, exist_ok=True)
            for tbl in staged:
                (directory / f"{tbl}.json").write_text(json.dumps(responses[tbl], ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    finally:
        conn.close()
    return {"changed_observations": changes, "tables": summary}


def refresh():
    key = os.environ.get("KOSIS_API_KEY", "")
    if not key:
        raise SystemExit("KOSIS_API_KEY is required")
    today = dt.date.today()
    responses, failed = {}, {}
    for t in load_spec():
        try:
            responses[t["tbl"]] = fetch(t, key, today)
        except Exception as exc:
            failed[t["tbl"]] = {"error": f"{type(exc).__name__}: {str(exc).replace(key, '[redacted]')[:180]}"}
    result = run(responses, today.isoformat(), save_raw=True)
    result["tables"].update(failed)
    ok = sum(1 for v in result["tables"].values() if "rows" in v)
    result["ok_tables"] = f"{ok}/{len(load_spec())}"
    print(json.dumps(result, ensure_ascii=False, indent=1))
    status = ROOT / "data" / "discovery" / "official_tables_status.json"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(json.dumps({"run_at": today.isoformat(), **result}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def from_raw(directory):
    directory = Path(directory) if str(directory).startswith("/") else ROOT / directory
    responses = {}
    for t in load_spec():
        path = directory / f"{t['tbl']}.json"
        if path.exists():
            responses[t["tbl"]] = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(run(responses, dt.date.today().isoformat(), save_raw=False), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--from-raw":
        from_raw(sys.argv[2])
    else:
        refresh()
