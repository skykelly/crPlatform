"""수동 지식 입력 도구. 채팅으로 받은 자료를 기록(patches.jsonl)으로 옮긴다.

흐름 (기본: 검토 후 반영)
  1. stage    원본 보관 + 접수 메타 생성
       python3 tools/intake.py stage <파일> --title "..." --slug <영문> [--author ..] [--date YYYY-MM-DD] [--url ..] [--grade A|B|C]
  2. (Claude) 주장 추출 → 질문 매핑 → 기존 기록 대조 → 원문 확인 → intake/<ID>.proposal.json 작성
  3. preview  검토 카드(마크다운 표) 출력 → 채팅에 그대로 붙인다
       python3 tools/intake.py preview <ID>
  4. apply    승인한 항목만 질문별 patches.jsonl에 쓰고 build_records.py를 돌린다
       python3 tools/intake.py apply <ID> [--only 1,2,5 | --skip 3,4]
  5. (Claude) 아티클 문장 손보기(apply가 손볼 위치를 알려줌) → render_article.py → site/build_site.py → 점검 → 커밋 → 게시
  기타: list (접수 목록), leads [질문] (미확인 단서 목록)

저장 위치
  inbox/<ID>/      원본 (git 제외 — 저장소가 공개라 남의 글 전문을 올리지 않는다)
  intake/<ID>.json 접수 메타·처리 결과 (커밋됨: 제목·저자·날짜·URL·항목별 결과)
  intake/<ID>.proposal.json  반영 후보 (커밋됨: 주장 요약과 출처 링크만, 원문 전문은 넣지 않는다)

proposal.json 항목 형식 (items 배열)
  {"n": 1, "q": "I3", "op": "revise", "id": "I3-M-007", "kind": "갱신", "why": "...",
   "set": {...}, "add_sources": [...], "add_flags": [...], "add_basis": [...],
   "impact": "판정 영향|문장 수정|참고", "claim": "자료 속 주장 요약", "status": "확인|부분 확인|미확인"}
  {"n": 2, "q": "I2", "op": "add", "record": {...전체 기록...}, "impact": ..., "claim": ..., "status": ...}
  {"n": 3, "q": "I1", "op": "lead", "claim": "...", "reason": "원문 미확인 / C등급 단독"}
"""
import argparse, datetime, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
from records import KIND_ORDER, GRADES  # noqa: E402

INBOX, INTAKE = ROOT / "inbox", ROOT / "intake"
CAT = json.loads((ROOT / "site" / "catalog.json").read_text(encoding="utf-8"))
QDIR = {q["no"]: ROOT / c["id"] / q["id"] for c in CAT["categories"] for q in c.get("questions", [])}
TODAY = datetime.date.today().isoformat()


def _slug(t):
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "-", t).strip("-").lower()
    return s[:40] or "doc"


def _meta(i):
    return json.loads((INTAKE / f"{i}.json").read_text(encoding="utf-8"))


def _save_meta(i, m):
    (INTAKE / f"{i}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _proposal(i):
    return json.loads((INTAKE / f"{i}.proposal.json").read_text(encoding="utf-8"))


def _records(q):
    p = QDIR[q] / "records.jsonl"
    return {r["id"]: r for r in (json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip())}


def cmd_stage(a):
    src = Path(a.file)
    i = f"{a.date or TODAY}-{a.slug or _slug(a.title)}"
    d = INBOX / i
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, d / src.name)
    INTAKE.mkdir(exist_ok=True)
    m = {"id": i, "title": a.title, "author": a.author, "published": a.date, "url": a.url, "grade": a.grade,
         "received": TODAY, "file": f"inbox/{i}/{src.name}", "status": "접수", "items": {}}
    _save_meta(i, m)
    print(i)


