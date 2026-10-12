"""Life Signals 공통 아티클 생성기.

질문 폴더의 render_article.py는 내용(한 줄 답·해석·라이프스테이지·판정 행)만 정하고 render(cfg)를 부른다.
순서: 한 줄 답 → 해석(+라이프스테이지) → 주요 사건 → 전망 → 판정 → 핵심 지표 → 미확인·경고

cfg 키
  QNO, CATEGORY, AREA, ROUND(int), DATE(YYYY-MM-DD), UPDATED(선택), QVER, TITLE, QUESTION
  ONE_LINE, ONE_LINE_BASIS, ANSWER_ROWS=[(항목, 문장, [근거])]
  NARRATIVE=[(문단, [근거])], LENS=[(라이프스테이지, 문장, [근거])]  # LIFE_STAGES 순서
  SIZE_LENS=[(평형대, 문장, [근거])]  # SIZE_BANDS 순서, 3개 모두. 근거 없으면 빈 목록
  EVENTS_LEAD, FORECAST_TITLE, FORECAST_LEAD
  JUDGE: {"scale": "dir"|"owner"|"rank"|"adoption", "title": 소제목, "lead": 설명, "rows": [...], "chip": 포털 칩, "gauge": 게이지 설명}
    dir      rows: {"item","value","direction","speed","prov","basis","note"}
    owner    rows: {"target","owner","second","prov","note","basis"}     # owner/second ∈ 가족|공공|시장|기술|경합
    rank     rows: {"rank","factor","size","trend","spaces","prov","basis"} # trend 예: "증가·가속"
    adoption rows: {"item","level","value","prov","basis","note"}          # level ∈ ADOPTION
    JUDGE["extra_html"](선택): 판정 표 아래 덧붙일 HTML(예: H2의 '변하는 공간과 기능' 표)
  METRICS_LEAD
"""
import html, json, re, sys
from pathlib import Path

LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB))
import judge as J

E = html.escape
LIFE_STAGES = ["청년 1인", "신혼·무자녀 부부", "자녀양육 가구", "중장년", "고령 가구"]
SIZE_BANDS = ["소형 (60㎡ 이하)", "중형 (60~100㎡)", "대형 (100㎡ 초과)"]
DIRCLS = {"증가": "up", "감소": "down", "정체": "flat", "강화": "up", "약화": "down", "중립": "flat"}


