# 좌상단 메뉴(슬라이드 패널) 주입. build_site.py가 portal.py 다음에 exec한다.
# 모든 페이지에 같은 메뉴를 넣는다: 홈 · 전체 변경 이력 · 카테고리별 질문(아티클 링크 + 질문별 변경 건수 링크)
import re as _re

_chg_n = {}
for _c in changes:
    _chg_n[_c[1]] = _chg_n.get(_c[1], 0) + 1

MENU_CSS = """
.menubtn { display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--rule); background: var(--paper); color: var(--ink); border-radius: 6px; padding: 5px 10px 5px 8px; font: 500 13px/1.2 var(--mono); cursor: pointer; }
.menubtn:hover, .menubtn:focus-visible { border-color: var(--ink); }
.menubtn i, .menubtn i::before, .menubtn i::after { display: block; width: 14px; height: 2px; background: currentColor; border-radius: 1px; position: relative; }
.menubtn i::before, .menubtn i::after { content: ""; position: absolute; left: 0; }
.menubtn i::before { top: -4px; } .menubtn i::after { top: 4px; }
.sitebar .lhs { display: inline-flex; align-items: center; gap: 12px; min-width: 0; }
.topbar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20; background: var(--paper); border-bottom: 1px solid var(--rule); margin: 0 -20px; padding: 10px 20px; display: flex; align-items: center; gap: 12px; font: 600 13px/1.4 var(--mono); }
.topbar .brand { display: inline-flex; align-items: center; gap: 8px; color: var(--ink); text-decoration: none; }
.topbar .brand::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--signal); box-shadow: 0 0 0 3px var(--signal-soft); }
.menuscrim { position: fixed; inset: 0; z-index: 90; background: rgba(0,0,0,.45); opacity: 0; transition: opacity .2s; }
.menuscrim.on { opacity: 1; }
.menupanel { position: fixed; z-index: 100; top: 0; bottom: 0; left: 0; width: min(380px, 90vw); background: var(--paper); color: var(--ink); border-right: 1px solid var(--rule); box-shadow: 8px 0 32px rgba(0,0,0,.18); display: flex; flex-direction: column; transform: translateX(-102%); transition: transform .24s cubic-bezier(.2,.8,.2,1); padding-top: env(safe-area-inset-top, 0px); }
.menupanel.on { transform: none; }
@media (prefers-reduced-motion: reduce) { .menupanel, .menuscrim { transition: none; } }
.mp-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 2px solid var(--ink); font: 700 15px var(--mono); }
.mp-head button { border: 0; background: none; color: var(--muted); font: 500 22px/1 var(--body); cursor: pointer; padding: 2px 6px; }
.mp-body { overflow-y: auto; overscroll-behavior: contain; padding: 6px 0 calc(24px + env(safe-area-inset-bottom, 0px)); }
.mp-top { display: grid; margin: 6px 0 4px; }
.mp-top a, .mp-q a.main { color: var(--ink); text-decoration: none; }
.mp-top a { display: flex; justify-content: space-between; gap: 12px; padding: 10px 18px; font: 500 14px var(--body); }
.mp-top a:hover, .mp-q:hover { background: var(--panel); }
.mp-top a span { color: var(--muted); font: 500 12px var(--mono); }
.mp-cat { margin: 14px 0 0; padding: 6px 18px; font: 600 11px/1.4 var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); border-top: 1px solid var(--rule); }
.mp-q { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 8px; align-items: baseline; padding: 8px 18px; }
.mp-q .no { font: 600 12px var(--mono); color: var(--signal-ink); }
.mp-q a.main { font: 500 14px/1.45 var(--body); }
.mp-q a.main small { display: block; color: var(--muted); font-size: 12px; font-weight: 400; }
.mp-q .chg { font: 500 11px/1.6 var(--mono); border: 1px solid var(--rule); border-radius: 3px; padding: 0 6px; color: var(--ink); text-decoration: none; white-space: nowrap; background: none; display: inline; }
.mp-q .chg:hover, .mp-q .chg:focus-visible { border-color: var(--signal-ink); color: var(--signal-ink); }
.mp-q[aria-current="page"] { background: var(--signal-soft); }
.mp-q.planned .main { color: var(--muted); }
.mp-q.planned .main small { color: var(--muted); }
body.menuopen { overflow: hidden; }
"""

MENU_JS = """
(function () {
  var p = document.getElementById('menupanel'), s = document.getElementById('menuscrim'), last;
  if (!p || !s) return;
  function open() { last = document.activeElement; s.hidden = false; p.hidden = false; p.removeAttribute('inert');
    requestAnimationFrame(function () { p.classList.add('on'); s.classList.add('on'); });
    document.body.classList.add('menuopen'); document.querySelectorAll('.menubtn').forEach(function (b) { b.setAttribute('aria-expanded', 'true'); });
    var f = p.querySelector('.mp-x'); if (f) f.focus(); }
  function close() { p.classList.remove('on'); s.classList.remove('on'); document.body.classList.remove('menuopen');
    document.querySelectorAll('.menubtn').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
    setTimeout(function () { if (!p.classList.contains('on')) { p.hidden = true; s.hidden = true; p.setAttribute('inert', ''); } }, 260);
    if (last && last.focus) last.focus(); }
  document.querySelectorAll('.menubtn').forEach(function (b) { b.addEventListener('click', open); });
  s.addEventListener('click', close); p.querySelector('.mp-x').addEventListener('click', close);
  p.addEventListener('click', function (e) { var a = e.target.closest('a'); if (a && a.getAttribute('href').split('#')[0] === location.pathname.split('/').pop()) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && p.classList.contains('on')) close(); });
})();
"""