def validate(prop):
    """반영 전에 막아야 할 오류를 찾는다."""
    errs = []
    seen = {}
    for it in prop["items"]:
        n, q, op = it.get("n"), it.get("q"), it.get("op")
        if q not in QDIR:
            errs.append(f"#{n}: 없는 질문 {q}")
            continue
        recs = _records(q)
        if op == "revise":
            if it["id"] not in recs:
                errs.append(f"#{n}: {q}에 없는 기록 {it['id']}")
            if it.get("kind") not in KIND_ORDER:
                errs.append(f"#{n}: 변경 종류 오류 {it.get('kind')}")
            if not it.get("why"):
                errs.append(f"#{n}: 바꾼 이유(why) 없음")
        elif op == "add":
            r = it["record"]
            if r["id"] in recs or r["id"] in seen:
                errs.append(f"#{n}: 이미 있는 ID {r['id']}")
            seen[r["id"]] = n
            if not r["id"].startswith(q + "-"):
                errs.append(f"#{n}: ID {r['id']}가 질문 {q}와 맞지 않음")
            if r.get("type") in ("지표", "사건"):
                srcs = r.get("sources") or []
                if not srcs or not all(s.get("url") for s in srcs):
                    errs.append(f"#{n}: 사실 기록에 원문 링크 없음")
                if srcs and all(s.get("grade") == "C" for s in srcs):
                    errs.append(f"#{n}: C등급 단독 근거")
        elif op != "lead":
            errs.append(f"#{n}: 알 수 없는 op {op}")
        for s in (it.get("add_sources") or []) + ((it.get("record") or {}).get("sources") or []):
            if s.get("grade") not in GRADES:
                errs.append(f"#{n}: 출처 등급 없음 ({s.get('publisher')})")
    return errs


def _short(t, n=70):
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def cmd_preview(a):
    m, prop = _meta(a.id), _proposal(a.id)
    errs = validate(prop)
    out = [f"**{m['title']}**" + (f" · {m['author']}" if m.get("author") else "") + (f" · {m['published']}" if m.get("published") else ""),
           f"자료 자체 등급: {m.get('grade') or '미정'} · 후보 {len(prop['items'])}건", ""]
    out += ["| # | 질문 | 대상 | 구분 | 바뀌는 내용 | 근거 | 영향 |", "|---|---|---|---|---|---|---|"]
    for it in prop["items"]:
        if it["op"] == "lead":
            continue
        if it["op"] == "revise":
            tgt, kind = it["id"], it["kind"]
            st = it.get("set", {}).get("statement")
            body = f"{_short(_records(it['q'])[it['id']]['statement'], 45)} → **{_short(st, 60)}**" if st else _short(it.get("why"), 90)
            srcs = it.get("add_sources") or []
        else:
            r = it["record"]
            tgt, kind = f"{r['id']} (신규 {r['type']})", "신규"
            body = _short(r["statement"], 100)
            srcs = r.get("sources") or []
        grade = "·".join(sorted({s.get("grade", "?") for s in srcs})) or "기존"
        out.append(f"| {it['n']} | {it['q']} | {tgt} | {kind} | {body} | {grade} · {it.get('status', '')} | {it.get('impact', '')} |")
    leads = [it for it in prop["items"] if it["op"] == "lead"]
    if leads:
        out += ["", "**단서로만 남길 것** (원문 미확인 또는 C등급 단독)", ""]
        out += [f"- #{it['n']} {it['q']}: {_short(it['claim'], 90)} — {it.get('reason', '')}" for it in leads]
    if errs:
        out += ["", "**반영 전 고칠 오류**", ""] + [f"- {e}" for e in errs]
    print("\n".join(out))


def _pick(items, only, skip):
    ns = {it["n"] for it in items}
    if only:
        keep = {int(x) for x in only.split(",")}
        return [it for it in items if it["n"] in keep]
    if skip:
        drop = {int(x) for x in skip.split(",")}
        return [it for it in items if it["n"] not in drop]
    return items


