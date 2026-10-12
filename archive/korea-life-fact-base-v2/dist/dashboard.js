const $ = (selector) => document.querySelector(selector);
const fmt = (value, digits = 0) => new Intl.NumberFormat('ko-KR', {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(value);
const latest = (series) => series.at(-1);
const colors = ['#EA1917', '#212731', '#A50034', '#0C9AFF', '#88847F'];

function card(label, value, unit, year, meta = '', accent = false) {
  return `<article class="metric-card ${accent ? 'accent' : ''}"><div class="card-label">${label}</div><div class="card-value">${value}<span class="unit">${unit}</span></div><div class="card-meta">${year}년 · ${meta}</div></article>`;
}
function section(id, number, title, description, cards, visuals, note, sources) {
  const links = [...new Set(sources)].map((url, i) => `<a href="${url}" target="_blank" rel="noopener">원자료 ${i + 1} ↗</a>`).join('');
  return `<section class="driver" id="${id}"><div class="section-heading"><div><span class="section-index">${number} / 05 · ACTUAL</span><h2>${title}</h2></div><p>${description}</p></div><div class="card-grid">${cards.join('')}</div><div class="visual-grid">${visuals.join('')}</div><div class="source-line"><span>${note}</span><span class="links">${links}</span></div></section>`;
}
function viz(title, caption, body, legend = '') {
  return `<article class="viz"><h3>${title}</h3><div class="caption">${caption}</div>${body}${legend}</article>`;
}
function lineChart(series, options = {}) {
  const width = 600, height = 210, left = 45, right = 10, top = 18, bottom = 29;
  const all = series.flatMap(s => s.data);
  const years = [...new Set(all.map(p => p.year))].sort((a,b) => a-b);
  const values = all.map(p => p.value);
  let lo = options.zero ? 0 : Math.floor(Math.min(...values) * 0.9);
  let hi = Math.ceil(Math.max(...values) * 1.08);
  if (hi <= lo) hi = lo + 1;
  const x = year => left + (year - years[0]) / Math.max(1, years.at(-1) - years[0]) * (width-left-right);
  const y = value => height-bottom - (value-lo)/(hi-lo)*(height-top-bottom);
  const formatAxis = options.axis || (v => fmt(v));
  const lines = [0, .5, 1].map(f => {
    const yy = height-bottom-f*(height-top-bottom);
    return `<line class="gridline" x1="${left}" x2="${width-right}" y1="${yy}" y2="${yy}"/><text class="axis-label" x="${left-7}" y="${yy+4}" text-anchor="end">${formatAxis(lo+f*(hi-lo))}</text>`;
  }).join('');
  const yearMarks = [...new Set([years[0], years[Math.floor(years.length/2)], years.at(-1)])].map(yr => `<text class="axis-label" x="${x(yr)}" y="${height-4}" text-anchor="middle">${yr}</text>`).join('');
  const paths = series.map((s, i) => {
    const color = s.color || colors[i];
    const path = s.data.map((p, j) => `${j ? 'L' : 'M'}${x(p.year).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ');
    const circles = s.data.length <= 7 ? s.data.map(p => `<circle cx="${x(p.year)}" cy="${y(p.value)}" r="3.8" fill="${color}"/>`).join('') : '';
    return `<path d="${path}" fill="none" stroke="${color}" stroke-width="2.7" stroke-linejoin="round" stroke-linecap="round"/>${circles}`;
  }).join('');
  return `<div class="chart"><svg role="img" aria-label="${series.map(s=>s.name).join(', ')} 추이" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">${lines}${yearMarks}${paths}</svg></div>`;
}
function legend(series) {
  return `<div class="chart-key">${series.map((s,i) => `<span><i style="background:${s.color || colors[i]}"></i>${s.name}</span>`).join('')}</div>`;
}
function bars(rows, suffix = '%') {
  return `<div class="bars">${rows.map(row => `<div class="bar-row"><span>${row.label}</span><span class="bar-track"><span class="bar-fill" style="display:block;width:${Math.min(100,row.value)}%"></span></span><strong>${fmt(row.value, 1)}${suffix}</strong></div>`).join('')}</div>`;
}
function timeLabel(value) { return `${Math.floor(value/60)}시간 ${fmt(value%60)}분`; }

function render(d) {
  const dem = d.demographic, life = d.life_event, ls = d.lifestyle, home = d.home, spend = d.spending;
  const demMix = [{name:'1인가구',data:dem.single_share},{name:'부부만 거주',data:dem.couple_only_share},{name:'가구주 65세 이상',data:dem.senior_head_share}];
  const demDual = [{name:'유배우 가구 중 맞벌이',data:dem.dual_earner_share_of_married}];
  const lifeCounts = [{name:'혼인',data:life.marriages.map(p=>({year:p.year,value:p.value/10000}))},{name:'출생',data:life.births.map(p=>({year:p.year,value:p.value/10000}))}];
  const moveLine = [{name:'이동자',data:life.movers.map(p=>({year:p.year,value:p.value/10000}))}];
  const sleepLine = [{name:'수면',data:ls.sleep_minutes}];
  const homeLine = [{name:'가정관리',data:ls.home_management_minutes}];
  const areaLine = [{name:'가구당 평균 주거면적',data:home.mean_area_m2}];
  const expenditure = spend.monthly_won_per_household;
  const spendingSeries = Object.entries(expenditure).filter(([name])=>name!=='주거·수도·광열').map(([name,data])=>({name,data:data.map(p=>({year:p.year,value:p.value/1000}))}));
  const drivers = [
    section('demographic','01','인구·가구','총가구 규모와 구성의 이동을 함께 봅니다. 맞벌이는 전체 가구가 아닌 유배우 가구에서 계산합니다.',[
      card('일반가구',fmt(latest(dem.total_households).value/10000,1),'만 가구',latest(dem.total_households).year,'전국',true),
      card('1인가구 비중',fmt(latest(dem.single_share).value,1),'%',latest(dem.single_share).year,'전체 일반가구'),
      card('고령 가구주 비중',fmt(latest(dem.senior_head_share).value,1),'%',latest(dem.senior_head_share).year,'가구주 65세 이상'),
      card('맞벌이 비중',fmt(latest(dem.dual_earner_share_of_married).value,1),'%',latest(dem.dual_earner_share_of_married).year,'유배우 가구')
    ],[
      viz('가구 구성 비중','단위 % · 각 항목은 전체 일반가구 대비',lineChart(demMix,{axis:v=>fmt(v,0)+'%'}),legend(demMix)),
      viz('맞벌이 비중','단위 % · 유배우 가구 대비',lineChart(demDual,{axis:v=>fmt(v,0)+'%'}),legend(demDual))
    ],dem.note,dem.source),
    section('life-event','02','생애사건','혼인·출생·주소 이동을 각각 세어 생애 전환의 규모를 봅니다.',[
      card('국내 이동자',fmt(latest(life.movers).value/10000,1),'만 명',latest(life.movers).year,'이사 가구 수 아님',true),
      card('혼인',fmt(latest(life.marriages).value/10000,1),'만 건',latest(life.marriages).year,'인구동향조사'),
      card('출생',fmt(latest(life.births).value/10000,1),'만 명',latest(life.births).year,'인구동향조사'),
      card('이동자 장기 변화',fmt((latest(life.movers).value/life.movers[0].value-1)*100,1),'%',`${life.movers[0].year}→${latest(life.movers).year}`,'신고 인원')
    ],[
      viz('혼인과 출생','단위 만 건·만 명 · 수량 비교',lineChart(lifeCounts,{zero:true,axis:v=>fmt(v,0)}),legend(lifeCounts)),
      viz('국내 이동자','단위 만 명 · 신고 인원',lineChart(moveLine,{axis:v=>fmt(v,0)}),legend(moveLine))
    ],life.note,life.source),
    section('lifestyle','03','생활방식','생활시간조사의 하루 평균시간. 관측 간격이 5년이라 연속적인 연간 변화로 읽지 않습니다.',[
      card('수면',timeLabel(latest(ls.sleep_minutes).value),'',latest(ls.sleep_minutes).year,'10세 이상·요일평균',true),
      card('가정관리',timeLabel(latest(ls.home_management_minutes).value),'',latest(ls.home_management_minutes).year,'10세 이상·요일평균'),
      card('수면 변화',`${fmt(latest(ls.sleep_minutes).value-ls.sleep_minutes[0].value)}`,'분',`${ls.sleep_minutes[0].year}→${latest(ls.sleep_minutes).year}`,'동일 분류'),
      card('가정관리 변화',`${fmt(latest(ls.home_management_minutes).value-ls.home_management_minutes[0].value)}`,'분',`${ls.home_management_minutes[0].year}→${latest(ls.home_management_minutes).year}`,'동일 분류')
    ],[
      viz('하루 수면시간','단위 분/일 · 5년 간격',lineChart(sleepLine,{axis:v=>fmt(v,0)}),legend(sleepLine)),
      viz('하루 가정관리 시간','단위 분/일 · 5년 간격',lineChart(homeLine,{axis:v=>fmt(v,0)}),legend(homeLine))
    ],ls.note,ls.source),
    section('home','04','주거','주택 재고의 유형, 거주면적, 가구의 점유형태를 분모를 구분해 표시합니다.',[
      card('전체 주택 재고',fmt(latest(home.housing_stock_total).value/10000,1),'만 호',latest(home.housing_stock_total).year,'주택 수',true),
      card('아파트 비중',fmt(home.stock_mix.find(p=>p.label==='아파트').value,1),'%',home.stock_year,'전체 주택 재고'),
      card('평균 주거면적',fmt(latest(home.mean_area_m2).value,1),'㎡',latest(home.mean_area_m2).year,'가구 기준'),
      card('자가 거주 비중',fmt(latest(home.tenure.owner_share).value,1),'%',latest(home.tenure.owner_share).year,'거주 가구·표본')
    ],[
      viz('주택 종류별 재고',`${home.stock_year}년 · 전체 주택 대비 %`,bars(home.stock_mix)),
      viz('점유형태','2015·2020년 표본조사 · 거주 가구 대비 %',bars([
        {label:'자가',value:latest(home.tenure.owner_share).value},
        {label:'전세',value:latest(home.tenure.jeonse_share).value},
        {label:'보증부 월세',value:latest(home.tenure.deposit_monthly_share).value}
      ]))
    ],home.note,home.source),
    section('spending','05','Home & Living 지출','가계동향조사의 가구당 월평균 금액입니다. 항목별 지출은 명목 원으로 읽습니다.',[
      ...['가전·가정용 기기','가구·조명','주택 유지·수선','가사서비스'].map((name,i)=>card(name,fmt(latest(expenditure[name]).value/1000,1),'천 원',latest(expenditure[name]).year,'가구당 월평균',i===0))
    ],[
      viz('핵심 네 항목의 지출 추이','단위 천 원/가구/월 · 명목',lineChart(spendingSeries,{zero:true,axis:v=>fmt(v,0)}),legend(spendingSeries)),
      viz('2025년 지출 항목','단위 원/가구/월 · 선택한 5개 항목',`<div class="spend-table" role="table" aria-label="2025년 월평균 지출">${Object.entries(expenditure).map(([name,data])=>`<div role="row" style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee;font-size:13px"><span role="cell">${name}</span><strong role="cell">${fmt(latest(data).value)}원</strong></div>`).join('')}</div>`)
    ],spend.note,spend.source)
  ];
  $('#dashboard').innerHTML = drivers.join('');
  const p = d.official_projection;
  const finalYear = latest(p.total_households).year;
  $('#projection-content').innerHTML = `<p class="proj-note">장래가구추계는 실제 관측과 분리한 별도 시나리오입니다. 최신 실측치와 추계치를 같은 선으로 잇지 않습니다.</p><div class="proj-cards"><div class="proj-card"><span>추계 마지막 연도</span><strong>${finalYear}</strong></div><div class="proj-card"><span>${finalYear}년 전체 가구</span><strong>${fmt(latest(p.total_households).value/10000,1)}만</strong></div><div class="proj-card"><span>${finalYear}년 1인가구</span><strong>${fmt(latest(p.single_person_households).value/10000,1)}만</strong></div></div><p class="proj-note">${p.note} <a href="${p.source}" target="_blank" rel="noopener">원자료 ↗</a></p>`;
  $('#update-label').textContent = `관측자료 반영 ${d.as_of}`;
}

async function load() {
  const local = 'data/dashboard.json';
  const remote = `https://raw.githubusercontent.com/skykelly/crPlatform/main/sites/korea-life-fact-base-v2/dist/data/dashboard.json?t=${Date.now()}`;
  let data;
  try {
    const response = await fetch(remote, {cache:'no-store'});
    if (!response.ok) throw new Error('remote unavailable');
    data = await response.json();
  } catch (_) {
    try {
      const response = await fetch(local, {cache:'no-store'});
      if (!response.ok) throw new Error('local unavailable');
      data = await response.json();
      $('#status').textContent = '최신 GitHub 데이터에 연결하지 못해 마지막 배포본을 표시합니다.';
    } catch (_) {
      $('#status').textContent = '데이터를 불러올 수 없습니다. 잠시 뒤 다시 확인해 주세요.';
      return;
    }
  }
  if (data.schema_version !== 3) {
    $('#status').textContent = '데이터 형식이 일치하지 않습니다.';
    return;
  }
  try { render(data); } catch (error) {
    console.error(error);
    $('#status').textContent = '대시보드 계산을 확인할 수 없습니다.';
  }
}
load();
