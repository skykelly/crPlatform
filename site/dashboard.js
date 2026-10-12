(function () {
  'use strict';
  var D = JSON.parse(document.getElementById('dash-data').textContent);
  var root = document.getElementById('dash'), panels = document.getElementById('panels'), tip = document.getElementById('tip');
  var SER = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--s7', '--s8'];
  var renderers = [];   // 크기가 바뀌면 다시 그릴 차트

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function col(i) { return 'var(' + SER[i % SER.length] + ')'; }
  function num(v, dp) { return v.toLocaleString('ko-KR', { minimumFractionDigits: dp, maximumFractionDigits: dp }); }
  function hm(m) { m = Math.round(m); var h = Math.floor(Math.abs(m) / 60), r = Math.abs(m) % 60; return (m < 0 ? '−' : '') + (h ? h + '시간 ' : '') + r + '분'; }
  function fv(v, f, plain) {
    if (v == null || isNaN(v)) return '–';
    f = f || {};
    if (f.unit === 'time') return hm(v);
    var x = f.div ? v / f.div : v, s = num(x, f.dp == null ? 1 : f.dp);
    if (plain || !f.unit) return s;
    return s + (f.unit === '%' ? '%' : ' ' + f.unit);
  }
  function unitOf(f) { return f && f.unit && f.unit !== 'time' ? f.unit : ''; }
  // 증감: % 단위는 %p, 시간은 분, 그 밖은 증감률
  function delta(cur, prev, f, mode) {
    if (cur == null || prev == null) return '';
    var d, s;
    if (mode === 'p' || (f && f.unit === '%' && mode !== 'pct')) { d = cur - prev; s = (d > 0 ? '+' : d < 0 ? '−' : '±') + num(Math.abs(d), 1) + '%p'; }
    else if (mode === 'min' || (f && f.unit === 'time')) { d = Math.round(cur - prev); s = (d > 0 ? '+' : d < 0 ? '−' : '±') + Math.abs(d) + '분'; }
    else { if (!prev) return ''; d = (cur / prev - 1) * 100; s = (d > 0 ? '+' : d < 0 ? '−' : '±') + num(Math.abs(d), 1) + '%'; }
    return '<span class="' + (d > 0 ? 'up' : d < 0 ? 'dn' : '') + '">' + s + '</span>';
  }
  function lastIdx(arr) { for (var i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return i; return -1; }
  function firstIdx(arr) { for (var i = 0; i < arr.length; i++) if (arr[i] != null) return i; return -1; }

  // ---------------------------------------------------------------- 축 눈금
  function nice(lo, hi, n) {
    if (lo === hi) { var p = Math.abs(lo) || 1; lo -= p * .1; hi += p * .1; }
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / n))), err = n / span * step;
    if (err <= .15) step *= 10; else if (err <= .35) step *= 5; else if (err <= .75) step *= 2;
    var a = Math.floor(lo / step) * step, b = Math.ceil(hi / step) * step, t = [];
    for (var v = a; v <= b + step / 2; v += step) t.push(+v.toFixed(10));
    return t;
  }
  function tickLabel(v, f) {
    if (f && f.unit === 'time') { var h = Math.floor(v / 60), m = Math.round(v % 60); return h + ':' + (m < 10 ? '0' : '') + m; }
    var x = f && f.div ? v / f.div : v, a = Math.abs(x);
    var dp = a >= 100 ? 0 : a >= 10 ? (x % 1 ? 1 : 0) : (x % 1 ? (Math.abs(x * 10 % 1) > 1e-6 ? 2 : 1) : 0);
    return num(x, Math.min(dp, 3));
  }

  // ---------------------------------------------------------------- 선 그래프
  function lineChart(el, years, series, f, opt) {
    opt = opt || {};
    function draw() {
      var W = Math.max(280, el.clientWidth || 320), narrow = W < 460;
      var vis = series.filter(function (s) { return !s.off; });
      var lab = !narrow && vis.length > 1 && vis.length <= 4;
      var H = opt.h || 230, m = { t: 14, r: lab ? 118 : 14, b: 26, l: 48 };
      var vals = [];
      vis.forEach(function (s) { s.v.forEach(function (v) { if (v != null) vals.push(v); }); });
      if (!vals.length) { el.innerHTML = '<p class="note">값 없음</p>'; return; }
      var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
      if (lo > 0 && lo < hi * .45) lo = 0;
      var ticks = nice(lo, hi, 4), y0 = ticks[0], y1 = ticks[ticks.length - 1];
      var iw = W - m.l - m.r, ih = H - m.t - m.b, n = years.length;
      var X = function (i) { return m.l + (n === 1 ? iw / 2 : i * iw / (n - 1)); };
      var Y = function (v) { return m.t + ih - (v - y0) / (y1 - y0 || 1) * ih; };
      var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(opt.title || '') + '">';
      // 추계 구간
      var lastAct = -1;
      vis.forEach(function (sr) { if (!sr.proj) lastAct = Math.max(lastAct, lastIdx(sr.v)); });
      var hasProj = vis.some(function (sr) { return sr.proj && lastIdx(sr.v) > lastAct; });
      if (hasProj && lastAct >= 0 && lastAct < n - 1) {
        s += '<rect class="band" x="' + X(lastAct) + '" y="' + m.t + '" width="' + (X(n - 1) - X(lastAct)) + '" height="' + ih + '"/>';
        s += '<text class="bandl" x="' + (X(lastAct) + 6) + '" y="' + (m.t + 11) + '">공식 추계 →</text>';
      }
      ticks.forEach(function (t) { s += '<line class="gl" x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + Y(t) + '" y2="' + Y(t) + '"/><text x="' + (m.l - 6) + '" y="' + (Y(t) + 4) + '" text-anchor="end">' + tickLabel(t, f) + '</text>'; });
      if (y0 < 0 && y1 > 0) s += '<line class="ax" x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + Y(0) + '" y2="' + Y(0) + '"/>';
      var every = Math.max(1, Math.ceil(n / Math.floor(iw / 44)));
      years.forEach(function (yr, i) { if (i % every === 0 || i === n - 1) { if (i !== n - 1 && n - 1 - i < every) return; s += '<text x="' + X(i) + '" y="' + (H - 6) + '" text-anchor="middle">' + yr + '</text>'; } });
      var ends = [];
      series.forEach(function (sr, k) {
        if (sr.off) return;
        var d = '', pen = false;
        sr.v.forEach(function (v, i) { if (v == null) { pen = false; return; } d += (pen ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); pen = true; });
        var ck = sr.c != null ? sr.c : k;
        s += '<path class="ln' + (sr.proj ? ' proj' : '') + '" d="' + d + '" style="stroke:' + col(ck) + '"/>';
        var cnt = sr.v.filter(function (v) { return v != null; }).length;
        sr.v.forEach(function (v, i) { if (v != null && cnt <= 2) s += '<circle class="dot" cx="' + X(i) + '" cy="' + Y(v) + '" r="4" style="fill:' + col(ck) + '"/>'; });
        var li = lastIdx(sr.v);
        if (li >= 0) ends.push({ k: k, y: Y(sr.v[li]), x: X(li), name: sr.name });
      });
      if (lab) {
        ends.sort(function (a, b) { return a.y - b.y; });
        for (var i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 13) ends[i].y = ends[i - 1].y + 13;
        ends.forEach(function (e) { s += '<text class="dl" x="' + (W - m.r + 8) + '" y="' + (e.y + 4) + '">' + esc(e.name.length > 13 ? e.name.slice(0, 12) + '…' : e.name) + '</text>'; });
      }
      s += '<line class="xh" x1="0" x2="0" y1="' + m.t + '" y2="' + (m.t + ih) + '" visibility="hidden"/><g class="hd"></g>';
      s += '<rect x="' + m.l + '" y="' + m.t + '" width="' + iw + '" height="' + ih + '" fill="transparent" class="hit"/></svg>';
      el.innerHTML = s;
      var svg = el.querySelector('svg'), xh = svg.querySelector('.xh'), hd = svg.querySelector('.hd'), hit = svg.querySelector('.hit');
      function at(ev) {
        var r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * W / r.width;
        var i = n === 1 ? 0 : Math.round((px - m.l) / iw * (n - 1)); i = Math.max(0, Math.min(n - 1, i));
        xh.setAttribute('x1', X(i)); xh.setAttribute('x2', X(i)); xh.setAttribute('visibility', 'visible');
        var dots = '', rows = '';
        series.forEach(function (sr, k) {
          if (sr.off) return;
          var v = sr.v[i];
          var ck = sr.c != null ? sr.c : k;
          if (v != null) dots += '<circle class="dot" cx="' + X(i) + '" cy="' + Y(v) + '" r="4.5" style="fill:' + col(ck) + '"/>';
          rows += '<div><i class="' + (sr.proj ? 'proj' : '') + '" style="--c:' + col(ck) + '"></i><span>' + esc(sr.name) + '</span><span>' + fv(v, f) + '</span></div>';
        });
        hd.innerHTML = dots;
        tip.innerHTML = '<b>' + years[i] + (opt.yearSuffix || '') + '</b>' + rows;
        tip.hidden = false;
        var tw = tip.offsetWidth, th = tip.offsetHeight, tx = ev.clientX + 14, ty = ev.clientY - th - 10;
        if (tx + tw > window.innerWidth - 8) tx = ev.clientX - tw - 14;
        if (ty < 8) ty = ev.clientY + 16;
        tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
      }
      function out() { xh.setAttribute('visibility', 'hidden'); hd.innerHTML = ''; tip.hidden = true; }
      hit.addEventListener('pointermove', at); hit.addEventListener('pointerdown', at); hit.addEventListener('pointerleave', out);
    }
    draw();
    renderers.push({ el: el, draw: draw });
    return draw;
  }
  function legendHtml(series) {
    if (series.length < 2) return '';
    return '<ul class="legend">' + series.map(function (s, k) { return '<li><i class="' + (s.proj ? 'proj' : '') + '" style="--c:' + col(s.c != null ? s.c : k) + '"></i>' + esc(s.name) + '</li>'; }).join('') + '</ul>';
  }

  // ---------------------------------------------------------------- 막대 목록
  function hbars(names, vals, base, f, o) {
    o = o || {};
    var all = vals.concat(base || []).concat(o.nat != null ? [o.nat] : []).filter(function (v) { return v != null; });
    var mx = Math.max.apply(null, all.concat([0])) || 1;
    var rows = names.map(function (nm, i) {
      var v = vals[i], b = base ? base[i] : null;
      var d = b != null && v != null ? delta(v, b, f, o.share ? 'p' : null) : '';
      return '<li title="' + esc(nm + ': ' + fv(v, f)) + '"><span class="n' + (o.bold === i ? ' nat' : '') + '">' + esc(nm) + '</span><span class="track">' +
        (v != null ? '<span class="fill" style="width:' + Math.max(0, v / mx * 100).toFixed(2) + '%"></span>' : '') +
        (b != null ? '<span class="base" style="left:calc(' + (b / mx * 100).toFixed(2) + '% - 1px)"></span>' : '') +
        (o.nat != null ? '<span class="natline" style="left:' + (o.nat / mx * 100).toFixed(2) + '%"></span>' : '') +
        '</span><span class="v">' + fv(v, f) + (d ? '<small>' + d + '</small>' : '') + '</span></li>';
    }).join('');
    return '<ul class="hbars">' + rows + '</ul>';
  }

  // ---------------------------------------------------------------- 표
  function yearTable(years, series, f, projFrom) {
    var h = '<div class="dtable"><table><thead><tr><th>연도</th>' + series.map(function (s) { return '<th>' + esc(s.name) + '</th>'; }).join('') + '</tr></thead><tbody>';
    for (var i = years.length - 1; i >= 0; i--) {
      h += '<tr' + (projFrom != null && i > projFrom ? ' class="proj"' : '') + '><td>' + years[i] + '</td>' + series.map(function (s) { var v = s.v[i]; return '<td' + (v == null ? ' class="na"' : '') + '>' + fv(v, f, true) + '</td>'; }).join('') + '</tr>';
    }
    return h + '</tbody></table></div>';
  }
  function unitNote(f) { var u = unitOf(f); return u ? '<p class="note">단위: ' + esc(u) + '</p>' : (f && f.unit === 'time' ? '<p class="note">단위: 하루 평균 시간</p>' : ''); }

  // ---------------------------------------------------------------- 카드
  function yearSelect(years, cur, idx) {
    return '<select aria-label="기준 연도" data-ysel="' + idx + '">' + years.map(function (y, i) { return '<option value="' + i + '"' + (i === cur ? ' selected' : '') + '>' + y + '</option>'; }).join('') + '</select>';
  }
  function bestYear(c) {   // 값이 가장 많이 채워진 가장 최근 연도
    var best = -1, cnt = -1, ser = c.series || [];
    (c.years || []).forEach(function (y, i) {
      var k = 0;
      if (c.type === 'matrix') c.rows.forEach(function (r) { r.v.forEach(function (col) { if (col[i] != null) k++; }); });
      else ser.forEach(function (s) { if (s.v[i] != null) k++; });
      if (k >= cnt) { cnt = k; best = i; }
    });
    return best;
  }
  function footer(c) {
    var src = c.src.map(function (s) { return '<a href="' + esc(s.url) + '" target="_blank" rel="noopener" title="' + esc(s.org + ' · ' + s.title) + '">' + esc(s.id) + '</a> <span>' + esc(s.title) + '</span>'; }).join(' · ');
    var rec = c.recs.length ? '<div class="recs"><span class="k">리포트 기록</span>' + c.recs.map(function (r) { return '<a href="' + esc(r.href) + '" title="' + esc(r.st) + '">' + esc(r.id) + '</a>'; }).join('') + '</div>' : '';
    return '<footer><div class="srcs"><span class="k">출처(KOSIS)</span>' + src + '</div>' + rec + '</footer>';
  }
  function card(c, ci) {
    var f = c.fmt || {}, el = document.createElement('article');
    el.className = 'card' + (c.type === 'matrix' || c.type === 'real' ? ' wide' : '');
    el.id = 'c-' + c.id;
    var head = '', body = '', table = '';
    if (c.type === 'line') {
      var main = c.series.filter(function (s) { return !s.proj; })[0] || c.series[0], li = lastIdx(main.v), pi = -1;
      for (var i = li - 1; i >= 0; i--) if (main.v[i] != null) { pi = i; break; }
      head = '<div class="kv"><span class="big">' + fv(main.v[li], f) + '</span><span class="chg">' + (c.series.length > 1 ? esc(main.name) + ' · ' : '') + c.years[li] + (pi >= 0 ? ' · ' + c.years[pi] + ' 대비 ' + delta(main.v[li], main.v[pi], f) : '') + '</span></div>';
      body = '<div class="chart"></div>' + legendHtml(c.series);
      var lastAct = -1; c.series.forEach(function (s) { if (!s.proj) lastAct = Math.max(lastAct, lastIdx(s.v)); });
      table = yearTable(c.years, c.series, f, c.series.some(function (s) { return s.proj; }) ? lastAct : null);
    } else if (c.type === 'comp' || c.type === 'bars' || c.type === 'region') {
      var yi = bestYear(c);
      head = '<div class="kv"><span class="yr">기준 연도 ' + yearSelect(c.years, yi, ci) + '</span><span class="chg cmp"></span></div>';
      body = '<div class="bars"></div>';
      table = yearTable(c.years, c.series, f);
    } else if (c.type === 'matrix') {
      head = '<div class="kv"><span class="yr">기준 연도 ' + yearSelect(c.years, bestYear(c), ci) + '</span></div>';
      body = '<div class="mxw"></div>';
    } else if (c.type === 'real') {
      body = realTable(c);
    }
    el.innerHTML = '<header><h3>' + esc(c.title) + '</h3>' + head + '</header>' + body +
      (c.note ? '<p class="note">' + esc(c.note) + '</p>' : '') +
      (table ? '<details><summary>표로 보기 · 연도별 전체 값</summary>' + unitNote(f) + table + '</details>' : '') + footer(c);
    // 그리기
    if (c.type === 'line') {
      lineChart(el.querySelector('.chart'), c.years, c.series, f, { title: c.title });
    } else if (c.type === 'comp' || c.type === 'bars' || c.type === 'region') {
      var sel = el.querySelector('select'), box = el.querySelector('.bars'), cmp = el.querySelector('.cmp');
      var paint = function () {
        var i = +sel.value, j = -1, names = c.series.map(function (s) { return s.name; });
        for (var k = 0; k < i; k++) if (c.series.some(function (s) { return s.v[k] != null; })) { j = k; break; }
        var vals = c.series.map(function (s) { return s.v[i]; }), base = j >= 0 ? c.series.map(function (s) { return s.v[j]; }) : null;
        var nat = c.type === 'region' ? c.national[i] : null;
        if (c.type === 'region') {   // 값 순 정렬
          var ord = names.map(function (_, k) { return k; }).filter(function (k) { return vals[k] != null; }).sort(function (a, b) { return vals[b] - vals[a]; });
          names = ord.map(function (k) { return names[k]; }); base = base ? ord.map(function (k) { return base[k]; }) : null; vals = ord.map(function (k) { return vals[k]; });
        }
        var share = c.type === 'comp';
        box.innerHTML = '<div class="hbkey"><span><i class="kf"></i>' + c.years[i] + '</span>' + (base ? '<span><i class="kb"></i>' + c.years[j] + '</span>' : '') +
          (nat != null ? '<span><i class="kn"></i>전국 ' + fv(nat, f) + '</span>' : '') + (base ? '<span class="dkey">오른쪽 작은 숫자: ' + c.years[j] + ' 대비 ' + (share || f.unit === '%' ? '%p' : f.unit === 'time' ? '분' : '증감률') + '</span>' : '') + '</div>' +
          hbars(names, vals, base, f, { share: share, nat: nat });
        cmp.textContent = c.proj ? '공식 추계' : '';
      };
      sel.addEventListener('change', paint); paint();
    } else if (c.type === 'matrix') {
      var msel = el.querySelector('select'), mw = el.querySelector('.mxw');
      var mpaint = function () { mw.innerHTML = matrixTable(c, +msel.value); };
      msel.addEventListener('change', mpaint); mpaint();
    }
    return el;
  }
  function matrixTable(c, i) {
    var f = c.fmt || {}, colsN = c.cols.length, mx = [];
    for (var k = 0; k < colsN; k++) { var m = 0; c.rows.forEach(function (r) { var v = r.v[k][i]; if (v != null && v > m) m = v; }); mx.push(m || 1); }
    var share = f.unit === '%';
    var gm = Math.max.apply(null, mx);
    var h = '<div class="dtable mx"><table><thead><tr><th>' + (share ? '구분 (행 합계 100%)' : '구분') + '</th>' + c.cols.map(function (x) { return '<th>' + esc(x) + '</th>'; }).join('') + '</tr></thead><tbody>';
    c.rows.forEach(function (r) {
      var ind = /^\s/.test(r.name);
      h += '<tr><td' + (ind ? ' class="ind"' : '') + '>' + esc(r.name.trim()) + '</td>' + r.v.map(function (col, k) {
        var v = col[i], a = v == null ? 0 : (share ? v / gm : v / mx[k]) * .55;
        return '<td class="cell' + (v == null ? ' na' : '') + '" style="--a:' + a.toFixed(3) + '"><span>' + fv(v, f, true) + '</span></td>';
      }).join('') + '</tr>';
    });
    return h + '</tbody></table></div>' + unitNote(f) + (share ? '' : '<p class="note">칸 색이 진할수록 같은 열에서 값이 크다.</p>');
  }
  function realTable(c) {
    var ok = c.rows.filter(function (r) { return !r.missing; });
    var y0 = ok.length ? ok[0].y0 : '', y1 = ok.length ? ok[0].y1 : '';
    var mx = Math.max.apply(null, ok.map(function (r) { return Math.abs(r.real); }).concat([1]));
    var h = '<div class="dtable realt"><table><thead><tr><th>항목</th><th>' + y0 + ' 월평균(원)</th><th>' + y1 + ' 월평균(원)</th><th>명목 증감</th><th>물가 상승</th><th>실질 증감</th></tr></thead><tbody>';
    c.rows.forEach(function (r) {
      if (r.missing) { h += '<tr><td>' + esc(r.name) + '</td><td class="na" colspan="5">대응 물가지수 없음</td></tr>'; return; }
      var w = Math.abs(r.real) / mx * 60;
      h += '<tr><td>' + esc(r.name) + '</td><td>' + num(r.n0, 0) + '</td><td>' + num(r.n1, 0) + '</td><td>' + sgn(r.nom) + '</td><td>' + sgn(r.cpi) + '</td><td><span class="rb" style="width:' + w.toFixed(1) + 'px;background:' + (r.real >= 0 ? 'var(--pos)' : 'var(--neg)') + '"></span>' + sgn(r.real) + '</td></tr>';
    });
    return h + '</tbody></table></div>';
  }
  function sgn(v) { return '<span class="' + (v > 0 ? 'up' : v < 0 ? 'dn' : '') + '">' + (v > 0 ? '+' : v < 0 ? '−' : '±') + num(Math.abs(v), 1) + '%</span>'; }

  // ---------------------------------------------------------------- 구분 패널
  var QPATH = D.qpath || {};
  D.sections.forEach(function (s) { s.cards.forEach(function (c) { c.recs.forEach(function (r) { QPATH[r.q] = r.href.split('#')[0]; }); }); });
  function section(s) {
    var p = document.createElement('section');
    p.className = 'secp'; p.id = 'p-' + s.id; p.setAttribute('role', 'tabpanel');
    var ql = s.q.map(function (q) { return QPATH[q] ? '<a href="' + esc(QPATH[q]) + '">' + q + ' 아티클</a>' : q; }).join(' · ');
    p.innerHTML = '<header><h2><b>' + s.no + '</b> ' + esc(s.name) + '</h2><p class="lead">' + esc(s.lead) + '</p><p class="qlinks">관련 질문: ' + ql + ' · 카드 ' + s.cards.length + '개 · 출처 표 ' + s.tables.length + '개</p></header><div class="cards"></div>';
    var box = p.querySelector('.cards');
    s.cards.forEach(function (c, i) { box.appendChild(card(c, s.id + i)); });
    var cov = document.createElement('div'); cov.className = 'cov';
    var have = s.facts.filter(function (x) { return x.n; }).length;
    cov.innerHTML = '<h3>수집 현황 · ' + have + '/' + s.facts.length + ' 항목</h3><p class="note">회색 항목은 아직 공식 표가 연결되지 않았다. 다음 수집 대상이다.</p><ul class="covl">' + s.facts.map(function (x) {
      return '<li class="' + (x.n ? '' : 'miss') + '"><code>' + esc(x.id) + '</code><span>' + esc(x.metric) + '<small>' + (x.n ? x.y0 + '~' + x.y1 + ' · 관측치 ' + num(x.n, 0) + '건' + (x.kind === 'Official Projection' ? ' · 추계' : '') : '미수집 · ' + esc(x.src)) + '</small></span></li>';
    }).join('') + '</ul>';
    p.appendChild(cov);
    return p;
  }

  // ---------------------------------------------------------------- 탐색기
  function explorer() {
    var p = document.createElement('section');
    p.className = 'secp xp'; p.id = 'p-x'; p.setAttribute('role', 'tabpanel');
    var used = {}, groups = '';
    D.sections.forEach(function (s) {
      groups += '<optgroup label="' + s.no + ' ' + esc(s.name) + '">' + s.tables.map(function (t) { used[t] = 1; var tb = D.tables[t]; return tb ? '<option value="' + t + '">' + esc(tb.title) + ' (' + t + ')</option>' : ''; }).join('') + '</optgroup>';
    });
    var rest = Object.keys(D.tables).filter(function (t) { return !used[t]; });
    if (rest.length) groups += '<optgroup label="그 밖의 표">' + rest.map(function (t) { return '<option value="' + t + '">' + esc(D.tables[t].title) + ' (' + t + ')</option>'; }).join('') + '</optgroup>';
    var nrows = Object.keys(D.tables).reduce(function (a, t) { return a + D.tables[t].rows.length; }, 0);
    p.innerHTML = '<header><h2><b>표</b> 전체 탐색기</h2><p class="lead">팩트베이스의 공식 표 ' + Object.keys(D.tables).length + '개, 전국·시도 관측치 ' + num(nrows, 0) + '건을 그대로 봅니다. 분류를 고르고, 열로 펼칠 분류를 정하면 연도별 표와 선 그래프가 나옵니다.</p></header>' +
      '<div class="xctl"><label class="tbl">표<select id="x-t">' + groups + '</select></label><span id="x-dims" style="display:contents"></span></div>' +
      '<p class="xmeta" id="x-meta"></p><div class="chart" id="x-chart"></div><div class="legend xlegend" id="x-leg"></div><div id="x-table"></div>';
    var ts = p.querySelector('#x-t'), dimsBox = p.querySelector('#x-dims'), st = {};
    var DN = { m: '항목', d2: '분류 1', d3: '분류 2', g: '지역' };
    function setup() {
      var tb = D.tables[ts.value], dims = ['m', 'd2', 'd3', 'g'].filter(function (k) { return tb.dims[k].length > 1; });
      st = { tb: tb, fix: {}, spread: dims.indexOf('d2') >= 0 ? 'd2' : dims.indexOf('d3') >= 0 ? 'd3' : dims[0] || 'm', on: null };
      ['m', 'd2', 'd3', 'g'].forEach(function (k) { st.fix[k] = 0; });
      var h = '<label>열로 펼칠 분류<select data-spread>' + dims.map(function (k) { return '<option value="' + k + '">' + DN[k] + ' (' + tb.dims[k].length + ')</option>'; }).join('') + '</select></label>';
      dims.forEach(function (k) { h += '<label data-for="' + k + '">' + DN[k] + '<select data-dim="' + k + '">' + tb.dims[k].map(function (d, i) { return '<option value="' + i + '">' + esc(d[1]) + '</option>'; }).join('') + '</select></label>'; });
      dimsBox.innerHTML = dims.length ? h : '';
      var sp = dimsBox.querySelector('[data-spread]');
      if (sp) { sp.value = st.spread; sp.addEventListener('change', function () { st.spread = sp.value; st.on = null; paint(); }); }
      dimsBox.querySelectorAll('[data-dim]').forEach(function (s) { s.addEventListener('change', function () { st.fix[s.getAttribute('data-dim')] = +s.value; paint(); }); });
      paint();
    }
    function paint() {
      var tb = st.tb, K = { m: 0, d2: 1, d3: 2, g: 3 }, sp = st.spread;
      dimsBox.querySelectorAll('label[data-for]').forEach(function (l) { l.hidden = l.getAttribute('data-for') === sp; });
      var cols = tb.dims[sp].map(function (d, i) { return i; }), yrs = {}, cell = {};
      tb.rows.forEach(function (r) {
        for (var k in K) if (k !== sp && tb.dims[k].length > 1 && r[K[k]] !== st.fix[k]) return;
        yrs[r[4]] = 1; cell[r[4] + '|' + r[K[sp]]] = r[5];
      });
      var years = Object.keys(yrs).map(Number).sort(function (a, b) { return a - b; });
      cols = cols.filter(function (i) { return years.some(function (y) { return cell[y + '|' + i] != null; }); });
      var isTime = tb.id === 'DT_1TS202001', f = isTime ? { unit: 'time' } : { dp: -1 };
      var fmt = function (v) { if (v == null) return '–'; if (isTime) return hm(v); var s = String(v); var dp = s.indexOf('.') >= 0 ? Math.min(s.length - s.indexOf('.') - 1, 3) : 0; return num(v, dp); };
      var unit = sp === 'm' ? '항목별 단위' : (tb.unit[st.fix.m] || '');
      p.querySelector('#x-meta').innerHTML = esc(tb.org) + ' · <a href="' + esc(tb.url) + '" target="_blank" rel="noopener">' + esc(tb.id) + ' ' + esc(tb.title) + '</a>' + (tb.proj ? ' · 공식 추계' : '') + (unit ? ' · 단위: ' + esc(isTime ? '시간:분' : unit) : '') + ' · 연도 ' + (years[0] || '') + '~' + (years[years.length - 1] || '');
      if (!st.on) { st.on = {}; cols.slice(0, Math.min(5, cols.length)).forEach(function (i, k) { st.on[i] = k; }); }
      var series = cols.map(function (i) { return { name: tb.dims[sp][i][1], v: years.map(function (y) { var v = cell[y + '|' + i]; return v == null ? null : v; }), off: !(i in st.on), c: st.on[i], proj: tb.proj, i: i }; });
      var shown = series.filter(function (s) { return !s.off; });
      var chartEl = p.querySelector('#x-chart');
      renderers = renderers.filter(function (r) { return r.el !== chartEl; });
      if (years.length > 1 && shown.length) lineChart(chartEl, years, shown, isTime ? { unit: 'time' } : { dp: 2 }, { title: tb.title, h: 260 });
      else if (years.length === 1) chartEl.innerHTML = '<p class="note">' + years[0] + '년 한 해 값만 있다. 아래 막대는 모든 열의 값이다.</p>' + hbars(series.map(function (s) { return s.name; }), series.map(function (s) { return s.v[0]; }), null, isTime ? { unit: 'time' } : { dp: 1 });
      else chartEl.innerHTML = '';
      var leg = p.querySelector('#x-leg');
      leg.innerHTML = '<p class="note" style="margin:0 0 4px">그래프에 넣을 열 (최대 8개)</p>' + series.map(function (s) {
        return '<label style="--c:' + (s.off ? 'var(--muted)' : col(s.c)) + '"><input type="checkbox" data-c="' + s.i + '"' + (s.off ? '' : ' checked') + '>' + esc(s.name) + '</label>';
      }).join(' ');
      leg.querySelectorAll('input').forEach(function (b) {
        b.addEventListener('change', function () {
          var i = +b.getAttribute('data-c');
          if (b.checked) {
            var used = {}; Object.keys(st.on).forEach(function (k) { used[st.on[k]] = 1; });
            var slot = -1; for (var q = 0; q < 8; q++) if (!used[q]) { slot = q; break; }
            if (slot < 0) { b.checked = false; return; } st.on[i] = slot;
          } else delete st.on[i];
          paint();
        });
      });
      var h = '<div class="dtable" style="max-height:640px"><table><thead><tr><th>연도</th>' + series.map(function (s) { return '<th>' + esc(s.name) + (sp === 'm' && tb.unit[s.i] ? '<br><small>' + esc(isTime ? '시간:분' : tb.unit[s.i]) + '</small>' : '') + '</th>'; }).join('') + '</tr></thead><tbody>';
      for (var y = years.length - 1; y >= 0; y--) h += '<tr><td>' + years[y] + '</td>' + series.map(function (s) { var v = s.v[y]; return '<td' + (v == null ? ' class="na"' : '') + '>' + fmt(v) + '</td>'; }).join('') + '</tr>';
      p.querySelector('#x-table').innerHTML = h + '</tbody></table></div>';
    }
    if (D.tables.DT_1JC1516) ts.value = 'DT_1JC1516';
    ts.addEventListener('change', setup);
    p._init = setup;
    return p;
  }

  // ---------------------------------------------------------------- 요약 타일
  var tiles = document.getElementById('tiles');
  tiles.innerHTML = D.tiles.map(function (t) {
    return '<button type="button" class="tile" data-go="' + t.sec + '"><span class="tl">' + esc(t.label) + '</span><span class="tv">' + fv(t.v, t.fmt, t.fmt.unit !== '%' && t.fmt.unit !== 'time') +
      (t.fmt.unit !== '%' && t.fmt.unit !== 'time' ? '<small>' + esc(t.fmt.unit) + '</small>' : '') + '</span><span class="td">' + t.y + (t.py ? ' · ' + t.py + ' 대비 ' + delta(t.v, t.pv, t.fmt, t.delta) : '') + '</span></button>';
  }).join('');

  // ---------------------------------------------------------------- 탭
  var built = {}, tabs = root.querySelectorAll('.dtabs [role=tab]');
  function show(id, push) {
    if (!built[id]) {
      var sec = D.sections.filter(function (s) { return s.id === id; })[0];
      var el = sec ? section(sec) : explorer();
      panels.appendChild(el); built[id] = el;
      if (el._init) el._init();
    }
    Object.keys(built).forEach(function (k) { built[k].hidden = k !== id; });
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-sec') === id ? 'true' : 'false'); });
    try { localStorage.setItem('dash-tab', id); } catch (e) {}
    if (push) { try { history.replaceState(null, '', '#' + id); } catch (e) {} }
    redraw();
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { show(t.getAttribute('data-sec'), true); }); });
  tiles.addEventListener('click', function (e) { var b = e.target.closest('[data-go]'); if (b) { show(b.getAttribute('data-go'), true); root.querySelector('.dtabs').scrollIntoView({ block: 'start' }); } });
  var start = (location.hash || '').slice(1);
  if (!/^(d|e|t|h|s|x)$/.test(start)) { try { start = localStorage.getItem('dash-tab') || 'd'; } catch (e) { start = 'd'; } }
  if (!/^(d|e|t|h|s|x)$/.test(start)) start = 'd';
  show(start, false);
  window.addEventListener('hashchange', function () { var h = location.hash.slice(1); if (/^(d|e|t|h|s|x)$/.test(h)) show(h, false); });

  // ---------------------------------------------------------------- 다시 그리기·사이트 바 높이·읽기 막대
  function redraw() { renderers.forEach(function (r) { if (r.el.isConnected && r.el.offsetParent !== null) r.draw(); }); }
  var rt = null;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { setBar(); redraw(); }, 120); });
  function setBar() { var b = document.querySelector('.sitebar'); if (b) root.querySelector('.dtabs').style.top = 'calc(env(safe-area-inset-top, 0px) + ' + b.offsetHeight + 'px)'; }
  setBar();
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () { var d = document.documentElement, mx = d.scrollHeight - window.innerHeight; d.style.setProperty('--read', mx > 0 ? Math.min(1, window.scrollY / mx).toFixed(4) : 0); ticking = false; tip.hidden = true; });
  }, { passive: true });
})();
