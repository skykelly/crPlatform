(function () {
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var canHover = window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches;
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
                set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

  // ---------- 숫자 올라가기
  if (!reduce) {
    document.querySelectorAll('.stats dd[data-count]').forEach(function (el) {
      var to = +el.getAttribute('data-count'), t0 = null, dur = 900;
      if (!(to > 0)) return;
      var step = function (t) {
        if (!t0) t0 = t;
        var p = Math.min(1, (t - t0) / dur), v = Math.round(to * (1 - Math.pow(1 - p, 3)));
        el.textContent = v.toLocaleString('ko-KR');
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }

  // ---------- 탭
  var board = document.getElementById('board');
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var ink = document.querySelector('.tab-ink');
  var cols = Array.prototype.slice.call(board.querySelectorAll('.col'));
  function moveInk(tab) {
    if (!ink || !tab) return;
    ink.style.setProperty('--x', tab.offsetLeft + 'px');
    ink.style.setProperty('--w', tab.offsetWidth + 'px');
  }
  function select(cat, focus, fromUser) {
    var tab = tabs.filter(function (t) { return t.dataset.cat === cat; })[0] || tabs[0];
    tabs.forEach(function (t) { var on = t === tab; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; });
    board.setAttribute('aria-labelledby', tab.id);
    board.dataset.view = tab.dataset.cat === 'all' ? 'all' : 'cat';
    cols.forEach(function (c) { c.classList.toggle('on', c.dataset.cat === tab.dataset.cat); });
    moveInk(tab);
    if (focus) tab.focus();
    if (fromUser) {
      store.set('axs-tab', tab.dataset.cat);
      if (!reduce) { board.classList.remove('swap'); void board.offsetWidth; board.classList.add('swap'); }
      var tabsBar = document.querySelector('.tabs');
      if (tabsBar.getBoundingClientRect().top < 0 || board.getBoundingClientRect().top < 0) {
        window.scrollTo({ top: board.closest('.boardwrap').offsetTop - 8, behavior: reduce ? 'auto' : 'smooth' });
      }
    }
    applySearch();
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { select(t.dataset.cat, false, true); });
    t.addEventListener('keydown', function (e) {
      var j = null;
      if (e.key === 'ArrowRight') j = (i + 1) % tabs.length;
      if (e.key === 'ArrowLeft') j = (i - 1 + tabs.length) % tabs.length;
      if (e.key === 'Home') j = 0;
      if (e.key === 'End') j = tabs.length - 1;
      if (j !== null) { e.preventDefault(); select(tabs[j].dataset.cat, true, true); }
    });
  });
  // 레이더 점·해시 링크로 카테고리 열기
  function fromHash() {
    var h = (location.hash || '').slice(1);
    if (h && tabs.some(function (t) { return t.dataset.cat === h; })) { select(h, false, false); return true; }
    return false;
  }
  document.querySelectorAll('.radar .dot').forEach(function (d) {
    d.addEventListener('click', function (e) {
      e.preventDefault();
      var cat = d.getAttribute('href').slice(1), q = d.getAttribute('data-q');
      select(cat, false, true);
      var tile = board.querySelector('.tile[data-q="' + q + '"] .tlink');
      if (tile) { tile.scrollIntoView({ block: 'center', behavior: reduce ? 'auto' : 'smooth' }); tile.focus({ preventScroll: true }); }
    });
  });
  window.addEventListener('hashchange', fromHash);
  window.addEventListener('resize', function () { moveInk(tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0]); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { moveInk(tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0]); });


  // ---------- 전체 보기에서 카드 높이 맞추기
  function equalize() {
    var all = Array.prototype.slice.call(board.querySelectorAll('.tile'));
    all.forEach(function (t) { t.style.height = ''; });
    if (board.dataset.view !== 'all') return;
    var vis = all.filter(function (t) { return t.offsetParent !== null; });
    var h = vis.reduce(function (m, t) { return Math.max(m, t.offsetHeight); }, 0);
    if (h) vis.forEach(function (t) { t.style.height = h + 'px'; });
  }
  var eqTimer = null;
  function equalizeSoon() { clearTimeout(eqTimer); eqTimer = setTimeout(equalize, 60); }
  window.addEventListener('resize', equalizeSoon);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(equalize);

  // ---------- 검색
  var input = document.getElementById('q-search'), count = document.getElementById('q-count'), none = document.querySelector('.noresult');
  var tiles = Array.prototype.slice.call(board.querySelectorAll('.tile[data-search]'));
  function applySearch() {
    var words = (input.value || '').toLowerCase().trim().split(/\s+/).filter(Boolean), shown = 0;
    var view = board.dataset.view, active = board.querySelector('.col.on');
    tiles.forEach(function (t) {
      var ok = words.every(function (w) { return t.dataset.search.indexOf(w) >= 0; });
      t.hidden = !ok;
      if (ok && (view === 'all' || t.closest('.col') === active)) shown++;
    });
    cols.forEach(function (c) { c.classList.toggle('empty', words.length > 0 && !c.querySelector('.tile[data-search]:not([hidden])')); });
    count.textContent = words.length ? shown + '개' : '';
    none.hidden = !(words.length && shown === 0);
    equalize();
  }
  input.addEventListener('input', applySearch);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { input.value = ''; applySearch(); input.blur(); }
    if (e.key === 'ArrowDown' || e.key === 'Enter') {
      var first = board.querySelector('.col:not(.empty) .tile:not([hidden]) .tlink');
      if (first && (board.dataset.view === 'all' || first.closest('.col.on'))) { e.preventDefault(); first.focus(); }
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); input.focus(); }
  });

  if (!fromHash()) select(store.get('axs-tab') || 'all', false, false);

  // ---------- 보드 안 방향키 이동
  function visibleLinks() {
    return Array.prototype.slice.call(board.querySelectorAll('.tile:not([hidden]) .tlink')).filter(function (a) { return a.offsetParent !== null; });
  }
  board.addEventListener('keydown', function (e) {
    var a = e.target.closest && e.target.closest('.tlink');
    if (!a || ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].indexOf(e.key) < 0) return;
    var links = visibleLinks(), r = a.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, best = null, bd = Infinity;
    links.forEach(function (b) {
      if (b === a) return;
      var s = b.getBoundingClientRect(), x = s.left + s.width / 2, y = s.top + s.height / 2, dx = x - cx, dy = y - cy;
      var ok = (e.key === 'ArrowDown' && dy > 10) || (e.key === 'ArrowUp' && dy < -10) || (e.key === 'ArrowRight' && dx > 10) || (e.key === 'ArrowLeft' && dx < -10);
      if (!ok) return;
      var d = (e.key === 'ArrowDown' || e.key === 'ArrowUp') ? Math.abs(dy) + Math.abs(dx) * 3 : Math.abs(dx) + Math.abs(dy) * 3;
      if (d < bd) { bd = d; best = b; }
    });
    if (best) { e.preventDefault(); best.focus(); best.scrollIntoView({ block: 'nearest' }); }
  });

  // ---------- 미리보기 (가리키면 팝오버, 터치하면 아래 시트)
  var pv = document.getElementById('preview'), scrim = document.querySelector('.scrim'), timer = null, current = null, opener = null;
  function fill(tile) {
    var link = tile.querySelector('.tlink');
    var tno = tile.querySelector('.tno');
    pv.querySelector('.pv-no').textContent = tno.querySelector('b').textContent + ' · ' + tno.querySelector('span').textContent;
    pv.querySelector('#pv-title').textContent = tile.querySelector('.ttl').textContent;
    var chip = tile.querySelector('.chip'), pc = pv.querySelector('.pv-chip');
    pc.textContent = chip ? chip.textContent : ''; pc.hidden = !chip;
    pv.querySelector('.pv-q').textContent = tile.querySelector('.tq').textContent;
    pv.querySelector('.pv-a').textContent = tile.querySelector('.ta').textContent;
    pv.querySelector('.pv-meta').innerHTML = tile.querySelector('.tmeta').innerHTML;
    var ti = tile.querySelector('.titems'); pv.querySelector('.pv-items').innerHTML = ti ? ti.outerHTML : '';
    pv.querySelector('.pv-go').href = link.getAttribute('href');
  }
  function place(tile) {
    if (window.innerWidth <= 760) { pv.style.left = ''; pv.style.top = ''; return; }
    var r = tile.getBoundingClientRect(), w = pv.offsetWidth, h = pv.offsetHeight, gap = 12;
    var left = r.right + gap + w <= window.innerWidth - 16 ? r.right + gap : r.left - gap - w;
    if (left < 16) left = Math.max(16, Math.min(r.left, window.innerWidth - w - 16));
    var top = Math.max(16, Math.min(r.top, window.innerHeight - h - 16));
    pv.style.left = left + 'px'; pv.style.top = top + 'px';
  }
  function open(tile, mode) {
    if (board.dataset.view === 'cat' && mode === 'hover') return; // 펼친 보기에서는 이미 한 줄 답이 보인다
    current = tile; fill(tile);
    pv.classList.toggle('hover', mode === 'hover');
    pv.hidden = false; place(tile);
    if (mode === 'sheet') {
      scrim.hidden = window.innerWidth > 760;
      opener = tile.querySelector('.tlink');
      pv.querySelector('.pv-go').focus({ preventScroll: true });
    }
  }
  function close() {
    clearTimeout(timer); pv.hidden = true; scrim.hidden = true; current = null;
    if (opener) { opener.focus({ preventScroll: true }); opener = null; }
  }
  if (canHover) {
    board.addEventListener('mouseover', function (e) {
      var tile = e.target.closest && e.target.closest('.tile[data-search]');
      if (!tile || tile === current) return;
      clearTimeout(timer);
      timer = setTimeout(function () { open(tile, 'hover'); }, 320);
    });
    board.addEventListener('mouseleave', function () { if (pv.classList.contains('hover')) close(); else clearTimeout(timer); });
    board.addEventListener('mouseout', function (e) {
      var tile = e.target.closest && e.target.closest('.tile[data-search]');
      if (tile && !tile.contains(e.relatedTarget)) { clearTimeout(timer); if (pv.classList.contains('hover') && current === tile) close(); }
    });
  } else {
    board.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('.tlink');
      if (!a || board.dataset.view === 'cat') return;
      e.preventDefault();
      open(a.closest('.tile'), 'sheet');
    });
  }
  // 키보드: 카드에서 스페이스로 미리보기
  board.addEventListener('keydown', function (e) {
    var a = e.target.closest && e.target.closest('.tlink');
    if (a && e.key === ' ') { e.preventDefault(); open(a.closest('.tile'), 'sheet'); }
  });
  pv.querySelector('.pv-x').addEventListener('click', close);
  scrim.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !pv.hidden) close(); });
  window.addEventListener('scroll', function () { if (!pv.hidden && pv.classList.contains('hover')) close(); }, { passive: true });
  // 시트를 아래로 끌어 닫기
  var y0 = null;
  pv.addEventListener('touchstart', function (e) { y0 = e.touches[0].clientY; }, { passive: true });
  pv.addEventListener('touchmove', function (e) {
    if (y0 === null || pv.scrollTop > 0) return;
    var dy = e.touches[0].clientY - y0;
    if (dy > 0) pv.style.transform = 'translateY(' + dy + 'px)';
  }, { passive: true });
  pv.addEventListener('touchend', function (e) {
    var dy = y0 === null ? 0 : e.changedTouches[0].clientY - y0;
    pv.style.transform = ''; y0 = null;
    if (dy > 80) close();
  });

  // ---------- 판정 임박 전망 더 보기
  document.querySelectorAll('.month .more').forEach(function (b) {
    b.addEventListener('click', function () {
      var m = b.closest('.month'), on = m.classList.toggle('open');
      b.setAttribute('aria-expanded', on);
      b.textContent = on ? '접기' : b.dataset.label || b.textContent;
      if (!b.dataset.label && on) b.dataset.label = b.textContent;
    });
    b.dataset.label = b.textContent;
  });
})();
