#!/usr/bin/env python3
"""Collect the five-driver dashboard's additional official KOSIS series."""

import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request

import sys

from factbase import API, ROOT, check, connect, ensure_catalog, insert_row, normalized_value, org_for, source_url

# 가계동향 가계수지 항목 코드(C1) → fact_id. 같은 API 응답에 125개 항목이 오므로 표를 더 부르지 않는다.
SPENDING = {"L": "S05", "L3": "S03", "M0": "S02", "M4": "S01", "M9": "S04",
            "L6": "S08", "L5": "S09", "L1": "S10", "L4": "S11", "M5": "S12", "M8": "S13", "M2": "S14", "F": "S15"}
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
# 실패해도 나머지 수집을 막지 않는 보조 출처. 행동분류 전체(objL4=ALL)를 LS09로 받는다.
OPTIONAL_SOURCES = (
    ("DT_1TS202001", "F", 2014, {"objL1": "A0", "objL2": "S0", "objL3": "C1", "objL4": "ALL", "itmId": "T10"}),
)
TIME_RE = re.compile(r"\d{1,2}:\d{2}")


def fetch(table, period, start, dimensions, key, current_year):
    params = {"method": "getList", "apiKey": key, "orgId": org_for(table), "tblId": table,
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


def map_row(table, item, today, optional=False):
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
    elif table == "DT_1TS202001" and optional:
        # 행동분류 전체. 수면·가정관리는 LS03·LS04에 이미 있으니 건너뛰고, 시간이 아닌 값('-' 등)도 건너뛴다.
        if category in TIME_USE or not TIME_RE.fullmatch(normalized_value(item.get("DT"))): return None
        if (item.get("C1"), item.get("C2"), item.get("C3")) != ("A0", "S0", "C1"):
            raise ValueError("Unexpected lifestyle classification")
        fact_id, driver, topic = "LS09", "Lifestyle", "생활시간"
        dim_code, dim_name = category, item.get("C4_NM") or ""
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
    full = {(row["fact_id"], row["year"], row["dimension_2_code"], row["measure_code"]): row for row in rows}
    if len(full) != len(rows): raise ValueError("Duplicate supplemental observations")
    # 기존 검사는 (fact, year, measure)로 찾는다. 한 fact 안에서 차원이 하나뿐인 항목에만 쓴다.
    lookup = {(f, y, m): row for (f, y, d, m), row in full.items() if f != "LS09"}
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
    # 세부 항목은 소비지출(S15)보다 클 수 없다.
    for year in {row["year"] for row in rows if row["fact_id"] == "S15"}:
        total = float(lookup[("S15", year, "T110")]["value_raw"])
        for fact_id in SPENDING.values():
            if fact_id != "S15" and (fact_id, year, "T110") in lookup and float(lookup[(fact_id, year, "T110")]["value_raw"]) > total:
                raise ValueError(f"{fact_id} exceeds total consumption in {year}")
    # 주거·수도·광열(S05) = 실제주거비 + 주택유지및수선 + 상하수도 + 기타주거관련서비스 + 연료비
    parts = ("S10", "S03", "S11", "S09", "S08")
    for year in {row["year"] for row in rows if row["fact_id"] == "S05"}:
        if all((f, year, "T110") in lookup for f in parts):
            total = float(lookup[("S05", year, "T110")]["value_raw"])
            summed = sum(float(lookup[(f, year, "T110")]["value_raw"]) for f in parts)
            if abs(total - summed) > 5: raise ValueError(f"S05 components disagree in {year}: {total} vs {summed}")
    for row in (row for row in rows if row["fact_id"] == "LS09"):
        if not TIME_RE.fullmatch(row["value_raw"]): raise ValueError(f"Invalid time-use value: LS09/{row['year']}")


def fix_catalog(conn):
    updates = {
        "D05": ("DT_1ES4F09S 시도별 맞벌이 가구", "2015–2025", 2025),
        "H03": ("DT_1PE1502 / DT_1PE2002 거처의 종류별·점유형태별 가구", "2015, 2020 (5년 주기 표본)", 2020),
        "LS03": ("DT_1TS202001 평균시간(10세 이상)", "2014, 2019, 2024 (5년 주기)", 2024),
        "LS04": ("DT_1TS202001 평균시간(10세 이상)", "2014, 2019, 2024 (5년 주기)", 2024),
        **{fact_id: ("DT_1L9U101 가구당 월평균 가계수지 (전국, 1인 이상)", "2019–", None)
           for fact_id in SPENDING.values()},
    }
    for fact_id, (table, period, latest) in updates.items():
        record = conn.execute("SELECT record_json FROM catalog WHERE fact_id=?", (fact_id,)).fetchone()
        data = json.loads(record[0])
        data["Table ID 또는 데이터 식별자"] = table
        data["제공 기간"] = period
        if latest is None:
            latest = conn.execute("SELECT max(year) FROM observations WHERE fact_id=?", (fact_id,)).fetchone()[0]
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


def ingest(responses, optional_responses, today, raw_date=None):
    """API 응답(또는 저장된 원본)을 검증해 DB에 넣는다."""
    staged = []
    for (table, _), items in responses.items():
        staged.extend(row for item in items if (row := map_row(table, item, today)) is not None)
    for (table, _), items in optional_responses.items():
        staged.extend(row for item in items if (row := map_row(table, item, today, optional=True)) is not None)
    validate(staged)
    conn = connect()
    try:
        check(conn)
        changes = 0
        with conn:
            ensure_catalog(conn)
            for row in staged: changes += insert_row(conn, row, revisions=True)
            fix_catalog(conn)
            check(conn)
        if changes and raw_date is None:
            directory = ROOT / "data" / "raw" / today
            directory.mkdir(parents=True, exist_ok=True)
            for (_, source_key), items in {**responses, **optional_responses}.items():
                (directory / f"{source_key}.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        return {"supplemental_rows": len(staged), "changed_observations": changes,
                "optional_sources": [k[1] for k in optional_responses]}
    finally:
        conn.close()


def source_key(table, dimensions, start):
    return f"{table}_{dimensions.get('objL4', start)}"


def refresh():
    key = os.environ.get("KOSIS_API_KEY", "")
    if not key: raise SystemExit("KOSIS_API_KEY is required")
    today = dt.date.today().isoformat()
    current_year = dt.date.today().year
    responses, optional_responses = {}, {}
    for table, period, start, dimensions in SOURCES:
        responses[(table, source_key(table, dimensions, start))] = fetch(table, period, start, dimensions, key, current_year)
    for table, period, start, dimensions in OPTIONAL_SOURCES:
        try:
            optional_responses[(table, source_key(table, dimensions, start))] = fetch(table, period, start, dimensions, key, current_year)
        except Exception as exc:  # 보조 출처는 경고만 남긴다
            print(json.dumps({"optional_source_failed": table, "objL4": dimensions.get("objL4"), "error": str(exc)[:160]}, ensure_ascii=False))
    print(json.dumps(ingest(responses, optional_responses, today), ensure_ascii=False))


def from_raw(directory):
    """저장된 API 원본(data/raw/날짜/)을 다시 넣는다. 키가 필요 없다."""
    directory = ROOT / directory if not str(directory).startswith("/") else directory
    today = dt.date.today().isoformat()
    responses, optional_responses = {}, {}
    for table, period, start, dimensions in SOURCES + OPTIONAL_SOURCES:
        name = source_key(table, dimensions, start)
        path = directory / f"{name}.json"
        if not path.exists(): continue
        target = optional_responses if (table, period, start, dimensions) in OPTIONAL_SOURCES else responses
        target[(table, name)] = json.loads(path.read_text(encoding="utf-8"))
    result = ingest(responses, optional_responses, today, raw_date=directory.name)
    print(json.dumps({"from_raw": str(directory), **result}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--from-raw": from_raw(sys.argv[2])
    else: refresh()
