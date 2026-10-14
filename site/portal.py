# build_site.py 안에서 실행되는 포털 조립부. cat, sections, latest, E, ROOT, SITE, DIST 를 그대로 쓴다.
import datetime as _dt

TODAY = _dt.date.today()

# ---------- 기록에서 '이번 달 신호'와 '판정 임박 전망' 뽑기
q_path, q_meta = {}, {}
for c, items in sections:
    for it in items:
        if it["status"] == "live":
            q_path[it["q"]["no"]] = it["cur"]["path"]
            q_meta[it["q"]["no"]] = (c, it)

events, forecasts = [], []
for rec_file in sorted(ROOT.glob("*/*/records.jsonl")):
    for line in rec_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        qn = r.get("question")
        if qn not in q_path or r.get("status") not in (None, "유효"):
            continue
        if r["type"] == "사건" and r.get("importance") == 3 and r.get("date"):
            events.append(r)
        if r["type"] == "전망" and r.get("due") and not r.get("scenario") and r.get("forecast_status", "진행 중") == "진행 중":
            forecasts.append(r)

def _d(s):
    try:
        return _dt.date.fromisoformat(s[:10])
    except Exception:
        return None

events.sort(key=lambda r: r["date"], reverse=True)
recent = []
seen_q = {}
for r in events:  # 질문마다 최대 1건, 최근 순 8건
    if seen_q.get(r["question"]):
        continue
    seen_q[r["question"]] = 1
    recent.append(r)
    if len(recent) == 8:
        break

horizon = TODAY + _dt.timedelta(days=90)
due_soon = sorted((r for r in forecasts if _d(r["due"]) and TODAY <= _d(r["due"]) <= horizon), key=lambda r: (r["due"], r["id"]))

def short(t, n=88):
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"

def score_of(sg):
    """항목마다 1단계 0점 … 4단계 100점, 평균. 잠정도 같은 점수로 넣는다."""
    if sg.get("kind") != "band" or not sg.get("items"):
        return None
    top = len(sg["levels"]) - 1
    return round(sum(st / top * 100 for _, st, _ in sg["items"]) / len(sg["items"]))

# ---------- 타일
def pips(on, of):
    return "".join(f'<i class="{"on" if k < on else ""}" style="--k:{k}"></i>' for k in range(of))

def tile(c, it):
    q = it["q"]
    if it["status"] != "live":
        return f'<li class="tile planned"><div class="tno"><b>{E(q["no"])}</b><span>{E(q.get("area", ""))}</span></div><p class="ttl">{E(q.get("question", "고정 질문 설계 예정"))}</p><span class="chip muted">준비 중</span></li>'
    a = it["cur"]
    sg = it["cur"].get("signal", {})
    search = " ".join([q["no"], q.get("area", ""), a["title"], a["question"], a["answer"], sg.get("chip", "")]).lower()
    gauge, items_html = "", ""
    if sg.get("kind") == "band" and sg.get("items"):
        lv = sg["levels"]
        its = sorted(sg["items"], key=lambda x: (-x[1], x[2]))
        sc = score_of(sg)
        gauge = (f'<div class="gauge"><div class="score" title="항목마다 1단계 0점 · 2단계 33점 · 3단계 67점 · 4단계 100점의 평균">'
                 f'<b>{sc}</b><span>점</span><span class="bar" aria-hidden="true"><i style="--v:{sc}%"></i></span></div>'
                 f'<span class="glab">{E(sg["gauge"])} <b>{sg["on"]}/{sg["of"]}</b></span></div>')
        items_html = '<ul class="titems">' + "".join(
            f'<li><span class="seg s{st}{" prov" if pv else ""}"></span><span>{E(nm)}</span><em>{E(lv[st])}</em></li>' for nm, st, pv in its) + "</ul>"
    elif sg.get("kind") == "text":
        gauge = f'<div class="gauge"><span class="gtext">{E(sg["text"])}</span></div>'
    elif sg.get("kind") == "dir" and sg.get("items"):
        # 방향×속도 판정: items = [[항목, 방향(증가|정체|감소), 속도(가속|유지|둔화), 잠정 여부]]
        gauge = f'<div class="gauge"><span class="gtext">{E(sg.get("text", ""))}</span></div>'
        _ar = {"증가": "↑", "정체": "→", "감소": "↓"}
        items_html = '<ul class="titems dir">' + "".join(
            f'<li><span class="darr d-{ {"증가": "up", "정체": "flat", "감소": "down"}.get(d, "flat") }{" prov" if pv else ""}">{_ar.get(d, "·")}</span><span>{E(nm)}</span><em>{E(d)}·{E(sp)}{"(잠정)" if pv else ""}</em></li>'
            for nm, d, sp, pv in sg["items"]) + "</ul>"
    older = "".join(f' <a href="{E(b["path"])}">R{b["n"]}</a>' for b in it["arts"][:-1])
    return f"""<li class="tile" data-search="{E(search)}" data-q="{E(q['no'])}">
  <a class="tlink" href="{E(a['path'])}" data-preview>
    <div class="tno"><b>{E(q['no'])}</b><span>{E(q.get('area', ''))}</span></div>
    <h3 class="ttl">{E(a['title'])}</h3>
    {f'<span class="chip">{E(sg["chip"])}</span>' if sg.get("chip") else ''}
    {gauge}
  </a>
  <div class="tmore">
    <p class="tq">{E(a['question'])}</p>
    <p class="ta">{E(a['answer'])}</p>
    {items_html}
    <p class="tmeta"><span class="live">R{a['n']}</span><time>{E(a['date'])}</time><span>기록 {E(a['records'])}건</span><span>질문 {E(a['qver'])}</span>{older}</p>
  </div>
</li>"""

