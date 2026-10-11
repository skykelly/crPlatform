const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const link = (url, label) => `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;

function renderTrend(data) {
  const filters = document.querySelector('#trend-filters');
  const grid = document.querySelector('#trend-grid');
  let selected = '전체';
  const labels = ['전체', ...data.drivers];
  function paint() {
    filters.innerHTML = labels.map(label => `<button type="button" class="filter-chip ${selected === label ? 'selected' : ''}" aria-pressed="${selected === label}" data-driver="${esc(label)}">${esc(label)}</button>`).join('');
    const entries = data.trends.filter(item => selected === '전체' || item.drivers.includes(selected));
    grid.innerHTML = entries.map(item => `<article class="trend-card" id="${esc(item.id)}"><div class="trend-top"><span class="trend-id">${esc(item.id)}</span><span class="source-type">${esc(item.type)}</span><time datetime="${esc(item.date)}">${esc(item.date)}</time></div><div class="driver-tags">${item.drivers.map(d => `<span>${esc(d)}</span>`).join('')}</div><h3>${esc(item.title)}</h3><div class="trend-body"><div><b>관측·보도</b><p>${esc(item.fact)}</p></div><div><b>생활에 미치는 영향 · 해석</b><p>${esc(item.life)}</p></div></div><p class="trend-limit"><b>읽을 때 주의</b> ${esc(item.limit)}</p><div class="trend-source"><span>${esc(item.metric)}<br>${esc(item.source)}</span><span>${link(item.url, '원문')}${item.extra_url ? ` ${link(item.extra_url, '추가 원문')}` : ''}</span></div></article>`).join('');
    filters.querySelectorAll('button').forEach(button => button.addEventListener('click', () => { selected = button.dataset.driver; paint(); }));
  }
  paint();
}

function renderInsights(data) {
  document.querySelector('#insight-list').innerHTML = data.insights.map(item => `<article class="insight-card"><div class="insight-index">${esc(item.number)}</div><div><h3>${esc(item.title)}</h3><div class="insight-columns"><div><span class="block-label">근거</span><p>${esc(item.evidence)}</p></div><div><span class="block-label">해석</span><p>${esc(item.interpretation)}</p></div></div><div class="insight-test"><b>다음 검증</b> ${esc(item.test)}</div><div class="evidence-links">관련 조사 ${item.trends.map(id => `<a href="trend.html#${esc(id)}">${esc(id)} ↗</a>`).join('')}</div></div></article>`).join('');
}

function renderOutlook(data) {
  document.querySelector('#scenario-list').innerHTML = data.scenarios.map(item => `<article class="scenario-card"><div class="scenario-period">${esc(item.period)}</div><div><h3>${esc(item.title)}</h3><div class="scenario-rows"><p><b>조건</b>${esc(item.condition)}</p><p><b>가능한 변화</b>${esc(item.outcome)}</p><p><b>불확실성</b>${esc(item.uncertainty)}</p></div></div></article>`).join('');
  document.querySelector('#watch-grid').innerHTML = data.watch.map(item => `<article><span>${esc(item.driver)}</span><h3>${esc(item.signal)}</h3><p>${esc(item.why)}</p></article>`).join('');
}

fetch('data/editorial.json').then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); }).then(data => {
  const page = document.body.dataset.page;
  if (page === 'trend') renderTrend(data);
  if (page === 'insights') renderInsights(data);
  if (page === 'outlook') renderOutlook(data);
}).catch(() => {
  const target = document.querySelector('#trend-grid, #insight-list, #scenario-list');
  if (target) target.innerHTML = '<p class="load-error" role="alert">콘텐츠를 불러오지 못했습니다. 잠시 후 새로고침해 주세요.</p>';
});
