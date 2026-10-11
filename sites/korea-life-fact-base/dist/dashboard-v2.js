(async () => {
  const root = document.getElementById('dashboard');
  const local = './data/dashboard.json';
  const remote = 'https://raw.githubusercontent.com/skykelly/crPlatform/main/sites/korea-life-fact-base/dist/data/dashboard.json';
  const sources = await Promise.all([[local, '사이트 저장본'], [remote, 'GitHub 최신본']].map(async ([url, label]) => {
    try {
      const response = await fetch(`${url}?t=${Date.now()}`, {cache: 'no-store'});
      if (!response.ok) throw new Error('network');
      const data = await response.json();
      if (data.schema_version !== 1 || !data.dashboard?.age_bands?.length) throw new Error('schema');
      return {data, label};
    } catch (_) { return null; }
  }));
  const selected = sources.filter(Boolean).sort((a, b) =>
    (a.data.last_changed_at || '').localeCompare(b.data.last_changed_at || '') ||
    a.data.quality.observations - b.data.quality.observations).at(-1);
  if (!selected) {
    root.innerHTML = '<div class="db-wrap"><div class="db-empty"><h2>데이터를 불러오지 못했습니다.</h2><p>잠시 후 다시 시도해 주세요. 저장된 통계는 GitHub 저장소에서 확인할 수 있습니다.</p><a href="https://github.com/skykelly/crPlatform/tree/main/data">원자료 보기</a></div></div>';
    return;
  }
  const {data, label: feedLabel} = selected;
  const db = data.dashboard;
  const actual = data.actual.single_person_households;
  const projected = data.official_projection.single_person_households;
  const births = data.actual.births;
  const marriages = data.actual.marriages;
  const last = values => values.at(-1);
  const byYear = values => new Map(values.map(item => [item.year, item.value]));
  const actualYears = byYear(actual), projectionYears = byYear(projected);
  const birthYears = byYear(births), marriageYears = byYear(marriages);
  const totalYears = byYear(db.total_households), projectedTotalYears = byYear(db.projection_total);
  const esc = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const integer = value => Math.round(value).toLocaleString('ko-KR');
  const wan = (value, decimals = 1) => (value / 10000).toFixed(decimals);
  const percent = (value, total) => `${(value / total * 100).toFixed(1)}%`;
  const change = (start, end) => `${end >= start ? '+' : ''}${((end / start - 1) * 100).toFixed(1)}%`;
  const latest = last(actual), latestTotal = totalYears.get(latest.year);
  const regionalNational = actualYears.get(db.regional_year);
  const latestSize = last(db.household_size);
  const forecast = last(projected), forecastTotal = projectedTotalYears.get(forecast.year);
  const kpi = (ey, value, unit, note, forecastCard = false) => `<article class="db-kpi${forecastCard ? ' forecast' : ''}"><div class="ey">${esc(ey)}</div><div class="num">${esc(value)}<small>${esc(unit)}</small></div><p>${esc(note)}</p></article>`;
  const lineSvg = (title, lines, xMin, xMax, yMax, yUnit, ticks) => {
    const width = 760, height = 300, left = 57, right = 20, top = 16, bottom = 37;
    const px = year => left + (year - xMin) / (xMax - xMin) * (width - left - right);
    const py = value => height - bottom - value / yMax * (height - top - bottom);
    const grid = Array.from({length: 6}, (_, i) => {
      const value = yMax * i / 5, y = py(value);
      return `<line x1="${left}" y1="${y}" x2="${width-right}" y2="${y}" stroke="#e5e7eb"/><text x="${left-8}" y="${y+4}" text-anchor="end" fill="#767980" font-size="11">${esc(yUnit(value))}</text>`;
    }).join('');
    const years = ticks.map(year => `<text x="${px(year)}" y="${height-8}" text-anchor="middle" fill="#767980" font-size="11">${year}</text>`).join('');
    const paths = lines.map(line => {
      const points = line.values.map(item => `${px(item.year).toFixed(1)},${py(item.value).toFixed(1)}`);
      const dots = line.values.filter((item, index) => !line.dashed || index === 0 || index === line.values.length - 1 || item.year % 5 === 0).map(item => `<circle cx="${px(item.year).toFixed(1)}" cy="${py(item.value).toFixed(1)}" r="4" fill="${line.color}"><title>${esc(line.label)} ${item.year}: ${integer(item.value)}${esc(line.unit)}</title></circle>`).join('');
      return `<polyline points="${points.join(' ')}" fill="none" stroke="${line.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" ${line.dashed ? 'stroke-dasharray="8 6"' : ''}/>${dots}`;
    }).join('');
    return `<svg class="db-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>${grid}${years}${paths}</svg>`;
  };
  const ageBars = `<div class="db-bars">${db.age_bands.map((row, i) => `<div class="db-bar-row"><span class="db-bar-label">${esc(row.label)}</span><div class="db-bar-track" aria-hidden="true"><div class="db-bar-fill${i === 3 ? ' red' : ''}" style="width:${(row.value/latest.value*100).toFixed(2)}%"></div></div><span class="db-bar-value">${percent(row.value,latest.value)}</span></div>`).join('')}</div>`;
  const housingBars = `<div class="db-bars">${db.housing_stock.map((row, i) => `<div class="db-bar-row"><span class="db-bar-label">${esc(row.label)}</span><div class="db-bar-track" aria-hidden="true"><div class="db-bar-fill${i === 0 ? ' red' : ''}" style="width:${(row.value/db.housing_total*100).toFixed(2)}%"></div></div><span class="db-bar-value">${percent(row.value,db.housing_total)}</span></div>`).join('')}</div>`;
  const areaRows = db.housing_area.filter(row => row.label !== '계').sort((a,b) => b.value-a.value);
  const areaBars = `<div class="db-bars db-area">${areaRows.map(row => `<div class="db-bar-row"><span class="db-bar-label">${esc(row.label)}</span><div class="db-bar-track" aria-hidden="true"><div class="db-bar-fill" style="width:${(row.value/80*100).toFixed(2)}%"></div></div><span class="db-bar-value">${row.value.toFixed(1)}㎡</span></div>`).join('')}</div>`;
  const projectionRows = [2015, 2020, 2025, 2030, 2040, 2052].map(year => `<tr><td>${year}</td><td class="num">${actualYears.has(year) ? `${wan(actualYears.get(year))}만` : '—'}</td><td class="num">${projectionYears.has(year) ? `${wan(projectionYears.get(year))}만` : '—'}</td><td class="num">${projectionYears.has(year) ? percent(projectionYears.get(year), projectedTotalYears.get(year)) : '—'}</td></tr>`).join('');
  const eventRows = [2010, 2015, 2020, 2025].map(year => `<tr><td>${year}</td><td class="num">${integer(birthYears.get(year))}</td><td class="num">${integer(marriageYears.get(year))}</td></tr>`).join('');
  const allHouseholdRows = actual.map(row => `<tr><td>${row.year}</td><td class="num">${integer(row.value)}</td><td class="num">${totalYears.has(row.year) ? percent(row.value,totalYears.get(row.year)) : '—'}</td></tr>`).join('');
  const allEventRows = births.map(row => `<tr><td>${row.year}</td><td class="num">${integer(row.value)}</td><td class="num">${integer(marriageYears.get(row.year))}</td></tr>`).join('');
  const driverCounts = ['Demographic','Life Event','Lifestyle','Home','Spending'].map(driver => ({driver, count:data.coverage.filter(row => row.driver === driver).length}));
  root.innerHTML = `<div class="db-wrap">
    <div class="db-top"><div><div class="eyebrow">KOREA · FACT DASHBOARD</div><h2>지표 대시보드</h2><p>공식 통계표 ${data.coverage.length}개에서 확보한 장기계열과 최신 단면. 실제치와 공식 전망을 구분했다.</p></div><div class="db-stamp"><strong>원자료 갱신 ${esc(data.last_changed_at)}</strong>${esc(feedLabel)} · 관측치 ${integer(data.quality.observations)}건<br>Catalog ${integer(data.catalog_count)}개 중 ${data.coverage.length}개 표 수집</div></div>
    <div class="db-kpis">
      ${kpi(`ACTUAL · ${latest.year} · 1인 가구`,wan(latest.value),'만 가구',`${actual[0].year}년 대비 ${change(actual[0].value,latest.value)}`)}
      ${kpi(`ACTUAL · ${latest.year} · 일반가구 중 1인`,percent(latest.value,latestTotal),'',`분모: 일반가구 ${wan(latestTotal)}만 가구`)}
      ${kpi(`ACTUAL · ${latestSize.year} · 평균 가구원`,latestSize.value.toFixed(1),'명',`2015년 ${db.household_size[0].value.toFixed(1)}명`)}
      ${kpi(`ACTUAL · ${last(births).year} · 출생아`,wan(last(births).value),'만 명',`2010년 대비 ${change(births[0].value,last(births).value)}`)}
      ${kpi(`ACTUAL · ${last(marriages).year} · 혼인`,wan(last(marriages).value),'만 건',`2010년 대비 ${change(marriages[0].value,last(marriages).value)}`)}
      ${kpi(`OFFICIAL PROJECTION · ${forecast.year}`,wan(forecast.value,0),'만 가구',`1인 가구 · 전체 추계가구의 ${percent(forecast.value,forecastTotal)}`,true)}
    </div>
    <div class="db-grid">
      <article class="db-card span-8"><div class="db-heading"><div><h3>1인 가구 수</h3><p>${actual[0].year}–${latest.year} 실제치 · 2022년 기준 2022–${forecast.year} 장래가구추계</p></div><span class="db-caption">단위: 만 가구</span></div><div class="db-legend"><span><i></i>Actual</span><span><i class="dash"></i>Official Projection</span></div>${lineSvg('1인 가구 수 실제치와 공식 전망치', [{label:'Actual',values:actual,color:'#111',unit:'가구'},{label:'Official Projection',values:projected,color:'#ea1917',unit:'가구',dashed:true}],2015,2052,11000000,n => `${Math.round(n/10000)}만`,[2015,2025,2035,2045,2052])}<p class="db-chart-note">전망선은 2022년 기준 추계다. 겹치는 연도의 두 값도 별개 계열로 표시한다.</p><details class="db-details"><summary>실제치 전체 연도 표</summary><div class="db-table-wrap"><table><caption>연도별 전국 1인 가구 실제치</caption><thead><tr><th>연도</th><th class="num">1인 가구(가구)</th><th class="num">일반가구 중 비중</th></tr></thead><tbody>${allHouseholdRows}</tbody></table></div></details></article>
      <article class="db-card span-4"><div class="db-heading"><div><h3>실제치와 전망치</h3><p>전국 1인 가구, 대표 연도</p></div></div><div class="db-table-wrap"><table><caption>연도별 1인 가구 실제치와 전망치</caption><thead><tr><th>연도</th><th class="num">Actual</th><th class="num">Projection</th><th class="num">전망 비중</th></tr></thead><tbody>${projectionRows}</tbody></table></div><p class="db-micro">전망 비중의 분모는 같은 추계의 전체 가구다. 실제치의 비중과 혼용하지 않는다.</p></article>
      <article class="db-card span-7"><div class="db-heading"><div><h3>출생과 혼인</h3><p>${births[0].year}–${last(births).year} 연간 인구동향</p></div><span class="db-caption">단위: 만 명 / 만 건</span></div><div class="db-legend"><span><i></i>출생아</span><span><i class="red"></i>혼인</span></div>${lineSvg('출생아 수와 혼인 건수의 연간 추이', [{label:'출생아',values:births,color:'#111',unit:'명'},{label:'혼인',values:marriages,color:'#ea1917',unit:'건'}],2010,2025,500000,n => `${Math.round(n/10000)}만`,[2010,2015,2020,2025])}<p class="db-chart-note">서로 다른 사건의 발생 건수를 같은 축에 표시했다. 두 계열의 동행은 인과관계를 뜻하지 않는다.</p><details class="db-details"><summary>출생·혼인 전체 연도 표</summary><div class="db-table-wrap"><table><caption>연도별 출생아와 혼인 실제치</caption><thead><tr><th>연도</th><th class="num">출생아(명)</th><th class="num">혼인(건)</th></tr></thead><tbody>${allEventRows}</tbody></table></div></details></article>
      <article class="db-card span-5"><div class="db-heading"><div><h3>주요 연도 비교</h3><p>전국 연간 건수</p></div></div><div class="db-table-wrap"><table><caption>출생아와 혼인 연도별 건수</caption><thead><tr><th>연도</th><th class="num">출생아(명)</th><th class="num">혼인(건)</th></tr></thead><tbody>${eventRows}</tbody></table></div><div class="db-stat-pair"><div><strong>${change(births[0].value,last(births).value)}</strong><span>출생아 · 2010→2025</span></div><div><strong>${change(marriages[0].value,last(marriages).value)}</strong><span>혼인 · 2010→2025</span></div></div></article>
    </div>
    <h3 class="db-section-title">가구·주택 단면</h3><p class="db-section-desc">연령 ${db.age_year}년 · 주택 재고 ${db.housing_year}년 · 주거면적 ${db.area_year}년. 주택 재고와 거주 가구는 서로 다른 모집단이다.</p>
    <div class="db-grid">
      <article class="db-card span-4"><div class="db-heading"><div><h3>1인 가구의 연령 구성</h3><p>${db.age_year}년 가구주 연령 · 전체 ${wan(latest.value)}만 가구</p></div></div>${ageBars}<p class="db-micro">65세 이상 ${wan(db.age_bands[3].value)}만 가구. 연령 4개 구간을 합하면 전국 1인 가구 총계와 일치한다.</p></article>
      <article class="db-card span-4"><div class="db-heading"><div><h3>주택 재고 구성</h3><p>${db.housing_year}년 주택 종류별 재고 · 전체 ${wan(db.housing_total)}만 호</p></div></div>${housingBars}<p class="db-micro">아파트 ${wan(db.housing_stock[0].value)}만 호. 가구가 거주하는 주택 유형 비중으로 해석하지 않는다.</p></article>
      <article class="db-card span-4"><div class="db-heading"><div><h3>가구당 주거면적</h3><p>${db.area_year}년 주택 종류별 평균 · 전체 ${db.housing_area.find(row => row.label === '계').value.toFixed(1)}㎡</p></div><span class="db-caption">단위: ㎡</span></div>${areaBars}<p class="db-micro">오피스텔 포함 가구 기준. 면적 구간별 가구 수는 이 표에 없다.</p></article>
    </div>
    <h3 class="db-section-title">지역별 1인 가구</h3><p class="db-section-desc">17개 시도, ${db.regional_year}년. 2015년과 동일 지역코드의 증가율을 계산했다.</p>
    <div class="db-card"><div class="db-tools"><input id="db-region-search" type="search" placeholder="시도 검색" aria-label="시도 검색"><select id="db-region-sort" aria-label="지역 정렬"><option value="count">${db.regional_year}년 가구 수 순</option><option value="growth">2015년 대비 증가율 순</option><option value="name">지역명 순</option></select></div><div class="db-table-wrap"><table><caption>17개 시도별 1인 가구</caption><thead><tr><th>시도</th><th class="num">2015</th><th class="num">${db.regional_year}</th><th class="num">전국 비중</th><th class="num">증가율</th></tr></thead><tbody id="db-region-body"></tbody></table></div><p class="db-micro">전국 비중의 분모는 같은 연도의 1인 가구 ${wan(regionalNational)}만 가구다. 읍·면·동 중복 집계는 제외했다.</p></div>
    <h3 class="db-section-title">수집 범위</h3><p class="db-section-desc">Core Fact Catalog는 ${data.catalog_count}개 지표다. 아래 ${data.coverage.length}개 공식 통계표가 현재 DB에 적재되어 있다.</p>
    <div class="db-card"><div class="db-coverage">${driverCounts.map(row => `<div class="${row.count ? 'has' : ''}"><strong>${esc(row.driver)}</strong><span>${row.count ? `${row.count}개 표 수집` : '아직 데이터 미수집'}</span></div>`).join('')}</div><div class="db-table-wrap"><table><caption>수집된 공식 통계표와 기간</caption><thead><tr><th>Driver</th><th>통계표</th><th>Table ID</th><th>기간</th><th class="num">관측치</th><th>구분</th></tr></thead><tbody>${data.coverage.map(row => `<tr><td>${esc(row.driver)}</td><td><a href="${esc(row.source_url)}" target="_blank" rel="noreferrer">${esc(row.title)}</a></td><td>${esc(row.table_id)}</td><td>${row.first_year}–${row.latest_year}</td><td class="num">${integer(row.records)}</td><td><span class="db-pill${row.status === 'Official Projection' ? ' red' : ''}">${esc(row.status)}</span></td></tr>`).join('')}</tbody></table></div><div class="db-notes">집계 원칙: Actual과 Official Projection은 분리 저장한다. 1인 가구 연령·시도, 주택 종류의 구성 합계는 원표의 전국 총계와 대조했다. 결측·비밀보호 표기는 0으로 치환하지 않았다. Lifestyle·Spending 지표는 Catalog에는 있으나 이 대시보드의 실제 수집 범위에는 아직 없다.</div></div>
  </div>`;
  const regionBody = root.querySelector('#db-region-body');
  const regionSearch = root.querySelector('#db-region-search');
  const regionSort = root.querySelector('#db-region-sort');
  const renderRegions = () => {
    const query = regionSearch.value.trim();
    const rows = db.regions.filter(row => row.name.includes(query)).slice();
    if (regionSort.value === 'growth') rows.sort((a,b) => (b[String(db.regional_year)]/b['2015'])-(a[String(db.regional_year)]/a['2015']));
    else if (regionSort.value === 'name') rows.sort((a,b) => a.name.localeCompare(b.name,'ko'));
    else rows.sort((a,b) => b[String(db.regional_year)]-a[String(db.regional_year)]);
    regionBody.innerHTML = rows.map(row => `<tr><td>${esc(row.name)}</td><td class="num">${integer(row['2015'])}</td><td class="num">${integer(row[String(db.regional_year)])}</td><td class="num">${percent(row[String(db.regional_year)],regionalNational)}</td><td class="num">${change(row['2015'],row[String(db.regional_year)])}</td></tr>`).join('') || '<tr><td colspan="5">일치하는 시도가 없습니다.</td></tr>';
  };
  regionSearch.addEventListener('input', renderRegions);
  regionSort.addEventListener('change', renderRegions);
  renderRegions();
  document.querySelector('.hero .meta span:first-child').textContent = `Core Fact ${data.catalog_count}개`;
  document.querySelector('.hero .meta span:last-child').textContent = `${data.last_changed_at} 원자료 갱신`;
})();
