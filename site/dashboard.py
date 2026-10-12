"""통계 대시보드: data/factbase.sqlite → site/dist/dashboard.html

build_site.py가 build(...)를 부른다. 단독 실행하면 계산 결과만 점검한다:
  python3 site/dashboard.py          # 카드별 계열 수·빈 계열 보고
카드 정의는 site/dashboard_spec.py. 값 계산은 여기서 끝내고 페이지 스크립트는 그리기만 한다.
탐색기에는 표마다 전국·시도 관측치를 모두 싣는다(시군구는 뺀다).
"""
import html
import json
import re
import sqlite3
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
sys.path.insert(0, str(SITE))
import dashboard_spec as SP  # noqa: E402

DB = ROOT / "data" / "factbase.sqlite"
MAP = ROOT / "data" / "indicator_map.json"
OFFICIAL = ROOT / "pipeline" / "official_tables.json"
ORG_NAME = {"101": "국가데이터처", "116": "국토교통부", "350": "국민건강보험공단", "177": "질병관리청",
            "114": "농림축산식품부", "170": "국무조정실"}
TIME = re.compile(r"(\d{1,3}):(\d{2})")
NUM = re.compile(r"-?\d+(\.\d+)?")
E = html.escape


def as_number(raw):
    raw = str(raw).strip().replace(",", "")
    m = TIME.fullmatch(raw)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return float(raw) if NUM.fullmatch(raw) else None


def clean_name(s):
    return re.sub(r"\s*\(14STD\d+\s*[^)]*\)", "", str(s or "")).strip()


def clean_unit(s):
    return re.sub(r"14STD\d+\s*", "", str(s or "")).strip()


class Facts:
    def __init__(self, conn):
        self.conn = conn
        self.obs, self.proj, self.geo_name = {}, set(), {}
        for t, ap, y, g, gn, d2, d3, m, raw in conn.execute(
                "SELECT dataset_id, actual_projection, year, geography_code, geography_name, dimension_2_code, dimension_3_code, measure_code, value_raw FROM observations"):
            v = as_number(raw)
            if v is None:
                continue
            self.obs.setdefault((t, m, d2 or "", d3 or "", g), {})[int(y)] = v
            self.geo_name[g] = gn
            if ap != "Actual":
                self.proj.add(t)

    # ---------- 식 계산 → {연도: 값}
    def ev(self, x, g=None):
        op = x["op"]
        if op == "sel":
            return dict(self.obs.get((x["t"], x["m"], x["d2"], x["d3"], g or x["g"]), {}))
        if op == "add":
            parts = [self.ev(a, g) for a in x["a"]]
            years = set.intersection(*(set(p) for p in parts)) if parts else set()
            return {y: sum(p[y] for p in parts) for y in years}
        if op == "ratio":
            a, b = self.ev(x["a"], g), self.ev(x["b"], g)
            return {y: a[y] / b[y] * x["scale"] for y in a if y in b and b[y]}
        if op == "either":
            out = {}
            for a in x["a"]:
                for y, v in self.ev(a, g).items():
                    out.setdefault(y, v)
            return out
        if op == "real":
            a, c = self.ev(x["a"], g), self.ev(x["cpi"], g)
            return {y: a[y] / (c[y] / 100) for y in a if y in c and c[y]}
        raise ValueError(op)