tabs_html = '<button class="tab" role="tab" id="tab-all" aria-controls="board" aria-selected="true" data-cat="all">전체 <span>{}</span></button>'.format(
    sum(1 for _, its in sections for i in its if i["status"] == "live"))
cols_html = ""
for c, items in sections:
    live = sum(1 for i in items if i["status"] == "live")
    tabs_html += f'<button class="tab" role="tab" id="tab-{E(c["id"])}" aria-controls="board" aria-selected="false" data-cat="{E(c["id"])}"><b>{c["no"]:02d}</b> {E(c["name"])} <span>{live}</span></button>'
    body = "".join(tile(c, it) for it in items) or '<li class="tile planned"><p class="ttl">고정 질문을 설계하는 중입니다.</p></li>'
    cols_html += f"""<section class="col" id="{E(c['id'])}" data-cat="{E(c['id'])}" aria-labelledby="h-{E(c['id'])}">
  <header class="colhead"><span class="cno">{c['no']:02d}</span><div><h2 id="h-{E(c['id'])}">{E(c['name'])}</h2><p>{E(c['desc'])}</p></div></header>
  <ol class="tiles">{body}</ol></section>"""

# ---------- 이번 달 신호
strip_html = ""
for r in recent:
    qn = r["question"]
    strip_html += (f'<li><a href="{E(q_path[qn])}#{E(r["id"])}"><span class="sm"><time>{E(r["date"])}</time><b>{E(qn)}</b></span>'
                   f'<span class="st">{E(short(r["statement"], 96))}</span></a></li>')

# ---------- 판정 임박 전망
by_month = {}
for r in due_soon:
    by_month.setdefault(r["due"][:7], []).append(r)
tl_html = ""
for ym, rs in by_month.items():
    y, m = ym.split("-")
    rows = ""
    for k, r in enumerate(rs):
        qn = r["question"]
        dleft = (_d(r["due"]) - TODAY).days
        rows += (f'<li{" class=extra" if k >= 5 else ""}><time>{E(r["due"][5:].replace("-", "/"))}</time><b>{E(qn)}</b>'
                 f'<a href="{E(q_path[qn])}#{E(r["id"])}">{E(short(r["statement"], 90))}</a><span class="dl">D-{dleft}</span></li>')
    more = f'<button class="more" type="button" aria-expanded="false">{len(rs) - 5}건 더 보기</button>' if len(rs) > 5 else ""
    tl_html += f'<div class="month"><h3><b>{int(m)}월</b><span>{y} · {len(rs)}건</span></h3><ol>{rows}</ol>{more}</div>'

