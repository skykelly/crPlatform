#!/usr/bin/env python3
"""Collect the five-driver dashboard's additional official KOSIS series."""

import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request

from factbase import API, ROOT, check, connect, insert_row, normalized_value, source_url

SPENDING = {"L": "S05", "L3": "S03", "M0": "S02", "M4": "S01", "M9": "S04"}
TIME_USE = {"S11": "LS03", "S4": "LS04"}
SOURCES = (
    ("DT_1ES4F09S", "Y", 2015, {"objL1": "00", "itmId": "ALL"}),
    ("DT_1B26001_A01", "Y", 2010, {"objL1": "00", "itmId": "ALL"}),
    ("DT_1TS202001", "F", 2014, {"objL1": "A0", "objL2": "S0", "objL3": "C1", "objL4": "S11", "itmId": "T10"}),
    ("DT_1TS202001", "F", 2014, {"objL1": "A0", "objL2": "S0", "objL3": "C1", "objL4": "S4", "itmId": "T10"}),
    ("DT_1PE1502", "F", 2015, {"objL1": "00", "objL2": "00", "itmId": "ALL"}),
    ("DT_1PE2002", "F", 2020, {"objL1": "00", "objL2": "00", "itmId": "ALL"}),
    ("DT_1L9U101", "Y", 2019, {"objL1": "ALL", "itmId": "T110"}),
)


def fetch(table, period, start, dimensions, key, current_year):
    params = {"method": "getList", "apiKey": key, "orgId": "101", "tblId": table,
              **dimensions, "prdSe": period, "startPrdDe": str(start),
              "endPrdDe": str(current_year), "format": "json", "jsonVD": "Y"}
    request = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "crPlatform-factbase/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8", errors="replace")
        result = json.loads(body)
    except Exception as exc:
        raise RuntimeError(f"{table}: API request failed ({type(exc).__name__})") from None
    if not isinstance(result, list) or not result:
        message = str(result.get("errMsg", "no rows"))[:160].replace(key, "[redacted]") if isinstance(result, dict) else "no rows"
        raise ValueError(f"{table}: KOSIS did not return rows: {message}")
    return result


def map_row(table, item, today):
    if item.get("TBL_ID") != table or not re.fullmatch(r"\d{4}", str(item.get("PRD_DE", ""))):
        raise ValueError(f"Unexpected table or period in {table}")
    if any(item.get(f"C{i}") for i in range(5, 9)):
        raise ValueError(f"Unexpected dimension in {table}")
    year = int(item["PRD_DE"])
    measure = str(item.get("ITM_ID") or "")
    category = str(item.get("C4") if table == "DT_1TS202001" else item.get("C1") or "")
    if table == "DT_1ES4F09S":
        fact_id, driver, topic, dim_code, dim_name = "D05", "Demographic", "맞벌이", "", ""
        if item.get("C1") != "00": raise ValueError("D05 must be nationwide")
    elif table == "DT_1B26001_A01":
        fact_id, driver, topic, dim_code, dim_name = "L01", "Life Event", "이사", "", ""
        if item.get("C1") != "00": raise ValueError("L01 must be nationwide")
    elif table == "DT_1TS202001":
        fact_id, driver, topic = TIME_USE.get(category), "Lifestyle", "생활시간"
        dim_code, dim_name = category, item.get("C4_NM") or ""
        if not fact_id or (item.get("C1"), item.get("C2"), item.get("C3")) != ("A0", "S0", "C1"):
            raise ValueError("Unexpected lifestyle classification")
    elif table in ("DT_1PE1502", "DT_1PE2002"):
        fact_id, driver, topic, dim_code, dim_name = "H03", "Home", "점유 형태", "00", "계"
        if (item.get("C1"), item.get("C2")) != ("00", "00"):
            raise ValueError("Unexpected tenure classification")
    else:
        fact_id, driver, topic = SPENDING.get(category), "Spending", "Home & Living 지출"
        dim_code, dim_name = category, item.get("C1_NM") or ""
        if not fact_id or measure != "T110": return None
    return dict(fact_id=fact_id, driver=driver, topic=topic, dataset_id=table,
                actual_projection="Actual", year=year, geography_code="00", geography_name="전국",
                dimension_2_code=dim_code, dimension_2_name=dim_name,
                dimension_3_code="", dimension_3_name="", measure_code=measure,
                measure_name=item.get("ITM_NM") or measure,
                value_raw=normalized_value(item.get("DT")), unit=item.get("UNIT_NM") or "",
                source_url=source_url(table), retrieved_at=today)


