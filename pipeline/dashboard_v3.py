#!/usr/bin/env python3
"""Publish a compact, source-traceable five-driver dashboard dataset."""

import json
from pathlib import Path

from factbase import ROOT, check, connect, source_url

OUT = ROOT / "archive" / "korea-life-fact-base-v2" / "dist" / "data" / "dashboard.json"


def observations(conn, table, measure, d2=None, d3=None, fact=None):
    conditions = ["dataset_id=?", "measure_code=?", "geography_code='00'", "actual_projection='Actual'"]
    args = [table, measure]
    if d2 is not None:
        conditions.append("dimension_2_code=?")
        args.append(d2)
    if d3 is not None:
        conditions.append("dimension_3_code=?")
        args.append(d3)
    if fact is not None:
        conditions.append("fact_id=?")
        args.append(fact)
    rows = conn.execute("SELECT year,value_raw FROM observations WHERE " + " AND ".join(conditions) + " ORDER BY year", args)
    data = {}
    for row in rows:
        try:
            data[row["year"]] = float(row["value_raw"])
        except ValueError:
            continue
    if not data:
        raise ValueError(f"Missing dashboard series: {table}/{measure}/{d2}/{d3}/{fact}")
    return data


def line(data, digits=1):
    return [{"year": year, "value": round(value, digits)} for year, value in sorted(data.items())]


def percent(numerator, denominator):
    return {year: 100 * value / denominator[year] for year, value in numerator.items() if year in denominator and denominator[year] > 0}


def minutes(data):
    output = {}
    for year, value in data.items():
        hours, minute = map(int, value.split(":"))
        if not (0 <= hours <= 24 and 0 <= minute < 60):
            raise ValueError(f"Invalid lifestyle time: {year}/{value}")
        output[year] = hours * 60 + minute
    return output


def raw_times(conn, code):
    rows = conn.execute("SELECT year,value_raw FROM observations WHERE dataset_id='DT_1TS202001' AND fact_id=? AND measure_code='T10' AND geography_code='00' ORDER BY year", (code,))
    result = {row["year"]: row["value_raw"] for row in rows}
    if set(result) != {2014, 2019, 2024}:
        raise ValueError(f"Lifestyle years changed: {code}/{sorted(result)}")
    return minutes(result)