total_q = sum(len(i) for _, i in sections)
total_live = sum(1 for _, its in sections for i in its if i["status"] == "live")
total_rec = sum(int(i["cur"]["records"] or 0) for _, its in sections for i in its if i["status"] == "live")
latest.sort(key=lambda x: x[0], reverse=True)
last_date = max([latest[0][0]] + [c[0] for c in changes]) if latest else "—"

# ---------- AI Chat 데이터 (포털 요약; 상세는 채팅이 아티클 페이지를 직접 읽는다)
_chat_q = []
for c, items in sections:
    for it in items:
        if it["status"] != "live":
            continue
        a, sg = it["cur"], it["cur"].get("signal", {})
        items_txt = ""
        if sg.get("kind") == "band":
            items_txt = ", ".join(f"{nm} {sg['levels'][st]}{'(잠정)' if pv else ''}" for nm, st, pv in sg["items"])
        elif sg.get("kind") == "text":
            items_txt = sg.get("text", "")
        elif sg.get("kind") == "dir":
            items_txt = ", ".join(f"{nm} {d}·{sp}{'(잠정)' if pv else ''}" for nm, d, sp, pv in sg.get("items", []))
        _chat_q.append({"no": it["q"]["no"], "cat": c.get("short", c["name"]), "title": a["title"], "question": a["question"],
                        "answer": a["answer"], "chip": sg.get("chip", ""), "score": score_of(sg), "items": items_txt,
                        "round": a["n"], "date": a["date"], "path": a["path"]})
CHAT_DATA = {"generated": str(TODAY), "categories": [f"{c['no']:02d} {c['name']}" for c, _ in sections], "questions": _chat_q,
             "events": [{"date": r["date"], "id": r["id"], "text": r["statement"]} for r in recent],
             "forecasts": [{"due": r["due"], "id": r["id"], "text": r["statement"]} for r in due_soon]}
CHAT_HTML = ((SITE / "chat.html").read_text(encoding="utf-8")
             .replace("%%ICON%%", (SITE / "ai_icon.txt").read_text(encoding="utf-8").strip())
             .replace("%%DATA%%", json.dumps(CHAT_DATA, ensure_ascii=False).replace("</", "<\\/")))
CHAT_TPL = CHAT_HTML                                     # 다른 페이지용: %%PREFIX%%·%%PAGE%% 자리 유지
CHAT_HTML = CHAT_TPL.replace("%%PREFIX%%", "").replace("%%PAGE%%", "index")

CSS = (ROOT / "lib" / "article.css").read_text(encoding="utf-8").split("/* 한 줄 답 */")[0]
PORTAL_CSS = (SITE / "portal.css").read_text(encoding="utf-8")
PORTAL_JS = (SITE / "portal.js").read_text(encoding="utf-8")

