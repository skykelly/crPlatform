"""Life Signals 포털 생성기.

- site/catalog.json 의 카테고리·질문 목록을 읽고,
- 각 질문 폴더(<카테고리>/<질문>/article_rN.html)에서 아티클을 찾아
- site/dist/ 에 포털(index.html)과 회차별 아티클 페이지를 만든다.

새 질문·새 회차 아티클이 생기면 이 스크립트만 다시 돌리면 포털에 붙는다.
catalog.json 에 없는 질문 폴더도 아티클이 있으면 자동으로 포함한다.
"""
import html, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = SITE / "dist"
E = html.escape

cat = json.loads((SITE / "catalog.json").read_text(encoding="utf-8"))
SITE_TITLE = cat["site"]["title"]

def text_of(fragment):
    fragment = re.sub(r'<a class="rid"[^>]*>.*?</a>', "", fragment, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()

def parse_article(path):
    s = path.read_text(encoding="utf-8")
    def grab(pat):
        m = re.search(pat, s, re.S)
        return text_of(m.group(1)) if m else ""
    question = re.sub(r"^고정 질문 v[\d.]+ — ", "", grab(r'<p class="question">(.*?)</p>'))
    qver = (re.search(r"고정 질문 (v[\d.]+)", s) or [None, ""])[1]
    date = (re.search(r"R\d+ [^<]*?· (\d{4}-\d{2}-\d{2})", s) or [None, ""])[1]
    nrec = (re.search(r"4유형 기록 (\d+)건", s) or [None, ""])[1]
    return {"html": s, "title": grab(r"<h1>(.*?)</h1>"), "question": question, "qver": qver,
            "answer": grab(r'<p class="answer[^"]*">(.*?)</p>'), "date": date, "records": nrec}

def rounds_of(qdir):
    out = []
    for p in qdir.glob("article_r*.html"):
        m = re.match(r"article_r(\d+)\.html$", p.name)
        if m:
            out.append((int(m.group(1)), p))
    return sorted(out)

ARTICLE_UI = (SITE / "article_ui.html").read_text(encoding="utf-8")

def wrap_article(art, crumbs, rounds_html, depth):
    head, body = art["html"].split("<main>", 1)
    # 아티클 원본에 박힌 스타일을 최신 lib/article.css 로 교체
    head = re.sub(r"<style>.*?</style>", lambda m: "<style>" + ARTICLE_CSS + "</style>", head, count=1, flags=re.S)
    up = "../" * depth
    bar = (f'<div class="readbar" aria-hidden="true"><span></span></div>'
           f'<nav class="sitebar" aria-label="사이트"><a class="home" href="{up}index.html">{E(SITE_TITLE)}</a><span class="crumb">{crumbs}</span><span class="rounds">{rounds_html}</span></nav>')
    return (f'<!doctype html>\n<html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'{head}</head><body>{bar}<main>{body.replace("</body>", "").replace("</html>", "")}{ARTICLE_UI}</body></html>')

ARTICLE_CSS = (ROOT / "lib" / "article.css").read_text(encoding="utf-8")

# ---------------------------------------------------------------- 수집
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir(parents=True)

pages = []           # (published path, file)
sections = []
latest = []
for c in cat["categories"]:
    cdir = ROOT / c["id"]
    qs = list(c.get("questions", []))
    known = {q["id"] for q in qs}
    if cdir.exists():  # catalog에 없는 질문 폴더 자동 포함
        for d in sorted(p for p in cdir.iterdir() if p.is_dir() and re.fullmatch(r"[a-z]\d+", p.name)):
            if d.name not in known and rounds_of(d):
                qs.append({"id": d.name, "no": d.name.upper(), "area": ""})
    items = []
    for q in qs:
        rs = rounds_of(cdir / q["id"])
        if not rs:
            items.append({"q": q, "status": "planned"})
            continue
        arts = []
        for n, p in rs:
            a = parse_article(p); a["n"] = n
            sp = p.with_name(f"signal_r{n}.json")  # render_article.py가 판정 데이터에서 계산해 내보낸 칩·게이지
            a["signal"] = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
            a["path"] = f'{c["id"]}/{q["id"]}/r{n}.html'
            arts.append(a)
        for a in arts:
            links = " ".join(f'<a href="r{b["n"]}.html"{" aria-current=page" if b["n"]==a["n"] else ""}>R{b["n"]}</a>' for b in arts)
            crumbs = f'/ {E(c["name"])} / {E(q["no"])}'
            out = DIST / a["path"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(wrap_article(a, crumbs, links, 2), encoding="utf-8")
            pages.append(a["path"])
        cur = arts[-1]
        items.append({"q": q, "status": "live", "cur": cur, "arts": arts})
        latest.append((cur["date"], c, q, cur))
    sections.append((c, items))

exec(compile((SITE / "changes.py").read_text(encoding="utf-8"), "changes.py", "exec"))
# 통계 대시보드 (팩트베이스 → dashboard.html). 계산 문제가 있으면 빌드를 멈춘다
sys.path.insert(0, str(SITE))
import dashboard as _dash
dash_bytes = _dash.build(DIST, ARTICLE_CSS, SITE_TITLE, ARTICLE_UI.split("<script>")[0], pages)
exec(compile((SITE / "portal.py").read_text(encoding="utf-8"), "portal.py", "exec"))
exec(compile((SITE / "menu.py").read_text(encoding="utf-8"), "menu.py", "exec"))

# ---------------------------------------------------------------- 점검
bad = []
for p in [DIST / "index.html", DIST / "changes.html", DIST / "dashboard.html"] + [DIST / x for x in pages]:
    s = p.read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"#:]+\.html)"', s):
        if not (p.parent / href).resolve().exists():
            bad.append(f"{p.relative_to(DIST)} → {href}")
(DIST / "manifest.json").write_text(json.dumps({"pages": pages + ["changes.html", "dashboard.html"]}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"포털 생성: 카테고리 {len(sections)}, 질문 {total_q}, 아티클 페이지 {len(pages)}")
print("페이지:", pages, "+ changes.html, dashboard.html", f"(대시보드 {dash_bytes // 1024:,} KB)")
print("깨진 내부 링크:", bad or "없음")
sys.exit(1 if bad else 0)