def render(cfg, folder):
    folder = Path(folder)
    recs = [json.loads(l) for l in (folder / "records.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by = {r["id"]: r for r in recs}
    inds = json.loads((folder / "indicators.json").read_text(encoding="utf-8"))
    ind_name = {i["id"]: i["name"] for i in inds}
    q, n = cfg["QNO"], cfg["ROUND"]
    css = (LIB / "article.css").read_text(encoding="utf-8")

    def tags(ids):
        missing = [i for i in ids if i not in by]
        if missing:
            raise KeyError(f"없는 기록 번호: {missing}")
        return "".join(f'<a class="rid" href="#{E(i)}" title="{E(by[i]["statement"])}">{E(i)}</a>' for i in ids)

    def para(text, ids):
        return f"<p>{E(text)} {tags(ids)}</p>"

    def src_links(r):
        return " · ".join(f'<a href="{E(s["url"])}" target="_blank" rel="noopener">{E(s["publisher"])}</a><span class="grade g{E(s["grade"])}">{E(s["grade"])}</span>'
                          for s in r.get("sources", []))

    def prov(p):
        return '<span class="prov-tag" title="기준을 직접 재는 수치가 없어 간접 근거로 판정">잠정</span>' if p else ""

    # 1. 한 줄 답
    answer_rows = "".join(f'<div class="arow"><dt>{E(k)}</dt><dd>{E(v)} {tags(ids)}</dd></div>' for k, v, ids in cfg["ANSWER_ROWS"])

    # 2. 해석 + 라이프스테이지
    narrative_html = "".join(para(t, ids) for t, ids in cfg["NARRATIVE"])
    irows = "".join(f"""<tr id="{E(r['id'])}"><td><span class="dir {DIRCLS[r['direction']]}">{E(r['direction'])}</span></td>
  <td class="tgt">{E(r['target'])}</td><td>{E(r['statement'])}</td><td>{tags(r['basis'])}</td><td class="idc"><code>{E(r['id'])}</code></td></tr>"""
                    for r in recs if r["type"] == "해석" and r.get("status", "유효") == "유효")
    lens = cfg.get("LENS", [])
    if [s for s, _, _ in lens] != LIFE_STAGES:
        raise ValueError(f"LENS는 {LIFE_STAGES} 순서로 5개 모두 적는다")
    slens = cfg.get("SIZE_LENS", [])
    if [s_ for s_, _, _ in slens] != SIZE_BANDS:
        raise ValueError(f"SIZE_LENS는 {SIZE_BANDS} 순서로 3개 모두 적는다")
    srows = "".join(f'<tr><td class="tgt">{E(s_)}</td><td>{E(t)}</td><td>{tags(ids) if ids else "<span class=muted>근거 없음</span>"}</td></tr>' for s_, t, ids in slens)
    lrows = "".join(f'<tr><td class="tgt">{E(s)}</td><td>{E(t)}</td><td>{tags(ids) if ids else "<span class=muted>근거 없음</span>"}</td></tr>' for s, t, ids in lens)

    # 3. 사건
    events = sorted([r for r in recs if r["type"] == "사건" and r.get("verified")], key=lambda r: r["date"], reverse=True)
    erows = "".join(f"""<li id="{E(r['id'])}"><time>{E(r['date'])}</time><div><b>{E(r.get('actor', ''))}</b> {E(r['statement'])}
  <div class="src">{src_links(r)} <code>{E(r['id'])}</code></div></div></li>""" for r in events) or '<li><time>—</time><div class="muted">원문을 확인한 사건이 없다.</div></li>'

    # 4. 전망
    scen = sorted([r for r in recs if r["type"] == "전망" and r.get("scenario")], key=lambda r: 0 if r["scenario"] == "낙관" else 1)
    scen_html = ""
    for r in scen:
        cls = "opt" if r["scenario"] == "낙관" else "pes"
        ms = "".join(f'<li><time>{E(m["by"])}</time><span>{E(m["text"])}</span></li>' for m in r.get("milestones", []))
        scen_html += f"""<article class="scen {cls}" id="{E(r['id'])}"><header><span class="sk">{E(r['scenario'])} · {'Optimistic' if cls == 'opt' else 'Pessimistic'}</span><code>{E(r['id'])}</code></header>
  <p class="sstmt">{E(r['statement'])}</p><ol class="ms">{ms}</ol>
  <dl class="sdl"><div><dt>판정 시점</dt><dd>{E(r['due'])}</dd></div><div><dt>판정 방법</dt><dd>{E(r['method'])}</dd></div>
  <div><dt>전제</dt><dd>{E(r.get('condition') or '없음')}</dd></div><div><dt>근거</dt><dd>{tags(r['basis'])}</dd></div></dl></article>"""
    sign = {}
    for r in scen:
        for sp in r.get("signposts", []):
            d = sign.setdefault(sp["id"], {"hit": set(), "miss": set()})
            if "on_hit" in sp: d["hit"].add(sp["on_hit"])
            if "on_miss" in sp: d["miss"].add(sp["on_miss"])

    def side(s):
        return "".join(f'<span class="side {"opt" if x == "낙관" else "pes"}">{E(x)}</span>' for x in sorted(s)) or '<span class="muted">—</span>'
    details = sorted([r for r in recs if r["type"] == "전망" and not r.get("scenario")], key=lambda r: r["due"])
    frows = "".join(f"""<tr id="{E(r['id'])}"><td class="stmt">{E(r['statement'])}<small>확인 방법: {E(r['method'])}</small></td>
  <td class="asof">{E(r['due'])}</td><td>{side(sign.get(r['id'], {}).get('hit', set()))}</td><td>{side(sign.get(r['id'], {}).get('miss', set()))}</td>
  <td><span class="fstat">{E(r.get('forecast_status', '진행 중'))}</span>{('<small>' + E(r['result']) + '</small>') if r.get('result') else ''}</td><td>{tags(r['basis'])}</td></tr>""" for r in details)

    # 5. 판정
    jd = cfg["JUDGE"]
    scale, rows = jd["scale"], jd["rows"]
    if scale == "dir":
        for x in rows:
            assert x["direction"] in J.DIRECTIONS and x["speed"] in J.SPEEDS, x
        jhead = ["항목", "현재값", "방향", "속도", "메모", "근거"]
        jrows = "".join(f"""<tr><td class="tgt">{E(x['item'])}</td><td>{E(x['value'])}</td>
  <td><span class="dir {DIRCLS[x['direction']]}">{E(x['direction'])}</span></td><td><span class="own neutral">{E(x['speed'])}</span>{prov(x.get('prov'))}</td>
  <td>{E(x.get('note', ''))}</td><td>{tags(x['basis'])}</td></tr>""" for x in rows)
        panel = J.criteria_panel([J.dir_block()], rules=J.DIR_RULES)
        n_acc = sum(1 for x in rows if x["speed"] == "가속")
        signal = {"kind": "dir", "items": [[x["item"], x["direction"], x["speed"], bool(x.get("prov"))] for x in rows],
                  "on": sum(1 for x in rows if x["direction"] != "정체" and x["speed"] != "둔화"), "of": len(rows),
                  "text": f"가속 {n_acc} · 유지 {sum(1 for x in rows if x['speed'] == '유지')} · 둔화 {sum(1 for x in rows if x['speed'] == '둔화')}"}
    elif scale == "owner":
        for x in rows:
            assert x["owner"] in J.OWNER_CLS, x
        jhead = ["돌봄 대상", "주도 주체", "다음 주체", "메모", "근거"]
        jrows = "".join(f"""<tr><td class="tgt">{E(x['target'])}</td><td>{J.chip(x['owner'], J.OWNER_CLS[x['owner']])}{prov(x.get('prov'))}</td>
  <td>{J.chip(x['second'], J.OWNER_CLS[x['second']]) if x.get('second') else '<span class=muted>—</span>'}</td><td>{E(x.get('note', ''))}</td><td>{tags(x['basis'])}</td></tr>""" for x in rows)
        panel = J.criteria_panel([J.owner_block()], rules=J.OWNER_RULES)
        cnt = {}
        for x in rows:
            cnt[x["owner"]] = cnt.get(x["owner"], 0) + 1
        signal = {"kind": "text", "on": sum(1 for x in rows if x["owner"] != "가족"), "of": len(rows),
                  "text": " · ".join(f"{k} 주도 {v}" for k, v in cnt.items())}
    elif scale == "rank":
        rows = sorted(rows, key=lambda x: x["rank"])
        jhead = ["순위", "요인", "규모", "방향·속도", "바꾸는 공간·기능", "근거"]
        jrows = "".join(f"""<tr><td class="num">{x['rank']}</td><td class="tgt">{E(x['factor'])}{prov(x.get('prov'))}</td><td>{E(x['size'])}</td>
  <td><span class="own neutral">{E(x['trend'])}</span></td><td>{E(x['spaces'])}</td><td>{tags(x['basis'])}</td></tr>""" for x in rows)
        panel = J.criteria_panel([J.rank_block()], rules=J.RANK_RULES)
        signal = {"kind": "text", "on": sum(1 for x in rows if "가속" in x["trend"] or "증가" in x["trend"]), "of": len(rows),
                  "text": " · ".join(f"{x['rank']}위 {x['factor']}" for x in rows[:3])}
    elif scale == "adoption":
        for x in rows:
            assert x["level"] in J.ADOPTION, x
        jhead = ["수요 유형", "단계", "이용률·규모", "메모", "근거"]
        jrows = "".join(f"""<tr><td class="tgt">{E(x['item'])}</td><td>{J.gauge(J.ADOPTION, x['level'], tip=J.adoption_tip(x['level']), prov=x.get('prov'))}{prov(x.get('prov'))}</td>
  <td>{E(x['value'])}</td><td>{E(x.get('note', ''))}</td><td>{tags(x['basis'])}</td></tr>""" for x in rows)
        panel = J.criteria_panel([J.adoption_block()], rules=J.ADOPTION_RULES)
        signal = {"kind": "band", "levels": J.ADOPTION, "items": [[x["item"], J.ADOPTION.index(x["level"]), bool(x.get("prov"))] for x in rows],
                  "on": sum(1 for x in rows if J.ADOPTION.index(x["level"]) >= 2), "of": len(rows)}
    else:
        raise ValueError(scale)
    jtable = f'<div class="tablewrap"><table><thead><tr>{"".join(f"<th>{E(h)}</th>" for h in jhead)}</tr></thead><tbody>{jrows}</tbody></table></div>'
    signal.update({"question": q, "round": n, "chip": jd["chip"], "gauge": jd.get("gauge", ""), "scale": scale})

    # 6. 지표
    metrics = sorted([r for r in recs if r["type"] == "지표" and r.get("status", "유효") == "유효"], key=lambda r: (r["indicator"], -r["importance"]))
    filled = {r["indicator"] for r in metrics if r.get("verified")}
    empty = [f"{i['id']} {i['name']}" for i in inds if i["id"] not in filled]

    def fmt_val(r):
        v, u = r.get("value"), r.get("unit", "")
        s = f"{v:,}" if isinstance(v, int) else (f"{v:g}" if isinstance(v, float) else str(v))
        return f"{s}{'' if str(u).startswith('%') else ' '}{u}"
    mrows = "".join(f"""<tr id="{E(r['id'])}"><td class="ind">{E(r['indicator'])}<small>{E(ind_name.get(r['indicator'], ''))}</small></td>
  <td class="stmt">{E(r['statement'])} {'<span class="warn">확인 필요</span>' if r.get('check_flags') else ''}<div class="src">{src_links(r)}</div></td>
  <td class="num">{E(fmt_val(r))}</td><td class="asof">{E(str(r['as_of']))}<small>{E(r.get('region', 'KR'))}</small></td><td class="idc"><code>{E(r['id'])}</code></td></tr>""" for r in metrics)
    itable = "".join(f"""<tr><td class="ind">{E(i['id'])}</td><td>{E(i['name'])}<small>{E(i.get('definition', ''))}</small></td><td>{E(i.get('source', ''))}{(' · 팩트베이스 ' + E(i['factbase'])) if i.get('factbase') else ''}</td>
  <td>{E(i.get('release', '확인 필요'))}</td><td>{'<span class="own brand">확보</span>' if i['id'] in filled else '<span class="own contest">미확보</span>'}</td></tr>""" for i in inds)

    # 7. 미확인·경고
    warns = [(r, "원문 미확인" if r["type"] in ("지표", "사건") and not r.get("verified") else "확인 필요") for r in recs
             if (r["type"] in ("지표", "사건") and not r.get("verified")) or r.get("check_flags")]
    wrows = "".join(f"""<tr><td><code>{E(r['id'])}</code></td><td><span class="wk">{E(k)}</span></td><td>{E(r['statement'])}</td><td class="muted">{E('; '.join(r.get('check_flags', [])))}</td></tr>""" for r, k in warns) \
        or '<tr><td colspan="4" class="muted">해당 기록 없음</td></tr>'
    counts = {t: sum(1 for r in recs if r["type"] == t) for t in ("지표", "사건", "해석", "전망")}
    upd = f'<span>갱신 {E(cfg["UPDATED"])} · <a href="../../changes.html#{E(q)}">변경 이력</a></span>' if cfg.get("UPDATED") else f'<span><a href="../../changes.html#{E(q)}">변경 이력</a></span>'

    page = f"""<title>{E(q)} {E(cfg['TITLE'])} R{n}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600&family=Noto+Serif+KR:wght@600;800&display=swap">
<style>{css}</style>
<main>
  <header class="narrow">
    <div class="eyebrow"><span>{E(cfg['CATEGORY'])}</span><span>{E(q)} · {E(cfg['AREA'])}</span><span>R{n} {'기준 회차' if n == 1 else '딥리서치 회차'} · {E(cfg['DATE'])}</span>{upd}</div>
    <h1>{E(cfg['TITLE'])}</h1>
    <p class="question">고정 질문 {E(cfg['QVER'])} — {E(cfg['QUESTION'])}</p>
  </header>
  <section class="answer-box"><h2>한 줄 답</h2>
    <p class="answer narrow">{E(cfg['ONE_LINE'])} {tags(cfg['ONE_LINE_BASIS'])}</p><dl class="arows">{answer_rows}</dl></section>
  <section><h2>해석</h2><div class="narrative">{narrative_html}</div>
    <div class="tablewrap"><table><thead><tr><th>방향</th><th>대상</th><th>해석</th><th>근거</th><th>기록</th></tr></thead><tbody>{irows}</tbody></table></div>
    <h3 class="subhead">라이프스테이지별로 보면</h3>
    <div class="tablewrap"><table><thead><tr><th>라이프스테이지</th><th>무엇이 바뀌나</th><th>근거</th></tr></thead><tbody>{lrows}</tbody></table></div>
    <h3 class="subhead">평형대별로 보면</h3>
    <div class="tablewrap"><table><thead><tr><th>평형대</th><th>무엇이 바뀌나</th><th>근거</th></tr></thead><tbody>{srows}</tbody></table></div></section>
  <section><h2>주요 사건 <small>최신순 · 원문 확인된 것만</small></h2><p class="lead">{E(cfg['EVENTS_LEAD'])}</p><ul class="timeline">{erows}</ul></section>
  <section><h2>전망 <small>{E(cfg['FORECAST_TITLE'])}</small></h2><p class="lead">{E(cfg['FORECAST_LEAD'])}</p>
    <div class="scens">{scen_html}</div>
    <h3 class="subhead">세부 판정 근거</h3>
    <p class="lead muted">각 세부 전망이 적중하거나 빗나갔을 때 어느 시나리오 쪽 신호인지 표시했다. 확인 시점이 오면 확인 방법대로 판정한다.</p>
    <div class="tablewrap"><table><thead><tr><th>세부 전망</th><th>확인 시점</th><th>적중 시</th><th>빗나갈 시</th><th>상태</th><th>근거</th></tr></thead><tbody>{frows}</tbody></table></div></section>
  <section><h2>판정 <small>{E(jd['title'])}</small></h2><p class="lead">{E(jd['lead'])}</p>{jtable}{jd.get('extra_html', '')}{panel}</section>
  <section><h2>핵심 지표 <small>추적 지표 {len(filled)}/{len(inds)}개 값 확보</small></h2><p class="lead">{E(cfg['METRICS_LEAD'])}</p>
    <div class="tablewrap"><table><thead><tr><th>추적 지표</th><th>내용 · 출처</th><th style="text-align:right">현재값</th><th>기준 시점</th><th>기록</th></tr></thead><tbody>{mrows}</tbody></table></div>
    <h3 class="subhead">추적 지표 목록 v{E(cfg['QVER'].lstrip('v'))}</h3>
    <div class="tablewrap"><table><thead><tr><th>ID</th><th>지표 · 정의</th><th>우선 출처</th><th>발표 시기</th><th>이번 회차</th></tr></thead><tbody>{itable}</tbody></table></div></section>
  <section><h2>미확인·경고 <small>본문 판단에서 빼거나 주의해서 쓴 기록</small></h2>
    <div class="tablewrap"><table><thead><tr><th>기록</th><th>구분</th><th>진술</th><th>사유</th></tr></thead><tbody>{wrows}</tbody></table></div></section>
  <footer>
    <span>이 글은 4유형 기록 {len(recs)}건(지표 {counts['지표']} · 사건 {counts['사건']} · 해석 {counts['해석']} · 전망 {counts['전망']})에서 생성했습니다. 문장 옆 번호를 누르면 해당 기록으로 이동합니다.</span>
    <span>출처 등급 A = 1차 조사·공식 통계, B = 주요 언론·2차 보도·연구기관, C = 블로그·출처 불명(원문 확인 전까지 판단에 쓰지 않음).</span>
  </footer>
</main>
"""
    out = folder / f"article_r{n}.html"
    out.write_text(page, encoding="utf-8")
    (folder / f"signal_r{n}.json").write_text(json.dumps(signal, ensure_ascii=False, indent=1), encoding="utf-8")

    anchors = set(re.findall(r'id="([A-Z]\d+-[A-Z]-\d{3})"', page))
    bad = sorted({i for i in re.findall(r'href="#([A-Z]\d+-[A-Z]-\d{3})"', page) if i not in anchors})
    heads = ("한 줄 답", "해석", "주요 사건", "전망", "판정", "핵심 지표", "미확인·경고")
    order = [page.index(f"<h2>{h}") for h in heads]
    print(f"{out.name} 생성, {len(page):,} bytes; 앵커 없는 근거 링크:", bad or "없음", "; 섹션 순서 정상:", order == sorted(order))
    print(f"signal_r{n}.json:", signal["chip"], f'{signal["on"]}/{signal["of"]}', "; 미확보 지표:", empty or "없음")
    if bad or order != sorted(order):
        sys.exit(1)
    return page