def validate(rows):
    lookup = {(row["fact_id"], row["year"], row["measure_code"]): row for row in rows}
    if len(lookup) != len(rows): raise ValueError("Duplicate supplemental observations")
    years = {row["year"] for row in rows if row["fact_id"] == "D05"}
    for year in years:
        spouse = float(lookup[("D05", year, "T00")]["value_raw"])
        dual = float(lookup[("D05", year, "T10")]["value_raw"])
        reported = float(lookup[("D05", year, "T20")]["value_raw"])
        if spouse <= 0 or abs(dual / spouse * 100 - reported) > 0.2:
            raise ValueError(f"D05 share mismatch in {year}")
    for year in {row["year"] for row in rows if row["fact_id"] == "L01"}:
        if lookup[("L01", year, "T10")]["value_raw"] != lookup[("L01", year, "T20")]["value_raw"]:
            raise ValueError(f"Nationwide inward/outward movers disagree in {year}")
    for fact_id in TIME_USE.values():
        if not all((fact_id, year, "T10") in lookup for year in (2014, 2019, 2024)):
            raise ValueError(f"Missing five-year lifestyle series: {fact_id}")
        for row in (row for row in rows if row["fact_id"] == fact_id):
            if not re.fullmatch(r"\d{1,2}:\d{2}", row["value_raw"]):
                raise ValueError(f"Invalid time-use value: {fact_id}/{row['year']}")
    for year in (2015, 2020):
        total = int(lookup[("H03", year, "T10")]["value_raw"])
        parts = sum(int(lookup[("H03", year, f"T{n}")]["value_raw"]) for n in range(11, 17))
        if total != parts: raise ValueError(f"Tenure components disagree in {year}")
    for fact_id in SPENDING.values():
        if not all((fact_id, year, "T110") in lookup for year in range(2019, 2026)):
            raise ValueError(f"Missing annual spending series: {fact_id}")
        if any(float(row["value_raw"]) < 0 for row in rows if row["fact_id"] == fact_id):
            raise ValueError(f"Negative spending value: {fact_id}")


def fix_catalog(conn):
    updates = {
        "D05": ("DT_1ES4F09S 시도별 맞벌이 가구", "2015–2025", 2025),
        "H03": ("DT_1PE1502 / DT_1PE2002 거처의 종류별·점유형태별 가구", "2015, 2020 (5년 주기 표본)", 2020),
        "LS03": ("DT_1TS202001 평균시간(10세 이상)", "2014, 2019, 2024 (5년 주기)", 2024),
        "LS04": ("DT_1TS202001 평균시간(10세 이상)", "2014, 2019, 2024 (5년 주기)", 2024),
        **{fact_id: ("DT_1L9U101 가구당 월평균 가계수지 (전국, 1인 이상)", "2019–2025", 2025)
           for fact_id in SPENDING.values()},
    }
    for fact_id, (table, period, latest) in updates.items():
        record = conn.execute("SELECT record_json FROM catalog WHERE fact_id=?", (fact_id,)).fetchone()
        data = json.loads(record[0])
        data["Table ID 또는 데이터 식별자"] = table
        data["제공 기간"] = period
        data["최신 데이터 기준연도"] = latest
        if fact_id == "H03":
            data["갱신 주기"] = "5년"
            data["원본 URL"] = source_url("DT_1PE2002")
            data["데이터 품질 및 한계"] = "2015·2020년 표본조사. 주택 소유 여부가 아니라 거주 거처의 점유형태이며 연간 보간 금지"
        elif fact_id in ("LS03", "LS04"):
            data["갱신 주기"] = "5년"
            data["원본 URL"] = source_url("DT_1TS202001")
        elif fact_id == "D05": data["원본 URL"] = source_url("DT_1ES4F09S")
        elif fact_id in SPENDING.values():
            data["원본 URL"] = source_url("DT_1L9U101")
            data["데이터 품질 및 한계"] = "2019년 이후 현행 가계동향조사 계열. 과거 가계동향조사와 조사설계 단절을 검토하기 전에는 연결 금지; 명목 원/가구/월"
        conn.execute("UPDATE catalog SET record_json=? WHERE fact_id=?", (json.dumps(data, ensure_ascii=False), fact_id))


def refresh():
    key = os.environ.get("KOSIS_API_KEY", "")
    if not key: raise SystemExit("KOSIS_API_KEY is required")
    today = dt.date.today().isoformat()
    current_year = dt.date.today().year
    responses = {}
    staged = []
    for table, period, start, dimensions in SOURCES:
        source_key = f"{table}_{dimensions.get('objL4', start)}"
        items = fetch(table, period, start, dimensions, key, current_year)
        responses[source_key] = items
        staged.extend(row for item in items if (row := map_row(table, item, today)) is not None)
    validate(staged)
    conn = connect()
    try:
        check(conn)
        changes = 0
        with conn:
            for row in staged: changes += insert_row(conn, row, revisions=True)
            fix_catalog(conn)
            check(conn)
        if changes:
            directory = ROOT / "data" / "raw" / today
            directory.mkdir(parents=True, exist_ok=True)
            for source_key, items in responses.items():
                (directory / f"{source_key}.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print(json.dumps({"supplemental_rows": len(staged), "changed_observations": changes}, ensure_ascii=False))
    finally:
        conn.close()


if __name__ == "__main__": refresh()
