"""일간 Diff: 어제 스냅숏과 오늘 records.jsonl을 비교해 그날 바뀐 것만 changelog/<날짜>.json에 쌓는다.

사용:
  python3 lib/diff_day.py                 # 오늘(KST) 날짜로 비교·저장, 스냅숏 갱신
  python3 lib/diff_day.py --date 2026-10-22
  python3 lib/diff_day.py --round X1      # X1을 회차 재조사로 처리(기록별 항목 대신 한 줄)
  python3 lib/diff_day.py --baseline      # 현재 상태를 기준선으로 저장(변경 이력 비움)
  python3 lib/diff_day.py --dry-run       # 저장 없이 결과만 출력

- 스냅숏: state/snapshot.json (기록 ID → 비교 필드)
- 변경 이력: changelog/<YYYY-MM-DD>.json  {"date", "notes": [...], "items": [...]}
  같은 날 여러 번 돌리면 항목을 덧붙인다(덮어쓰지 않음). 변화가 없으면 notes에 '변화 없음'을 남긴다.
- 항목 종류: 신규, 판정(forecast_status·result 변경), 삭제, 그 밖의 변경은 그날 revisions의 kind(없으면 갱신).
"""
import argparse, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "state" / "snapshot.json"
LOG = ROOT / "changelog"
FIELDS = ("statement", "status", "forecast_status", "result", "value", "due", "period_start", "period_end",
          "condition", "method", "reasoning", "counter", "check_flags")


def current():
    out = {}
    for f in sorted(ROOT.glob("*/*/records.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r
    return out


def core(r):
    d = {k: r.get(k) for k in FIELDS if r.get(k) not in (None, [], "")}
    d["question"] = r.get("question")
    d["type"] = r.get("type")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--round", default="")
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--note", action="append", default=[])
    a = ap.parse_args()
    day = a.date or datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    cur = current()
    now = {i: core(r) for i, r in cur.items()}
    if a.baseline or not SNAP.exists():
        qs = sorted({v["question"] for v in now.values()})
        entry = {"date": day, "notes": [f"기준선: {len(qs)}개 질문 기록 {len(now)}건. 이 날짜 이전 변경은 이력에 남기지 않는다."] + a.note, "items": []}
        if not a.dry_run:
            SNAP.parent.mkdir(exist_ok=True); LOG.mkdir(exist_ok=True)
            SNAP.write_text(json.dumps(now, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            (LOG / f"{day}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
        print(entry["notes"][0]); return 0
    old = json.loads(SNAP.read_text(encoding="utf-8"))
    rounds = {x.strip().upper() for x in a.round.split(",") if x.strip()}
    items, notes = [], list(a.note)
    rcount = {}
    for i in sorted(set(old) | set(now)):
        o, n = old.get(i), now.get(i)
        q = (n or o)["question"]
        if o == n:
            continue
        if q in rounds:
            rcount[q] = rcount.get(q, 0) + 1
            continue
        if o is None:
            items.append({"q": q, "id": i, "kind": "신규", "now": n.get("statement"), "why": cur[i].get("added_why") or "새로 확인한 기록을 추가했다.", "origin": cur[i].get("origin")})
        elif n is None:
            items.append({"q": q, "id": i, "kind": "삭제", "before": o.get("statement"), "why": "기록을 삭제했다."})
        else:
            revs = [v for v in cur[i].get("revisions", []) if v.get("on") == day]
            if (o.get("forecast_status"), o.get("result")) != (n.get("forecast_status"), n.get("result")):
                kind, why = "판정", f"{o.get('forecast_status')} → {n.get('forecast_status')}" + (f": {n['result']}" if n.get("result") else "")
            else:
                kind = revs[-1]["kind"] if revs else "갱신"
                why = revs[-1]["why"] if revs else "기록 내용을 고쳤다."
            it = {"q": q, "id": i, "kind": kind, "now": n.get("statement"), "why": why, "origin": cur[i].get("origin")}
            if o.get("statement") != n.get("statement"):
                it["before"] = o.get("statement")
            items.append(it)
    for q, c in sorted(rcount.items()):
        notes.append(f"{q} 회차 재조사: 기록 {c}건 교체·추가")
    if not items and not rcount:
        notes.append("변화 없음")
    path = LOG / f"{day}.json"
    entry = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"date": day, "notes": [], "items": []}
    entry["items"] += items
    for x in notes:
        if x not in entry["notes"]:
            entry["notes"].append(x)
    if entry["items"] or any(x != "변화 없음" for x in entry["notes"]):
        entry["notes"] = [x for x in entry["notes"] if x != "변화 없음"]
    kinds = {}
    for x in items:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    print(f"{day}: 항목 {len(items)}건 {kinds or ''} | " + " / ".join(notes))
    if not a.dry_run:
        LOG.mkdir(exist_ok=True)
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
        SNAP.write_text(json.dumps(now, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