def sels(x, out=None):
    out = [] if out is None else out
    if isinstance(x, dict):
        if x.get("op") == "sel":
            out.append(x)
        for v in x.values():
            sels(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            sels(v, out)
    return out


def rnd(v, dp):
    return None if v is None else round(v, max(dp, 0) + 2)


def aligned(series_maps, dp):
    years = sorted(set().union(*[set(m) for m in series_maps])) if series_maps else []
    return years, [[rnd(m.get(y), dp) for y in years] for m in series_maps]


def table_titles(conn):
    titles = {}
    for (rec,) in conn.execute("SELECT record_json FROM catalog"):
        j = json.loads(rec)
        for part in re.split(r"\s*/\s*", str(j.get("Table ID 또는 데이터 식별자") or "")):
            m = re.match(r"(DT_[0-9A-Za-z_]+)\s+(.+)", part.strip())
            if m and m.group(1) not in titles:
                titles[m.group(1)] = re.sub(r"\s*\(.*?수록\)$", "", m.group(2).split(";")[0]).strip()
    try:
        for t in json.loads(OFFICIAL.read_text(encoding="utf-8"))["tables"]:
            titles[t["tbl"]] = t["title"]
    except FileNotFoundError:
        pass
    titles.setdefault("DT_1PE1502", "거처의 종류별·점유형태별 가구 (2015)")
    titles.setdefault("DT_1PE2002", "거처의 종류별·점유형태별 가구 (2020)")
    return titles


def org_for(t):
    sys.path.insert(0, str(ROOT / "pipeline"))
    try:
        import factbase
        return factbase.org_for(t)
    except Exception:
        return "101"


def compute(facts, card):
    t, dp = card["type"], card.get("fmt", {}).get("dp", 1)
    out = {k: card[k] for k in ("id", "title", "type", "fmt", "note", "cols", "proj") if k in card}
    if t == "line":
        maps = [facts.ev(s[1]) for s in card["series"]]
        out["years"], vals = aligned(maps, dp)
        out["series"] = [{"name": s[0], "proj": bool(s[2]) if len(s) > 2 else False, "v": v} for s, v in zip(card["series"], vals)]
    elif t in ("comp", "bars"):
        tot = facts.ev(card["total"]) if card.get("total") else None
        maps = []
        for _, x in card["parts"]:
            m = facts.ev(x)
            if tot is not None:
                m = {y: m[y] / tot[y] * 100 for y in m if y in tot and tot[y]}
            maps.append(m)
        out["years"], vals = aligned(maps, dp)
        out["series"] = [{"name": p[0], "v": v} for p, v in zip(card["parts"], vals)]
    elif t == "region":
        cand = sorted({g for (tt, m, d2, d3, g) in facts.obs for s in sels(card["expr"]) if tt == s["t"] and len(g) == 2 and g not in ("00", "03", "04", "05")})
        maps, names = [], []
        for g in cand:
            m = facts.ev(card["expr"], g)
            if m:
                maps.append(m); names.append(facts.geo_name.get(g, g))
        nat = facts.ev(card["expr"])
        out["years"], vals = aligned(maps + [nat], dp)
        out["series"] = [{"name": n, "v": v} for n, v in zip(names, vals)]
        out["national"] = vals[-1]
    elif t == "matrix":
        cells = []
        for rname, cols in card["rows"]:
            cells.append((rname, [facts.ev(x) for _, x in cols]))
        years = sorted(set().union(*[set(m) for _, row in cells for m in row]))
        out["years"] = years
        out["rows"] = [{"name": n, "v": [[rnd(m.get(y), dp) for y in years] for m in row]} for n, row in cells]
    elif t == "real":
        rows = []
        for name, nom, cp in card["rows"]:
            a, c = facts.ev(nom), facts.ev(cp)
            ys = sorted(y for y in a if y in c)
            if len(ys) < 2:
                rows.append({"name": name, "missing": True}); continue
            y0, y1 = ys[0], ys[-1]
            r0, r1 = a[y0] / (c[y0] / 100), a[y1] / (c[y1] / 100)
            rows.append({"name": name, "y0": y0, "y1": y1, "n0": round(a[y0]), "n1": round(a[y1]),
                         "nom": round((a[y1] / a[y0] - 1) * 100, 1), "cpi": round((c[y1] / c[y0] - 1) * 100, 1),
                         "real": round((r1 / r0 - 1) * 100, 1),
                         "series": {str(y): [round(a[y]), round(c[y], 2), round(a[y] / (c[y] / 100))] for y in ys}})
        out["rows"] = rows
    else:
        raise ValueError(t)
    return out


def empty_parts(c):
    if c["type"] == "real":
        return [r["name"] for r in c["rows"] if r.get("missing")]
    if c["type"] == "matrix":
        return [r["name"] for r in c["rows"] if all(all(v is None for v in col) for col in r["v"])]
    return [s["name"] for s in c.get("series", []) if all(v is None for v in s["v"])]


def rule_expr(rule):
    def one(spec):
        return SP.S(spec["dataset"], spec["measure"], spec.get("d2", ""), spec.get("d3", ""))
    if "num" in rule:
        return SP.ratio(SP.add(*map(one, rule["num"])), SP.add(*map(one, rule["den"])), rule.get("scale", 1))
    return SP.add(*map(one, rule["sum"]))


def card_maps(facts, spec):
    """카드에 그려지는 모든 계열(연도→값)."""
    t = spec["type"]
    if t == "line":
        return [facts.ev(s[1]) for s in spec["series"]]
    if t in ("comp", "bars"):
        tot = facts.ev(spec["total"]) if spec.get("total") else None
        out = []
        for _, x in spec["parts"]:
            m = facts.ev(x)
            out.append({y: m[y] / tot[y] * 100 for y in m if y in tot and tot[y]} if tot is not None else m)
        return out
    if t == "region":
        return [facts.ev(spec["expr"])]
    if t == "matrix":
        return [facts.ev(x) for _, cols in spec["rows"] for _, x in cols]
    if t == "real":
        return [facts.ev(r[1]) for r in spec["rows"]]
    return []


def same(a, b):
    ys = set(a) & set(b)
    return bool(ys) and all(abs(a[y] - b[y]) <= 1e-6 * max(1, abs(b[y])) for y in ys)


def record_links(facts, card_spec, maps, recs, pages):
    """카드가 그 기록과 같은 값을 그대로 보여 줄 때만 연결한다."""
    shown = card_maps(facts, card_spec)
    have = {(s["t"], s["m"]) for s in sels(card_spec)}
    out = []
    for rid, rule in maps.items():
        specs = [s for k in ("num", "den", "sum") for s in rule.get(k, [])]
        if rid not in recs or not all((s["dataset"], s["measure"]) in have for s in specs):
            continue
        target = facts.ev(rule_expr(rule))
        if target and any(same(m, target) for m in shown):
            q = rid.split("-")[0].lower()
            page = next((p for p in reversed(pages) if f"/{q}/" in p), None)
            if page:
                out.append({"id": rid, "q": rid.split("-")[0], "href": f"{page}#{rid}", "st": recs[rid]})
    return out


def load_records():
    recs = {}
    for f in ROOT.glob("*/*/records.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                recs[r["id"]] = r.get("statement", "")
    return recs


def explorer_tables(conn, titles):
    out = {}
    q = ("SELECT dataset_id, actual_projection, measure_code, measure_name, unit, dimension_2_code, dimension_2_name, dimension_3_code, dimension_3_name, "
         "geography_code, geography_name, year, value_raw, source_url FROM observations WHERE length(geography_code) <= 2 ORDER BY dataset_id, year")
    for t, ap, m, mn, unit, d2, d2n, d3, d3n, g, gn, y, raw, url in conn.execute(q):
        v = as_number(raw)
        if v is None:
            continue
        tb = out.setdefault(t, {"id": t, "title": titles.get(t, t), "proj": False, "url": url, "org": "",
                                "dims": {"m": {}, "d2": {}, "d3": {}, "g": {}}, "unit": {}, "rows": []})
        tb["proj"] = tb["proj"] or ap != "Actual"
        idx = []
        for key, code, name in (("m", m, mn), ("d2", d2 or "", d2n), ("d3", d3 or "", d3n), ("g", g, gn)):
            d = tb["dims"][key]
            if code not in d:
                d[code] = [len(d), clean_name(name) or "계"]
            idx.append(d[code][0])
        tb["unit"].setdefault(m, clean_unit(unit))
        tb["rows"].append(idx + [int(y), v if not float(v).is_integer() else int(v)])
    for t, tb in out.items():
        o = org_for(t)
        tb["org"] = ORG_NAME.get(o, f"기관 {o}")
        tb["url"] = f"https://kosis.kr/statHtml/statHtml.do?orgId={o}&tblId={t}"
        tb["unit"] = [tb["unit"].get(c, "") for c in sorted(tb["dims"]["m"], key=lambda c: tb["dims"]["m"][c][0])]
        tb["dims"] = {k: [[c, n] for c, (i, n) in sorted(d.items(), key=lambda kv: kv[1][0])] for k, d in tb["dims"].items()}
    return out


def catalog_status(conn):
    st = {}
    for fid, rec in conn.execute("SELECT fact_id, record_json FROM catalog"):
        j = json.loads(rec)
        n, y0, y1 = conn.execute("SELECT count(*), min(year), max(year) FROM observations WHERE fact_id=?", (fid,)).fetchone()
        st[fid] = {"id": fid, "metric": j.get("Metric", ""), "topic": j.get("Topic", ""), "n": n, "y0": y0, "y1": y1,
                   "src": j.get("Dataset / 통계명") or "", "kind": j.get("Actual / Official Projection", "")}
    return st


def model(pages=()):
    conn = sqlite3.connect(DB)
    facts = Facts(conn)
    titles = table_titles(conn)
    maps = json.loads(MAP.read_text(encoding="utf-8"))["records"]
    recs = load_records()
    cat = catalog_status(conn)
    tables = explorer_tables(conn, titles)
    secs, problems = [], []
    for sec in SP.SECTIONS:
        cards = []
        for spec in sec["cards"]:
            c = compute(facts, spec)
            bad = empty_parts(c)
            if bad:
                problems.append(f"{spec['id']}: 값 없음 {bad}")
            ts = sorted({s["t"] for s in sels(spec)})
            c["src"] = [{"id": t, "title": titles.get(t, t), "org": tables[t]["org"] if t in tables else "", "url": tables[t]["url"] if t in tables else ""} for t in ts]
            c["recs"] = record_links(facts, spec, maps, recs, list(pages))
            cards.append(c)
        facts_info = [cat[f] for f in sec["facts"] if f in cat]
        secs.append({"id": sec["id"], "no": sec["no"], "name": sec["name"], "lead": sec["lead"], "q": sec["q"], "cards": cards,
                     "facts": facts_info, "tables": sorted({s["id"] for c in cards for s in c["src"]})})
    tiles = []
    for t in SP.TILES:
        m = facts.ev(t["expr"])
        ys = sorted(m)
        tiles.append({"label": t["label"], "fmt": t["fmt"], "delta": t["delta"], "sec": t["sec"],
                      "y": ys[-1], "v": rnd(m[ys[-1]], t["fmt"]["dp"]), "py": ys[-2] if len(ys) > 1 else None,
                      "pv": rnd(m[ys[-2]], t["fmt"]["dp"]) if len(ys) > 1 else None})
    asof = conn.execute("SELECT max(retrieved_at) FROM observations").fetchone()[0]
    nobs = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    assigned = {f for s in SP.SECTIONS for f in s["facts"]}
    missing = sorted(set(cat) - assigned)
    if missing:
        problems.append(f"구분에 없는 카탈로그 항목: {missing}")
    qpath = {}
    for p in pages:
        q = p.split("/")[1].upper() if p.count("/") >= 2 else None
        if q:
            qpath[q] = p          # 같은 질문의 마지막 회차가 남는다
    return {"asof": asof, "qpath": qpath, "nobs": nobs, "ncat": len(cat), "tiles": tiles, "sections": secs, "tables": tables}, problems


LAST = None


def tile_html(t):
    """포털 첫 화면용 요약 타일 한 칸(대시보드 상단 타일과 같은 값·표기)."""
    f, v = t["fmt"], t["v"]
    if f["unit"] == "time":
        m = round(v); val = (f"{m // 60}시간 " if m >= 60 else "") + f"{m % 60}분"; unit = ""
    elif f["unit"] == "%":
        val = f"{v:.1f}%"; unit = ""
    else:
        val = f"{v:,.0f}"; unit = f"<small>{E(f['unit'])}</small>"
    d = ""
    if t.get("py") is not None and t.get("pv") is not None:
        cur, prev, mode = v, t["pv"], t["delta"]
        if mode == "p":
            x = cur - prev; txt = f"{x:+.1f}%p"
        elif mode == "min":
            x = round(cur - prev); txt = f"{x:+d}분" if x else "±0분"
        else:
            x = (cur / prev - 1) * 100; txt = f"{x:+.1f}%"
        txt = txt.replace("-", "−")
        if abs(x) < 0.05 and mode != "min":
            txt = "±0.0" + ("%p" if mode == "p" else "%")
        cls = "up" if x > 0 else "dn" if x < 0 else ""
        d = f" · {t['py']} 대비 <span class=\"{cls}\">{txt}</span>"
    return (f'<a class="ks-tile" href="dashboard.html#{t["sec"]}"><span class="ks-l">{E(t["label"])}</span>'
            f'<span class="ks-v">{val}{unit}</span><span class="ks-d">{t["y"]}{d}</span></a>')


def build(dist, head_css, site_title, ui_html, pages):
    data, problems = model(pages)
    if problems:
        raise SystemExit("대시보드 계산 문제:\n  " + "\n  ".join(problems))
    css = (SITE / "dashboard.css").read_text(encoding="utf-8")
    js = (SITE / "dashboard.js").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tabs = "".join(f'<button role="tab" type="button" data-sec="{s["id"]}" aria-selected="false"><b>{s["no"]}</b> {E(s["name"])}</button>' for s in data["sections"])
    page = (f'<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'<title>통계 대시보드 · {E(site_title)}</title>'
            f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600&family=Noto+Serif+KR:wght@600;800&display=swap">'
            f'<style>{head_css}{css}</style></head><body>'
            f'<div class="readbar" aria-hidden="true"><span></span></div><nav class="sitebar" aria-label="사이트"><a class="home" href="index.html">{E(site_title)}</a><span class="crumb">/ 통계 대시보드</span></nav>'
            f'<main class="dash" id="dash">'
            f'<header class="dhead"><p class="eyebrow"><span>공식 통계 팩트베이스</span><span>수집 기준 {E(data["asof"])}</span></p>'
            f'<h1>통계 대시보드</h1>'
            f'<p class="lead">KOSIS 공식 통계 {data["ncat"]}개 항목, 관측치 {data["nobs"]:,}건을 다섯 구분으로 나눴습니다. 값은 모두 공식 표에서 그대로 꺼내거나 표 안의 값끼리 계산했습니다. '
            f'점선은 공식 장래추계이며 실적과 섞지 않습니다. 카드 아래 번호는 이 값을 쓰는 리포트 기록입니다.</p></header>'
            f'<section class="tiles" aria-label="요약" id="tiles"></section>'
            f'<div class="dtabs" role="tablist" aria-label="구분">{tabs}<button role="tab" type="button" data-sec="x" aria-selected="false"><b>표</b> 전체 탐색기</button></div>'
            f'<div id="panels"></div>'
            f'<noscript><p>이 페이지는 자바스크립트로 차트를 그립니다.</p></noscript>'
            f'</main><div class="tip" id="tip" role="status" hidden></div>'
            f'<script type="application/json" id="dash-data">{payload}</script><script>{js}</script>{ui_html}</body></html>')
    (dist / "dashboard.html").write_text(page, encoding="utf-8")
    global LAST
    LAST = data
    return len(page)


if __name__ == "__main__":
    data, problems = model(["family/f1/r1.html", "family/f2/r1.html", "time-care/t1/r1.html", "time-care/t2/r1.html",
                            "residence/h1/r1.html", "residence/h2/r1.html", "needs/n1/r1.html", "needs/n2/r1.html"])
    for s in data["sections"]:
        print(s["no"], s["name"], "카드", len(s["cards"]), "표", len(s["tables"]), "기록 연결", sum(len(c["recs"]) for c in s["cards"]))
        for c in s["cards"]:
            ys = c.get("years") or []
            print(f"   {c['id']:<11} {c['type']:<6} {ys[0] if ys else '-'}~{ys[-1] if ys else '-'} 계열 {len(c.get('series') or c.get('rows') or [])} 기록 {[r['id'] for r in c['recs']]}")
    for t in data["tiles"]:
        print("타일", t["label"], t["y"], t["v"], t["py"], t["pv"])
    print("탐색기 표", len(data["tables"]), "행", sum(len(t["rows"]) for t in data["tables"].values()),
          "JSON", len(json.dumps(data, ensure_ascii=False, separators=(",", ":"))) // 1024, "KB")
    print("문제:", problems or "없음")