def cmd_apply(a):
    m, prop = _meta(a.id), _proposal(a.id)
    errs = validate(prop)
    if errs:
        sys.exit("반영 중단, 오류: " + "; ".join(errs))
    chosen = _pick(prop["items"], a.only, a.skip)
    chosen_n = {it["n"] for it in chosen}
    touched = {}
    for it in chosen:
        if it["op"] == "lead":
            m["items"][str(it["n"])] = {"result": "단서", "q": it["q"], "claim": it["claim"], "reason": it.get("reason")}
            continue
        base = {"on": a.on or TODAY, "intake": a.id}
        if it["op"] == "revise":
            p = {"op": "revise", "id": it["id"], "kind": it["kind"], "why": it["why"], **base}
            for k in ("set", "add_sources", "add_flags", "add_basis"):
                if it.get(k):
                    p[k] = it[k]
            rid = it["id"]
        else:
            p = {"op": "add", "record": it["record"], **base}
            rid = it["record"]["id"]
        with open(QDIR[it["q"]] / "patches.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        touched.setdefault(it["q"], []).append(rid)
        m["items"][str(it["n"])] = {"result": "반영", "q": it["q"], "id": rid, "op": it["op"]}
    for it in prop["items"]:
        if it["n"] not in chosen_n:
            m["items"][str(it["n"])] = {"result": "보류", "q": it["q"], "id": it.get("id") or (it.get("record") or {}).get("id"),
                                        "claim": it.get("claim")}
    m["status"] = "반영"
    m["applied_on"] = a.on or TODAY
    _save_meta(a.id, m)
    ok = True
    for q, ids in touched.items():
        r = subprocess.run([sys.executable, "build_records.py"], cwd=QDIR[q], capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        print(f"{q}: {last}")
        ok &= r.returncode == 0
        ra = (QDIR[q] / "render_article.py").read_text(encoding="utf-8").splitlines()
        hits = [f"    render_article.py:{k} {_short(line.strip(), 80)}" for k, line in enumerate(ra, 1) if any(f'"{i}"' in line for i in ids)]
        if hits:
            print(f"  아티클에서 확인할 곳 ({', '.join(ids)}):")
            print("\n".join(hits[:20]))
    print("반영 항목:", sorted(chosen_n), "· 보류:", sorted({it["n"] for it in prop["items"]} - chosen_n))
    sys.exit(0 if ok else 1)


def cmd_list(a):
    for p in sorted(INTAKE.glob("*.json")):
        if p.name.endswith(".proposal.json"):
            continue
        m = json.loads(p.read_text(encoding="utf-8"))
        res = {}
        for v in m["items"].values():
            res[v["result"]] = res.get(v["result"], 0) + 1
        print(f"{m['id']}  {m['status']}  {m['title']}  {res}")


def cmd_leads(a):
    for p in sorted(INTAKE.glob("*.json")):
        if p.name.endswith(".proposal.json"):
            continue
        m = json.loads(p.read_text(encoding="utf-8"))
        for n, v in m["items"].items():
            if v["result"] == "단서" and (not a.q or v["q"] == a.q):
                print(f"{v['q']}  [{m['id']} #{n}] {v['claim']} — {v.get('reason', '')}")


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sp = ap.add_subparsers(dest="cmd", required=True)
s = sp.add_parser("stage"); s.add_argument("file"); s.add_argument("--title", required=True); s.add_argument("--author")
s.add_argument("--date"); s.add_argument("--url"); s.add_argument("--slug", help="접수 ID용 영문 이름"); s.add_argument("--grade", choices=GRADES); s.set_defaults(f=cmd_stage)
s = sp.add_parser("preview"); s.add_argument("id"); s.set_defaults(f=cmd_preview)
s = sp.add_parser("apply"); s.add_argument("id"); s.add_argument("--only"); s.add_argument("--skip"); s.add_argument("--on")
s.set_defaults(f=cmd_apply)
s = sp.add_parser("list"); s.set_defaults(f=cmd_list)
s = sp.add_parser("leads"); s.add_argument("q", nargs="?"); s.set_defaults(f=cmd_leads)
a = ap.parse_args()
a.f(a)
