# 변경 이력 페이지 생성 (build_site.py가 exec). 각 질문 records.jsonl의 revisions·added_on에서 모은다.
# 결과: dist/changes.html, 변수 changes_total
changes = []   # (날짜, 질문번호, 종류, 기록ID, 현재 진술, 이전 진술, 이유, 출처 구분)
day_notes = {}  # 날짜 → 메모(기준선, 회차 재조사, 변화 없음, 주간 요약)
_qpath = {}
for _c, _items in sections:
    for _it in _items:
        if _it["status"] == "live":
            _qpath[_it["q"]["no"]] = _it["cur"]["path"]
# 변경 이력의 원본은 lib/diff_day.py가 매일 쌓는 changelog/<날짜>.json 이다(기록에서 다시 만들지 않는다)
for _f in sorted((ROOT / "changelog").glob("*.json")):
    _d = json.loads(_f.read_text(encoding="utf-8"))
    day_notes[_d["date"]] = _d.get("notes", [])
    for _x in _d.get("items", []):
        if _x["q"] in _qpath:
            changes.append((_d["date"], _x["q"], _x["kind"], _x["id"], _x.get("now") or "", _x.get("before"), _x.get("why", ""), _x.get("origin")))
changes_total = len(changes)

sys.path.insert(0, str(ROOT / "lib"))
from records import KIND_ORDER, KIND_CLS, KIND_DEF

def _entry(c):
    on, no, kind, rid, now, before, why, origin = c
    href = _qpath.get(no, "#") + "#" + rid
    prev = f'<div class="was"><span>이전</span><p>{E(before)}</p></div>' if before else ""
    nowlab = "지금" if before else "내용"
    return (f'<li class="chg" data-kind="{E(kind)}"><div class="chead"><span class="ck {KIND_CLS[kind]}" title="{E(KIND_DEF[kind])}">{E(kind)}</span>'
            f'<a class="cid" href="{E(href)}">{E(rid)}</a>{"<span class=ck-src>제공 자료</span>" if origin == "manual" else ""}</div>'
            f'<p class="why">{E(why)}</p>{prev}<div class="now"><span>{nowlab}</span><p>{E(now)}</p></div></li>')

_by = {}
for c in changes:
    _by.setdefault(c[0], {}).setdefault(c[1], []).append(c)
_body = ""
for _on in sorted(set(_by) | set(day_notes), reverse=True):
    if _on not in _by:
        _body += f'<section class="day"><h2>{E(_on)}<small>{E(" · ".join(day_notes[_on]))}</small></h2></section>'
        continue
    _n = sum(len(v) for v in _by[_on].values())
    _kinds = {}
    for v in _by[_on].values():
        for c in v:
            _kinds[c[2]] = _kinds.get(c[2], 0) + 1
    _sum = " · ".join(f"{k} {_kinds[k]}" for k in KIND_ORDER if k in _kinds)
    _body += f'<section class="day"><h2>{E(_on)}<small>{_n}건 · {E(_sum)}</small></h2>'
    if day_notes.get(_on):
        _body += f'<p class="lead">{E(" · ".join(day_notes[_on]))}</p>'
    for _no in sorted(_by[_on]):
        _q = next(it["q"] for _c2, its in sections for it in its if it["status"] == "live" and it["q"]["no"] == _no)
        _body += f'<div class="qgrp" id="{E(_no)}"><h3><a href="{E(_qpath[_no])}">{E(_no)}</a><span>{E(_q.get("area",""))}</span></h3><ul>'
        for c in sorted(_by[_on][_no], key=lambda c: (KIND_ORDER.index(c[2]), c[3])):
            _body += _entry(c)
        _body += "</ul></div>"
    _body += "</section>"
if not _body:
    _body = '<p class="empty">아직 기록이 바뀐 적이 없습니다.</p>'
_legend = "".join(f'<li><span class="ck {KIND_CLS[k]}">{E(k)}</span>{E(KIND_DEF[k])}</li>' for k in KIND_ORDER)