def _menu_html(prefix, cur_path):
    cats = ""
    for c, items in sections:
        rows = ""
        for it in items:
            q = it["q"]
            no = q["no"]
            if it["status"] != "live":
                rows += (f'<div class="mp-q planned"><span class="no">{E(no)}</span>'
                         f'<span class="main">{E(q.get("area") or "준비 중")}<small>준비 중</small></span><span></span></div>')
                continue
            a = it["cur"]
            n = _chg_n.get(no, 0)
            cur = ' aria-current="page"' if a["path"] == cur_path else ""
            chg = (f'<a class="chg" href="{prefix}changes.html#{E(no)}" title="{E(no)} 변경 이력 보기">변경 {n}</a>' if n else
                   '<span></span>')
            rows += (f'<div class="mp-q"{cur}><span class="no">{E(no)}</span>'
                     f'<a class="main" href="{prefix}{E(a["path"])}">{E(a["title"])}<small>{E(q.get("area", ""))}</small></a>{chg}</div>')
        cats += f'<p class="mp-cat">{int(c["no"]):02d} · {E(c["name"])}</p>{rows}'
    home_cur = ' aria-current="page"' if cur_path == "index" else ""
    dash_cur = ' aria-current="page"' if cur_path == "dashboard" else ""
    return (f'<div class="menuscrim" id="menuscrim" hidden></div>'
            f'<aside class="menupanel" id="menupanel" role="dialog" aria-modal="true" aria-label="페이지 바로가기" hidden inert>'
            f'<div class="mp-head"><span>{E(SITE_TITLE)}</span><button class="mp-x" type="button" aria-label="메뉴 닫기">×</button></div>'
            f'<div class="mp-body"><nav class="mp-top" aria-label="바로가기">'
            f'<a href="{prefix}index.html"{home_cur}>홈 · 신호 보드</a>'
            f'<a href="{prefix}dashboard.html"{dash_cur}>통계 대시보드<span>공식 통계</span></a>'
            f'<a href="{prefix}changes.html">전체 변경 이력<span>{changes_total}건</span></a></nav>{cats}</div></aside>')

_BTN = '<button class="menubtn" type="button" aria-haspopup="dialog" aria-controls="menupanel" aria-expanded="false"><i aria-hidden="true"></i>메뉴</button>'

def _inject(path, prefix, cur_path, portal_page=False):
    s = path.read_text(encoding="utf-8")
    if 'id="menupanel"' in s:
        return
    if portal_page:
        top = f'<div class="topbar">{_BTN}<a class="brand" href="index.html">{E(SITE_TITLE)}</a></div>'
        s = s.replace('<main class="portal">', top + '<main class="portal">', 1)
    else:
        s = _re.sub(r'(<a class="home" href="[^"]*">' + _re.escape(E(SITE_TITLE)) + '</a>)', lambda m: f'<span class="lhs">{_BTN}{m.group(1)}</span>', s, count=1)
    block = f'<style>{MENU_CSS}</style>{_menu_html(prefix, cur_path)}<script>{MENU_JS}</script>'
    if portal_page and "</body>" not in s:      # artifact_index.html: body 태그 없음
        s = s + block
    else:
        s = s.replace("</body>", block + "</body>", 1)
    path.write_text(s, encoding="utf-8")

def _inject_chat(path, prefix, page):
    s = path.read_text(encoding="utf-8")
    if 'id="chat-fab"' in s:
        return
    block = CHAT_TPL.replace("%%PREFIX%%", prefix).replace("%%PAGE%%", page)
    s = s.replace("</body>", block + "</body>", 1)
    path.write_text(s, encoding="utf-8")

_inject(DIST / "index.html", "", "index", True)
_inject(DIST / "artifact_index.html", "", "index", True)
_inject(DIST / "changes.html", "", "changes")
_inject(DIST / "dashboard.html", "", "dashboard")
for _p in pages:
    _inject(DIST / _p, "../../", _p)

# AI Chat: 포털 첫 화면 외 모든 페이지에도 같은 대화 창을 붙인다(현재 화면을 함께 알려 준다)
_inject_chat(DIST / "changes.html", "", "changes")
_inject_chat(DIST / "dashboard.html", "", "dashboard")
_qno = {it["cur"]["path"]: it["q"]["no"] for _c, _its in sections for it in _its if it["status"] == "live"}
for _p in pages:
    _inject_chat(DIST / _p, "../../", "question:" + _qno.get(_p, ""))
