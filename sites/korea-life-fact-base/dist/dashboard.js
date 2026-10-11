(async () => {
  const status = document.createElement('p');
  status.id = 'data-status';
  status.style.cssText = 'font-size:12px;color:#666;margin:0 0 18px';
  document.querySelector('#dashboard .intro').after(status);
  status.textContent = '공식 통계 데이터 확인 중…';
  const local = './data/dashboard.json';
  const remote = 'https://raw.githubusercontent.com/skykelly/crPlatform/main/sites/korea-life-fact-base/dist/data/dashboard.json';
  let data, origin;
  for (const [url, label] of [[remote, 'GitHub 최신본'], [local, '사이트 저장본']]) {
    try {
      const response = await fetch(url + '?t=' + Date.now(), {cache: 'no-store'});
      if (!response.ok) throw new Error(String(response.status));
      const candidate = await response.json();
      if (candidate.schema_version !== 1 || !candidate.actual?.single_person_households?.length) throw new Error('schema');
      data = candidate;
      origin = label;
      break;
    } catch (_) { /* fall through to the published snapshot */ }
  }
  if (!data) {
    status.textContent = '데이터 연결 실패. 화면의 고정값은 2026.10.10 기준이며 최신 값이 아닐 수 있습니다.';
    return;
  }
  const actual = data.actual.single_person_households;
  const projected = data.official_projection.single_person_households;
  const births = data.actual.births;
  const marriages = data.actual.marriages;
  const last = values => values[values.length - 1];
  const number = (n, digits = 1) => (n / 10000).toFixed(digits);
  const growth = ((last(actual).value / actual[0].value - 1) * 100).toFixed(1);
  const cards = document.querySelectorAll('#dashboard .kpi');
  const card = (i, mode, point, value, unit, description) => {
    cards[i].className = 'kpi ' + mode;
    cards[i].querySelector('.label').textContent = `${mode === 'actual' ? 'ACTUAL' : 'OFFICIAL PROJECTION'} · ${point.year}`;
    cards[i].querySelector('.val').innerHTML = `${value}<small>${unit}</small>`;
    cards[i].querySelector('p').textContent = description;
  };
  card(0, 'actual', last(actual), number(last(actual).value), '만 가구', `1인 가구. ${actual[0].year}년 대비 ${growth}% 증가.`);
  card(1, 'actual', last(births), number(last(births).value), '만 명', '출생아 수. 인구동향 연간 관측치.');
  card(2, 'actual', last(marriages), number(last(marriages).value), '만 건', '혼인 건수. 인구동향 연간 관측치.');
  card(3, 'forecast', last(projected), number(last(projected).value, 0), '만 가구', '2022년 기준 장래가구추계의 공식 전망치.');
  const chart = document.querySelector('#dashboard .plot svg');
  const combined = [...actual, ...projected];
  const ymin = Math.floor(Math.min(...combined.map(d => d.value)) / 1000000) * 1000000 - 300000;
  const ymax = Math.ceil(Math.max(...combined.map(d => d.value)) / 1000000) * 1000000 + 300000;
  const xmin = actual[0].year, xmax = last(projected).year;
  const coords = item => `${((item.year - xmin) / (xmax - xmin) * 600).toFixed(1)},${(218 - (item.value - ymin) / (ymax - ymin) * 205).toFixed(1)}`;
  chart.setAttribute('aria-label', `${xmin}–${last(actual).year}년 1인 가구 실제치와 ${projected[0].year}–${xmax}년 공식 전망치`);
  chart.innerHTML = `<polyline points="${actual.map(coords).join(' ')}" fill="none" stroke="#111" stroke-width="5"/><polyline points="${projected.map(coords).join(' ')}" fill="none" stroke="#EA1917" stroke-width="5" stroke-dasharray="9 7"/><circle cx="${coords(last(actual)).split(',')[0]}" cy="${coords(last(actual)).split(',')[1]}" r="6"/><circle cx="${coords(last(projected)).split(',')[0]}" cy="${coords(last(projected)).split(',')[1]}" r="6" fill="#EA1917"/>`;
  const axis = document.querySelector('#dashboard .chart + .legend');
  axis.innerHTML = `<span>${xmin}</span><span>${last(actual).year}</span><span>2040</span><span>${xmax}</span>`;
  const minis = document.querySelectorAll('#dashboard .mini');
  [[`${growth}%`, `${actual[0].year}–${last(actual).year}년 1인 가구 증가율`],
   [`${number(last(births).value)}만 명`, `${last(births).year}년 출생아`],
   [`${data.quality.observations.toLocaleString('ko-KR')}건`, `검증된 관측치 · 공식 표 ${data.coverage.length}개`]]
    .forEach(([value, caption], i) => {minis[i].querySelector('strong').textContent = value; minis[i].querySelector('span').textContent = caption;});
  const observed = [last(actual), last(births), last(marriages)];
  const latestRetrieval = observed.map(d => d.retrieved_at).sort().at(-1);
  status.textContent = `${origin} · 실제치 ${last(actual).year}년 · 수집 ${latestRetrieval} · Actual과 Official Projection 분리`;
  document.querySelector('.hero .meta span:first-child').textContent = `Core Fact ${data.catalog_count}개`;
  document.querySelector('.hero .meta span:last-child').textContent = `${latestRetrieval} 데이터 기준`;
  const sourceLine = document.querySelector('#dashboard .sources');
  sourceLine.innerHTML = `출처: <a href="${last(actual).source_url}" target="_blank" rel="noreferrer">KOSIS 1인 가구</a> · <a href="${last(projected).source_url}" target="_blank" rel="noreferrer">KOSIS 장래가구추계</a> · <a href="${last(births).source_url}" target="_blank" rel="noreferrer">KOSIS 인구동향</a>. 전망은 2022년 기준 추계이며 실제치와 직접 연결하지 않았다.`;
})();