_DASH_SECS = [("d", "01", "인구·가구"), ("e", "02", "생애사건"), ("t", "03", "생활시간·돌봄"), ("h", "04", "주거"), ("s", "05", "지출·물가"), ("x", "표", "전체 탐색기")]
dash_secs = "".join(f'<li><a href="dashboard.html#{k}"><b>{n}</b>{E(t)}</a></li>' for k, n, t in _DASH_SECS)
import dashboard as _dashmod
dash_tiles = "".join(_dashmod.tile_html(t) for t in _dashmod.LAST["tiles"])
portal = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(SITE_TITLE)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600&family=Noto+Serif+KR:wght@600;800&display=swap">
<style>{CSS}{PORTAL_CSS}</style></head>
<body><main class="portal">
  <header class="masthead">
    <div class="mh-text">
      <h1>{E(cat['site']['title'])}</h1>
      <p class="tag">{E(cat['site']['tagline'])}</p>
      <dl class="stats">
        <div><dt>카테고리</dt><dd data-count="{len(sections)}">{len(sections)}</dd></div>
        <div><dt>발행 아티클</dt><dd data-count="{total_live}">{total_live}</dd></div>
        <div><dt>근거 기록</dt><dd data-count="{total_rec}">{total_rec:,}</dd></div>
        <div><dt>판정 대기 전망</dt><dd data-count="{len(forecasts)}">{len(forecasts)}</dd></div>
        <div><dt>변경 이력</dt><dd><a class="chg-link" href="changes.html">{changes_total}건</a></dd></div>
        <div><dt>최근 업데이트</dt><dd>{E(last_date)}</dd></div>
      </dl>
    </div>
  </header>

  <section class="kls" aria-labelledby="h-kls">
    <h2 id="h-kls">Korean Life Statistics</h2>
    <ol class="kls-nav">{dash_secs}</ol>
    <div class="kls-tiles">{dash_tiles}</div>
  </section>

  <section class="signals" aria-labelledby="h-signals">
    <div class="sechead"><h2 id="h-signals">최근 주요 사건</h2><p>중요도 3 사건을 질문마다 하나씩, 최근 순으로 모았습니다. 2회차부터는 판정 단계가 바뀐 질문이 여기에 먼저 올라옵니다.</p></div>
    <ol class="strip">{strip_html}</ol>
  </section>

  <section class="boardwrap" aria-labelledby="h-board">
    <div class="sechead row"><div><h2 id="h-board">신호 보드</h2><p>질문마다 이번 회차의 판정입니다. 방향×속도로 판정하는 질문은 빠르게 변하는 항목 수를, 채택 단계로 판정하는 질문은 단계 점수(1단계 0점, 4단계 100점의 평균)를 보여 줍니다. 카드를 가리키면 한 줄 답과 항목별 판정을 볼 수 있습니다.</p></div>
      <label class="search"><span class="vh">질문 검색</span><input id="q-search" type="search" placeholder="검색  /" autocomplete="off"><output id="q-count" aria-live="polite"></output></label></div>
    <div class="tabs" role="tablist" aria-label="카테고리">{tabs_html}<span class="tab-ink" aria-hidden="true"></span></div>
    <div class="board" id="board" data-view="all">{cols_html}</div>
    <p class="noresult" hidden>검색어와 맞는 질문이 없습니다. 다른 단어로 찾아보세요.</p>
  </section>

  <section class="due" aria-labelledby="h-due">
    <div class="sechead"><h2 id="h-due">판정 임박 전망</h2><p>앞으로 90일 안에 맞았는지 틀렸는지 판정할 전망 {len(due_soon)}건입니다. 판정일이 지나면 결과를 기록에 남깁니다.</p></div>
    <div class="months">{tl_html}</div>
  </section>

  <footer><span>{E(SITE_TITLE)} · 원본 기록과 생성 스크립트는 GitHub skykelly/crPlatform 저장소에 있습니다. 공식 통계 원값은 같은 저장소의 팩트베이스(data/factbase.sqlite)에 있습니다.</span></footer>
</main>
<div class="preview" id="preview" role="dialog" aria-modal="false" aria-labelledby="pv-title" hidden>
  <div class="pv-grip" aria-hidden="true"></div>
  <p class="pv-no"></p><h3 id="pv-title"></h3><span class="chip pv-chip"></span>
  <p class="tq pv-q"></p><p class="ta pv-a"></p><div class="pv-items"></div><p class="tmeta pv-meta"></p>
  <div class="pv-act"><a class="pv-go" href="#">아티클 읽기</a><button class="pv-x" type="button">닫기</button></div>
</div>
<div class="scrim" hidden></div>
<script>{PORTAL_JS}</script>
{CHAT_HTML}
</body></html>
"""
(DIST / "index.html").write_text(portal, encoding="utf-8")
# Claude 아티팩트 게시용 진입 페이지: 게시 시 문서 골격이 자동으로 씌워지므로 doctype·head·body 태그를 뺀다
entry = re.sub(r'^<!doctype html>\s*<html[^>]*><head><meta charset="utf-8"><meta name="viewport"[^>]*>', "", portal)
entry = entry.replace("</head>\n<body>", "").replace("</body></html>", "")
(DIST / "artifact_index.html").write_text(entry, encoding="utf-8")
print(f"이번 달 신호 {len(recent)}건, 판정 임박 전망 {len(due_soon)}건 (기준일 {TODAY})")
