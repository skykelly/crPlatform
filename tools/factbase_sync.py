"""팩트베이스(data/factbase.sqlite)와 지표 기록(records.jsonl)을 맞춰 본다.

data/indicator_map.json 에 대응을 적은 기록마다 DB에서 같은 값을 다시 계산해
  - 일치: 기록 값 = DB 값 (반올림 기준)
  - 값 다름: 같은 연도인데 값이 다르다 → 기록을 고칠지 검토
  - 새 연도: DB에 기록의 as_of보다 최신 연도가 있다 → 주간 조사에서 반영
을 보고한다. 기록은 고치지 않는다(문장 속 숫자도 함께 바뀌어야 하므로 반영은 사람이나 회차 작업이 한다).
보고서에 DB 시계열을 함께 적어, 증감폭에서 전년값을 역산하지 않게 한다.

실행: python3 tools/factbase_sync.py            # 보고서 출력 + data/sync_report.md
      python3 tools/factbase_sync.py --check    # 값 다름이 있으면 exit 1
"""
import json, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "factbase.sqlite"
MAP = ROOT / "data" / "indicator_map.json"
REPORT = ROOT / "data" / "sync_report.md"


def as_number(raw, kind):
    if kind == "time":
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", raw)
        return int(m.group(1)) * 60 + int(m.group(2)) if m else None
    try:
        return float(raw)
    except ValueError:
        return None


def series(conn, spec, kind=None):
    q = ("SELECT year, value_raw FROM observations WHERE dataset_id=? AND measure_code=? AND geography_code='00' "
         "AND actual_projection='Actual'")
    args = [spec["dataset"], spec["measure"]]
    for key, col in (("d2", "dimension_2_code"), ("d3", "dimension_3_code")):
        if key in spec:
            q += f" AND {col}=?"; args.append(spec[key])
    out = {}
    for year, raw in conn.execute(q, args):
        v = as_number(raw, kind)
        if v is not None:
            out[year] = out.get(year, 0) + v
    return out


def combined(conn, specs, kind=None):
    parts = [series(conn, s, kind) for s in specs]
    years = set.intersection(*(set(p) for p in parts)) if parts else set()
    return {y: sum(p[y] for p in parts) for y in years}


def compute(conn, rule):
    kind = rule.get("kind")
    if "num" in rule:
        num, den = combined(conn, rule["num"], kind), combined(conn, rule["den"], kind)
        vals = {y: num[y] / den[y] * rule.get("scale", 1) for y in num if y in den and den[y]}
    else:
        vals = combined(conn, rule["sum"], kind)
    r = rule.get("round", 1)
    return {y: (round(v) if r == 0 else round(v, r)) for y, v in sorted(vals.items())}


def load_records():
    recs = {}
    for f in ROOT.glob("*/*/records.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                recs[r["id"]] = (r, f.parent.relative_to(ROOT))
    return recs


def main(check=False):
    rules = json.loads(MAP.read_text(encoding="utf-8"))["records"]
    recs = load_records()
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows, counts = [], {"일치": 0, "값 다름": 0, "새 연도": 0, "기록 없음": 0, "DB 없음": 0}
    for rid, rule in rules.items():
        if rid not in recs:
            counts["기록 없음"] += 1; rows.append((rid, "기록 없음", "", "", "", "")); continue
        r, folder = recs[rid]
        vals = compute(conn, rule)
        if not vals:
            counts["DB 없음"] += 1; rows.append((rid, "DB 없음", r.get("value"), r.get("as_of"), "", "")); continue
        try:
            as_of = int(str(r.get("as_of"))[:4])
        except ValueError:
            as_of = None
        latest = max(vals)
        db_same = vals.get(as_of)
        rec_v = r.get("value")
        tol = 0.5 * 10 ** (-rule.get("round", 1)) if rule.get("round", 1) else 0.5
        if db_same is not None and isinstance(rec_v, (int, float)) and abs(db_same - rec_v) > tol:
            status = "값 다름"
        elif as_of is not None and latest > as_of:
            status = "새 연도"
        else:
            status = "일치"
        counts[status] += 1
        tail = ", ".join(f"{y}: {v:,}" for y, v in list(vals.items())[-6:])
        rows.append((rid, status, rec_v, r.get("as_of"), f"{latest}: {vals[latest]:,}", tail))
    conn.close()
    lines = ["# 팩트베이스 ↔ 지표 기록 대조", "",
             "data/indicator_map.json에 적은 기록만 대조한다. 기록은 바꾸지 않는다. "
             "'값 다름'·'새 연도'는 주간 조사나 다음 회차에서 기록과 문장을 함께 고친다.", "",
             "요약: " + " · ".join(f"{k} {v}" for k, v in counts.items() if v), "",
             "| 기록 | 상태 | 기록 값 | 기록 기준 | DB 최신 | DB 시계열(최근 6개) |", "|---|---|---|---|---|---|"]
    order = {"값 다름": 0, "새 연도": 1, "DB 없음": 2, "기록 없음": 3, "일치": 4}
    for row in sorted(rows, key=lambda x: (order[x[1]], x[0])):
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    text = "\n".join(lines) + "\n"
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    if check and counts["값 다름"]:
        sys.exit(1)


if __name__ == "__main__":
    main(check="--check" in sys.argv)