def make(conn):
    quality = check(conn)
    total = observations(conn, "DT_1JC1516", "T10", "00")
    single = observations(conn, "DT_1JC1516", "T10", "50")
    couple = observations(conn, "DT_1JC1517", "T210", "0", "000")
    head_total = observations(conn, "DT_1JC1517", "T100", "0", "000")
    senior = {}
    for age in ("070", "075", "080", "085", "086"):
        for year, value in observations(conn, "DT_1JC1517", "T100", "0", age).items():
            senior[year] = senior.get(year, 0) + value
    if any(abs(total[y] - head_total[y]) > 0.5 for y in set(total) & set(head_total)):
        raise ValueError("Household totals disagree between demographic tables")
    dual = observations(conn, "DT_1ES4F09S", "T20", fact="D05")
    movers = observations(conn, "DT_1B26001_A01", "T10", fact="L01")
    marriage = observations(conn, "DT_1B8000G", "20", fact="L03")
    births = observations(conn, "DT_1B8000G", "10", fact="L04")
    sleep = raw_times(conn, "LS03")
    housework = raw_times(conn, "LS04")
    stock_total = observations(conn, "DT_1JU1501", "T10")
    stock_codes = {"T30": "아파트", "T20": "단독주택", "T50": "다세대주택", "T40": "연립주택", "T60": "비주거용 건물 내 주택"}
    stock = {label: observations(conn, "DT_1JU1501", code) for code, label in stock_codes.items()}
    stock_year = max(stock_total)
    if abs(sum(values[stock_year] for values in stock.values()) - stock_total[stock_year]) > 0.5:
        raise ValueError("Housing stock components do not sum to total")
    area = observations(conn, "DT_1JC1521", "T30", "00")
    tenure_total = {}
    tenure = {code: {} for code in ("T11", "T12", "T13", "T14", "T15", "T16")}
    for table in ("DT_1PE1502", "DT_1PE2002"):
        tenure_total.update(observations(conn, table, "T10", "00"))
        for code in tenure:
            tenure[code].update(observations(conn, table, code, "00"))
    if set(tenure_total) != {2015, 2020}:
        raise ValueError("Unexpected tenure years")
    if any(abs(sum(values[year] for values in tenure.values()) - tenure_total[year]) > 0.5 for year in tenure_total):
        raise ValueError("Tenure components do not sum to total")
    spending_codes = {"S01": "가전·가정용 기기", "S02": "가구·조명", "S03": "주택 유지·수선", "S04": "가사서비스", "S05": "주거·수도·광열"}
    spending = {label: observations(conn, "DT_1L9U101", "T110", fact=fact) for fact, label in spending_codes.items()}
    if any(set(values) != set(range(2019, 2026)) for values in spending.values()):
        raise ValueError("Spending series must cover 2019–2025")
    projection_total = observations_projection(conn, "T01")
    projection_single = observations_projection(conn, "T02")
    return {
        "schema_version": 3,
        "as_of": max(row[0] for row in conn.execute("SELECT retrieved_at FROM observations")),
        "quality": quality,
        "scope": "전국. 기준연도와 단위는 지표별 표시. 실제치와 공식 추계 분리.",
        "demographic": {
            "total_households": line(total, 0),
            "single_share": line(percent(single, total)),
            "couple_only_share": line(percent(couple, total)),
            "senior_head_share": line(percent(senior, head_total)),
            "dual_earner_share_of_married": line(dual),
            "source": [source_url("DT_1JC1516"), source_url("DT_1JC1517"), source_url("DT_1ES4F09S")],
            "note": "고령가구는 가구주 65세 이상, 맞벌이 비율의 분모는 유배우 가구. 전체 가구 비율과 직접 비교할 수 없다."
        },
        "life_event": {
            "movers": line(movers, 0), "marriages": line(marriage, 0), "births": line(births, 0),
            "source": [source_url("DT_1B26001_A01"), source_url("DT_1B8000G")],
            "note": "이동자 수는 국내 주소 이동 신고 인원이며 이사 건수나 이사 가구 수가 아니다."
        },
        "lifestyle": {
            "sleep_minutes": line(sleep, 0), "home_management_minutes": line(housework, 0),
            "source": [source_url("DT_1TS202001")],
            "note": "10세 이상, 요일평균, 주행동 기준 1일 평균시간. 5년 간격 관측이며 중간연도는 보간하지 않는다."
        },
        "home": {
            "housing_stock_total": line(stock_total, 0),
            "stock_mix": [{"label": label, "value": round(values[stock_year] / stock_total[stock_year] * 100, 1)} for label, values in stock.items()],
            "stock_year": stock_year,
            "mean_area_m2": line(area),
            "tenure": {"owner_share": line(percent(tenure["T11"], tenure_total)),
                       "jeonse_share": line(percent(tenure["T12"], tenure_total)),
                       "deposit_monthly_share": line(percent(tenure["T13"], tenure_total))},
            "source": [source_url("DT_1JU1501"), source_url("DT_1JC1521"), source_url("DT_1PE2002")],
            "note": "주택 재고의 유형 비중과 가구의 점유형태는 서로 다른 분모. 점유형태 최신 관측은 2020년 표본조사."
        },
        "spending": {
            "monthly_won_per_household": {label: line(values, 0) for label, values in spending.items()},
            "source": [source_url("DT_1L9U101")],
            "note": "전국 1인 이상 가구의 명목 월평균 원. 2019년 조사체계 이후 시계열이며 물가조정 전. 항목 간 합은 전체 Home & Living 지출이 아니다."
        },
        "official_projection": {
            "total_households": line(projection_total, 0),
            "single_person_households": line(projection_single, 0),
            "source": source_url("DT_1BZ0506"),
            "note": "장래가구추계. 실제치와 연결·합산하지 않고 추계 작성 시점과 가정을 확인해야 한다."
        },
    }


def observations_projection(conn, measure):
    rows = conn.execute("SELECT year,value_raw FROM observations WHERE dataset_id='DT_1BZ0506' AND actual_projection='Official Projection' AND measure_code=? AND geography_code='00' AND dimension_2_code='000' ORDER BY year", (measure,))
    values = {row["year"]: float(row["value_raw"]) for row in rows}
    if not values:
        raise ValueError(f"Missing projection: {measure}")
    return values


def main():
    conn = connect()
    try:
        data = make(conn)
    finally:
        conn.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"dashboard": str(OUT.relative_to(ROOT)), "observations": data["quality"]["observations"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