CHANGES_CSS = """
.chgpage { max-width: 860px; margin: 0 auto; padding: 24px 20px 64px; display: flex; flex-direction: column; gap: 14px; }
.chgpage > * { margin-block: 0; }
.chgpage h1 { font: 800 clamp(26px, 4vw, 34px)/1.25 var(--serif, 'Noto Serif KR', serif); margin: 8px 0 0; text-wrap: balance; }
.chgpage .lead { color: var(--muted); margin: 0; max-width: 62ch; line-height: 1.7; }
.legend { list-style: none; margin: 6px 0 0; padding: 14px 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 8px 20px; border-block: 1px solid var(--rule); font-size: 13px; color: var(--muted); }
.legend li { display: flex; gap: 8px; align-items: baseline; }
.ck { flex: none; font: 600 11px/1.5 var(--mono); border: 1px solid currentColor; border-radius: 3px; padding: 0 6px; white-space: nowrap; }
.k-fix { color: var(--signal-ink); background: var(--signal-soft); border-color: transparent; }
.k-chg { color: var(--amber, var(--ink)); }
.k-chk { color: var(--muted); }
.k-new { color: var(--up, var(--ink)); }
.day h2 { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 14px; font: 600 18px var(--mono); margin: 32px 0 12px; padding-top: 14px; border-top: 2px solid var(--ink); }
.day h2 small { font: 400 13px var(--body); color: var(--muted); }
.qgrp { margin: 0 0 22px; }
.qgrp:target { outline: 2px solid var(--signal); outline-offset: 6px; border-radius: 4px; scroll-margin-top: 72px; }
.qgrp h3 { display: flex; gap: 10px; align-items: baseline; font: 600 15px var(--body); margin: 0 0 8px; }
.qgrp h3 a { font: 600 14px var(--mono); color: var(--signal-ink); }
.qgrp h3 span { color: var(--muted); font-weight: 400; font-size: 13px; }
.qgrp ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.chg { border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; display: grid; gap: 8px; background: var(--bg-elevated, var(--paper)); }
.chead { display: flex; gap: 10px; align-items: center; }
.ck-src { margin-left: auto; font: 500 11px/1.5 var(--mono); color: var(--muted); border: 1px dashed var(--rule); border-radius: 3px; padding: 0 6px; }
.cid { font: 500 12px var(--mono); color: var(--muted); text-decoration: none; }
.cid:hover, .cid:focus-visible { color: var(--signal-ink); text-decoration: underline; }
.chg .why { margin: 0; font-weight: 500; line-height: 1.6; }
.was, .now { display: grid; grid-template-columns: 38px 1fr; gap: 8px; font-size: 14px; line-height: 1.65; }
.was span, .now span { font: 500 11px/1.9 var(--mono); color: var(--muted); }
.was p { margin: 0; color: var(--muted); text-decoration: line-through; text-decoration-color: color-mix(in srgb, var(--muted) 50%, transparent); }
.now p { margin: 0; }
@media (max-width: 640px) { .was, .now { grid-template-columns: 1fr; gap: 0; } }
"""
_page = (f'<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
         f'<title>변경 이력 · {E(SITE_TITLE)}</title>'
         f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600&family=Noto+Serif+KR:wght@600;800&display=swap">'
         f'<style>{ARTICLE_CSS}{CHANGES_CSS}</style></head><body>'
         f'<div class="readbar" aria-hidden="true"><span></span></div><nav class="sitebar" aria-label="사이트"><a class="home" href="index.html">{E(SITE_TITLE)}</a><span class="crumb">/ 변경 이력</span></nav>'
         f'<main class="chgpage"><h1>변경 이력</h1>'
         f'<p class="lead">아티클에는 늘 최신 내용만 보입니다. 2026-10-21 기준선 이후 배치가 바뀐 기록(신규·갱신·판정·정정)과 이유, 바뀌기 전 문장을 날짜별로 쌓습니다. 변화가 없는 날도 한 줄로 남깁니다. 번호를 누르면 아티클의 해당 기록으로 이동합니다.</p>'
         f'<ul class="legend">{_legend}</ul>{_body}</main>{ARTICLE_UI}</body></html>')
(DIST / "changes.html").write_text(_page, encoding="utf-8")
