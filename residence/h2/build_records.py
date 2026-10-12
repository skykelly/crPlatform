"""H2 R1 4유형 기록 생성 + 규칙 검증. 출력: 같은 폴더 records.jsonl
실행: python3 build_records.py  (검증 오류가 있으면 exit 1)
"""
import sys
from pathlib import Path

Q, R = "H2", "R1"
FB = "팩트베이스(KOSIS API) 값"
# 출처 사전: key → url·publisher·date·grade (A 공식 1차 / B 언론·연구기관 / C 출처 불명)
SRC = {
    # 팩트베이스 (KOSIS 공식 API)
    "fb_hh": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1L9U101&conn_path=I2",
              "publisher": "국가데이터처 KOSIS (DT_1L9U101 가구당 월평균 가계수지, 전국 1인 이상)", "date": "2026-10-11", "grade": "A"},
    "fb_age": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1JC1517&conn_path=I2",
               "publisher": "국가데이터처 KOSIS (DT_1JC1517 가구주 연령·성·점유형태별 일반가구)", "date": "2026-10-10", "grade": "A"},
    "fb_one": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1PL1502&conn_path=I2",
               "publisher": "국가데이터처 KOSIS (DT_1PL1502 성 및 연령별 1인가구)", "date": "2026-10-10", "grade": "A"},
    # 공식 발표 원문(게재처)
    "census25": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=284799",
                 "publisher": "국가데이터처 2025 인구주택총조사 결과 보도자료 (KDI 경제정보센터 게재)", "date": "2026-07-28", "grade": "A"},
    "heat_jeju": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=284982",
                  "publisher": "기후에너지환경부 보도자료 (KDI 경제정보센터 게재)", "date": "2026-07-31", "grade": "A"},
    # 언론·연구기관
    "news1_census": {"url": "https://www.news1.kr/amp/economy/trend/6241227",
                     "publisher": "뉴스1 (국가데이터처 2025 인구주택총조사 주택 부문 인용)", "date": "2026-07-28", "grade": "B"},
    "newsis_census": {"url": "https://www.newsis.com/view/NISX20260728_0003726109",
                      "publisher": "뉴시스 (국가데이터처 2025 인구주택총조사 인용)", "date": "2026-07-28", "grade": "B"},
    "herald_census": {"url": "https://www.heraldk.com/article/2026072722090410402",
                      "publisher": "헤럴드경제 (국가데이터처 2025 인구주택총조사 가구 부문 인용)", "date": "2026-07-27", "grade": "B"},
    "cerik": {"url": "https://cerik.re.kr/board/press/589",
              "publisher": "한국건설산업연구원 보도자료 (건축물 리모델링 시장의 전망과 정책 과제)", "date": "2020-09-17", "grade": "B"},
    "gr_public26": {"url": "https://www.fnnews.com/news/202606021507382282",
                    "publisher": "파이낸셜뉴스 (국토교통부 2026 공공건축물 그린리모델링 선정 인용)", "date": "2026-06-03", "grade": "B"},
    "gr_public26b": {"url": "https://www.heraldk.com/article/2026060218000070240",
                     "publisher": "헤럴드경제 (국토교통부 2026 공공건축물 그린리모델링 선정 인용)", "date": "2026-06-02", "grade": "B"},
    "gr_public25": {"url": "https://newsseoul.co.kr/news/view/1065568824606918?dt=m",
                    "publisher": "뉴스서울 (국토교통부 2025 공공건축물 그린리모델링 선정 인용)", "date": "2025-06-04", "grade": "B"},
    "gr_private": {"url": "https://www.kairnews.com/news/474800",
                   "publisher": "한국AI부동산신문 (국토교통부 그린리모델링 이자지원 재개 인용)", "date": "2026-03-20", "grade": "B"},
    "gr_private_b": {"url": "https://v.daum.net/v/20260326043356184",
                     "publisher": "다음뉴스 게재 기사 (국토교통부 그린리모델링 이자지원 재개 인용)", "date": "2026-03-26", "grade": "B"},
    "energy_survey": {"url": "https://www.kukinews.com/article/view/kuk202503120201",
                      "publisher": "쿠키뉴스 (산업통상자원부 2023 에너지총조사 결과 인용)", "date": "2025-03-12", "grade": "B"},
    "energy_survey_b": {"url": "https://newsseoul.co.kr/news/view/1065583214519538",
                        "publisher": "뉴스서울 (산업통상자원부 2023 에너지총조사 결과 인용)", "date": "2025-03-12", "grade": "B"},
    "bldg_energy": {"url": "https://www.hankyung.com/article/2025073019141",
                    "publisher": "한국경제 (국토교통부 2024년 건물 용도별·지역별 에너지 지표 인용)", "date": "2025-07-30", "grade": "B"},
    "tariff": {"url": "https://www.kukinews.com/article/view/kuk202606220018",
               "publisher": "쿠키뉴스 (한국전력 2026년 3분기 전기요금 결정 인용)", "date": "2026-06-22", "grade": "B"},
    "heat_guide": {"url": "https://www.kharn.kr/mobile/article.html?no=31533",
                   "publisher": "칸(KHARN) (기후에너지환경부 난방 전기화 보조금 지침 개정 인용)", "date": "2026-08-08", "grade": "B"},
    "elder_survey": {"url": "https://www.etoday.co.kr/news/view/2434002",
                     "publisher": "이투데이 (보건복지부 2023 노인실태조사 인용)", "date": "2025-01-02", "grade": "B"},
    "housing_survey": {"url": "https://biz.newdaily.co.kr/site/data/html/2025/11/15/2025111500090.html",
                       "publisher": "뉴데일리 (국토교통부 2024년도 주거실태조사 결과 인용)", "date": "2025-11-16", "grade": "B"},
    "pet_survey": {"url": "https://www.newsseoul.co.kr/news/view/1065584423215514",
                   "publisher": "뉴스서울 (농림축산식품부 2025 반려동물 양육현황 조사 인용)", "date": "2026-02-12", "grade": "B"},
    "pet_survey_b": {"url": "https://www.khan.co.kr/article/202602121457001/",
                     "publisher": "경향신문 (농림축산식품부 2025 반려동물 양육현황 조사 인용)", "date": "2026-02-12", "grade": "B"},
    "flexwork": {"url": "https://bizhankook.com/articles/30184.html",
                 "publisher": "비즈한국 (통계청 유연근무제 활용 근로자 비율 인용)", "date": "2025-08-22", "grade": "B"},
    "senior_builders": {"url": "https://www.theguru.co.kr/mobile/article.html?no=105839",
                        "publisher": "더구루 (건설사 시니어 주거 서비스 보도)", "date": "2026-08-16", "grade": "B"},
    "furniture_h1": {"url": "https://news.bizwatch.co.kr/article/consumer/2026/08/11/0025",
                     "publisher": "비즈니스워치 (한샘·현대리바트 2026년 상반기 실적 보도)", "date": "2026-08-12", "grade": "B"},
    "soc_monitor": {"url": "https://biz.newdaily.co.kr/site/data/html/2021/08/05/2021080500024.amp.html",
                    "publisher": "뉴데일리 (국토교통부 2020년도 국토모니터링보고서 인용)", "date": "2021-08-05", "grade": "B"},
}
def src(*keys): return [dict(SRC[k], key=k) for k in keys]

base = dict(question=Q, question_version="v1.0", first_seen=R, last_seen=R, status="유효", replaces=None, check_flags=[])
records = []
def add(**kw):
    r = dict(base); r.update(kw); records.append(r)

# 팩트베이스 계산값 (일반가구 분모: DT_1JC1517 합계)
GEN = {2020: 20926710, 2021: 21448463, 2022: 21773507, 2023: 22073158, 2024: 22294419, 2025: 22495096}
OLD = {2020: 4732364, 2021: 5015574, 2022: 5331539, 2023: 5655260, 2024: 5993409, 2025: 6371694}   # 가구주 65세 이상 5개 연령구간 합
ONE = {2020: 6643354, 2021: 7165788, 2022: 7502350, 2023: 7829035, 2024: 8044948, 2025: 8244308}   # 1인가구 합계
old_s = {str(y): round(OLD[y] / GEN[y] * 100, 1) for y in GEN}
one_s = {str(y): round(ONE[y] / GEN[y] * 100, 1) for y in GEN}

# ---------- 지표 (M) ----------
# H2-K1 인테리어·리모델링 시장
add(id=f"{Q}-M-001", type="지표", indicator=f"{Q}-K1", importance=3, representative=True,
    statement="한국건설산업연구원은 2020년 건축물 리모델링 시장(개수와 유지·보수 포함)을 30조원으로 추정했다. 2025년 37조원, 2030년 44조원으로 전망했다.",
    value=30, unit="조원", as_of="2020", region="KR",
    definition="건축물 리모델링(개수)과 유지·보수 시장 합계 추정. 주거·비주거 구분 없음. 2025·2030년 값은 전망치",
    prev_value=None, extra={"series": {"2020": 30}, "projection": {"2025": 37, "2030": 44}},
    sources=src("cerik"), verified=True,
    check_flags=["확인 필요: 주거용만의 시장 규모가 아니고 2020년 추정 이후 실적 갱신값을 찾지 못함. 2025년 37조원은 전망치"])
add(id=f"{Q}-M-002", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="가구당 월평균 주택유지·수선 지출은 2025년 26,866원으로 2024년(30,363원)보다 줄었다. 2021년 37,115원이 최근 7년 중 가장 높았다.",
    value=26866, unit="원/월", as_of="2025", region="KR",
    definition=f"{FB}. 가계동향조사 전국 1인 이상 가구, 소비지출 중 주택유지및수선 항목. 명목 금액",
    prev_value=30363, extra={"series": {"2019": 26670, "2020": 30968, "2021": 37115, "2022": 25823, "2023": 26174, "2024": 30363, "2025": 26866}},
    sources=src("fb_hh"), verified=True,
    check_flags=["확인 필요: 명목 금액이며 소비자물가 실질화 전 값"])
add(id=f"{Q}-M-003", type="지표", indicator=f"{Q}-K1", importance=1, representative=False,
    statement="가구당 월평균 가구·조명 지출은 2025년 18,210원으로 2021년(22,440원) 정점 이후 줄어든 수준에 머물렀다.",
    value=18210, unit="원/월", as_of="2025", region="KR",
    definition=f"{FB}. 가계동향조사 전국 1인 이상 가구, 가구및조명 항목. 명목 금액",
    prev_value=18472, extra={"series": {"2019": 17549, "2020": 19740, "2021": 22440, "2022": 18084, "2023": 18835, "2024": 18472, "2025": 18210}},
    sources=src("fb_hh"), verified=True,
    check_flags=["확인 필요: 명목 금액이며 소비자물가 실질화 전 값"])
add(id=f"{Q}-M-004", type="지표", indicator=f"{Q}-K1", importance=1, representative=False,
    statement="유연근무제(재택·원격근무 포함)를 활용한 임금근로자 비율은 2021년 16.8%에서 2024년 15.0%로 낮아졌다.",
    value=15.0, unit="%", as_of="2024", region="KR",
    definition="통계청 근로형태별 부가조사 기준 유연근무제 활용 근로자 비율(언론 인용). 재택 공간 수요의 노출 규모를 보는 참고값",
    prev_value=15.6, extra={"series": {"2020": 14.2, "2021": 16.8, "2022": 16.0, "2023": 15.6, "2024": 15.0}},
    sources=src("flexwork"), verified=True,
    check_flags=["확인 필요: 재택·원격근무만의 비율이 아니라 유연근무제 전체 활용률. KOSIS 원표와 2025년 값 미확인"])

# H2-K2 주택 개조·그린리모델링
add(id=f"{Q}-M-005", type="지표", indicator=f"{Q}-K2", importance=3, representative=True,
    statement="국토교통부는 2026년 공공건축물 그린리모델링 대상으로 318동을 선정했다. 2025년 261동보다 57동 많다.",
    value=318, unit="동", as_of="2026", region="KR",
    definition="공공건축물 그린리모델링 지원 대상 선정 동수(신청 535동 중). 2020~2024년 누적 지원 3,470동",
    prev_value=261, extra={"series": {"2025": 261, "2026": 318}, "cumulative_2020_2024": 3470,
                           "type_2025": {"경로당": 187, "보건소": 37, "도서관": 12}, "type_2026": {"경로당": 217, "사회복지시설": 31, "노인복지시설": 18, "도서관": 13}},
    sources=src("gr_public26", "gr_public26b", "gr_public25"), verified=True,
    check_flags=["확인 필요: 단위가 '건'이 아니라 '동'(선정 기준). 준공 실적과 다를 수 있음. 2026년 유형별 수는 헤럴드경제 보도 기준"])
add(id=f"{Q}-M-006", type="지표", indicator=f"{Q}-K2", importance=2, representative=False,
    statement="민간 건축물 그린리모델링 이자지원은 2014~2023년 약 8만 건을 지원했다. 2024년 신규 지원이 멈췄다가 2026년 재개됐다.",
    value=80000, unit="건", as_of="2014~2023 누적", region="KR",
    definition="민간 그린리모델링 공사비 대출 이자지원 누적 건수(약). 연도별 건수 미공개",
    prev_value=None, sources=src("gr_private", "gr_private_b"), verified=True,
    check_flags=["확인 필요: '약 8만 건'은 언론 인용 누적값. 연도별·주거용 실적은 국토안전관리원 원자료 미확인"])
add(id=f"{Q}-M-007", type="지표", indicator=f"{Q}-K2", importance=3, representative=False,
    statement="2025년 준공 30년 이상 주택은 618만 1천 호로 전체 주택의 30.6%다. 1년 전보다 2.6%p, 5년 전보다 11.2%p 높다. 20년 이상 주택은 56.0%다.",
    value=30.6, unit="%", as_of="2025", region="KR",
    definition="인구주택총조사(2025-11-01 기준) 주택 부문, 사용승인 후 30년 이상 주택 비중. 개조 수요의 노출 규모",
    prev_value=28.0, extra={"series": {"2020": 19.4, "2024": 28.0, "2025": 30.6}, "over20y_2025": 56.0, "units_2025": 6181000},
    sources=src("census25", "news1_census", "newsis_census"), verified=True,
    check_flags=["확인 필요: 2020·2024년 값은 보도의 증감폭(5년 +11.2%p, 1년 +2.6%p)으로 역산한 값"])

# H2-K3 가구 에너지 소비
add(id=f"{Q}-M-008", type="지표", indicator=f"{Q}-K3", importance=3, representative=True,
    statement="2023년 에너지총조사(2022년 실적)에서 가구당 에너지 소비는 2.7% 줄었다. 가정 부문 소비는 2019~2022년 연평균 0.4% 감소했다.",
    value=-2.7, unit="%", as_of="2022", region="KR",
    definition="산업통상자원부 에너지총조사 가구부문, 가구당 에너지 소비 변화율(직전 조사 대비로 보도). TOE/가구 수준값은 미확보",
    prev_value=None, extra={"household_sector_share_2022": 8.8, "household_sector_share_change_pp": -0.3, "household_sector_cagr_2019_2022": -0.4},
    sources=src("energy_survey", "energy_survey_b"), verified=True,
    check_flags=["확인 필요: 가구당 TOE 수준값과 에너지원별 비중은 보고서 원문 미확인. 2.7%의 비교 기간이 보도에 명확하지 않음"])
add(id=f"{Q}-M-009", type="지표", indicator=f"{Q}-K3", importance=2, representative=False,
    statement="가구당 월평균 주거·수도·광열 지출은 2025년 360,650원으로 2019년(276,589원)보다 30.4% 많다. 2025년 증가율은 2.6%로 직전 5년 연평균(4.9%)보다 낮다.",
    value=360650, unit="원/월", as_of="2025", region="KR",
    definition=f"{FB}. 가계동향조사 전국 1인 이상 가구, 주거·수도·광열 대분류. 명목 금액. 연평균 증가율은 2019→2024 기하평균",
    prev_value=351613, extra={"series": {"2019": 276589, "2020": 285822, "2021": 298238, "2022": 302333, "2023": 330189, "2024": 351613, "2025": 360650}},
    sources=src("fb_hh"), verified=True,
    check_flags=["확인 필요: 월세 등 실제주거비가 포함된 대분류로 연료비만의 값이 아님. 명목 금액"])
add(id=f"{Q}-M-010", type="지표", indicator=f"{Q}-K3", importance=1, representative=False,
    statement="2024년 중부지역 아파트의 단위면적당 에너지 사용량은 136kWh/㎡로 단독주택(178kWh/㎡)보다 약 24% 적다.",
    value=136, unit="kWh/㎡", as_of="2024", region="KR 중부",
    definition="국토교통부 건물 용도별·지역별 에너지 지표(국가승인통계), 주택 유형별 단위면적당 사용량",
    prev_value=None, extra={"by_type_2024": {"아파트": 136, "연립": 150, "단독": 178, "다가구": 178, "다세대": 179}},
    sources=src("bldg_energy"), verified=True,
    check_flags=["확인 필요: 가구당이 아니라 면적당 값. 2025년 기준 발표값 미확인"])
add(id=f"{Q}-M-011", type="지표", indicator=f"{Q}-K3", importance=2, representative=False,
    statement=f"1인가구는 2025년 일반가구의 {one_s['2025']}%다. 2020~2024년에는 해마다 평균 1.1%p 늘었으나 2025년에는 0.5%p 늘었다.",
    value=one_s["2025"], unit="%", as_of="2025", region="KR",
    definition=f"{FB}. 1인가구 수(DT_1PL1502 합계) ÷ 일반가구 수(DT_1JC1517 합계) × 100. 가구 에너지 소비 감소 요인으로 지목된 가구 소형화의 규모",
    prev_value=one_s["2024"], extra={"series": one_s},
    sources=src("fb_one", "fb_age"), verified=True)

# H2-K5 고령자 주택 개조
add(id=f"{Q}-M-012", type="지표", indicator=f"{Q}-K5", importance=3, representative=True,
    statement="2023년 노인실태조사에서 노인 배려 설비가 있는 집에 사는 노인은 28.5%다. 욕실 안전손잡이 설치는 18.2%, 단차 제거는 22.6%, 낙상 방지 바닥재는 24.7%다.",
    value=28.5, unit="%", as_of="2023", region="KR",
    definition="보건복지부 노인실태조사, 노인 배려 설비가 있는 주거에 사는 65세 이상 노인 비율(언론 인용). 개조 지원 가구 수가 아니라 설비 보유율",
    prev_value=None, extra={"bath_grab_bar": 18.2, "threshold_removed": 22.6, "anti_slip_floor": 24.7, "bath_door_handle": 29.7, "no_facility": 62.1},
    sources=src("elder_survey"), verified=True,
    check_flags=["확인 필요: 지표 정의(지원 가구 수)와 다른 설비 보유율. 한국보건사회연구원 보고서 원문 미확인. 전국 주택 개조 지원 가구 집계는 찾지 못함"])
add(id=f"{Q}-M-013", type="지표", indicator=f"{Q}-K5", importance=2, representative=False,
    statement=f"가구주가 65세 이상인 가구는 2025년 637만 2천 가구로 일반가구의 {old_s['2025']}%다. 2025년 증가폭은 1.4%p로 2020~2024년 연평균(1.1%p)보다 크다.",
    value=old_s["2025"], unit="%", as_of="2025", region="KR",
    definition=f"{FB}. 가구주 65~69세부터 85세 이상까지 5개 구간 합 ÷ 일반가구 합계 × 100 (DT_1JC1517)",
    prev_value=old_s["2024"], extra={"series": old_s, "count_2025": OLD[2025]},
    sources=src("fb_age"), verified=True)
add(id=f"{Q}-M-014", type="지표", indicator=f"{Q}-K5", importance=2, representative=False,
    statement="65세 이상 1인가구는 2025년 245만 6천 가구로 일반가구의 10.9%다. 1년 새 7.3% 늘었다. 고령자가 있는 가구는 33.3%다.",
    value=10.9, unit="%", as_of="2025", region="KR",
    definition="2025 인구주택총조사 가구 부문, 65세 이상 1인가구 비중(일반가구 대비)",
    prev_value=10.2, extra={"count_2025": 2456000, "with_elderly_share_2025": 33.3},
    sources=src("herald_census", "census25"), verified=True,
    check_flags=["확인 필요: 2024년 값 10.2%는 보도의 증감폭(+0.7%p)으로 역산"])

# H2-K7 생활 인프라 접근성
add(id=f"{Q}-M-015", type="지표", indicator=f"{Q}-K7", importance=1, representative=True,
    statement="2020년도 국토모니터링보고서에서 응급의료시설까지 전국 평균 접근거리는 11.9km로 2019년(12.1km)보다 짧아졌다.",
    value=11.9, unit="km", as_of="2020", region="KR",
    definition="국토교통부 국토모니터링보고서, 시군구 평균 응급의료시설 접근거리. 지표 단위(분)와 다름",
    prev_value=12.1, extra={"library_km": {"2019": 4.9, "2020": 4.6}, "park_km": {"2019": 5.71, "2020": 5.4}},
    sources=src("soc_monitor"), verified=True,
    check_flags=["확인 필요: 기준연도가 2020년으로 오래됨. 의원·약국·돌봄시설 값과 시간(분) 단위 값 미확보. 이후 발간본 미확인"])

# ---------- 사건 (E) ----------
add(id=f"{Q}-E-001", type="사건", importance=2, date="2025-11-16", actor="국토교통부",
    statement="국토교통부가 2024년도 주거실태조사 결과를 발표했다. 1인당 주거면적은 36.0㎡로 전년과 같았다. 청년가구 31.1㎡, 신혼부부 27.4㎡, 고령가구 46.6㎡였다. 자발적 이사 이유 1위는 시설·설비 향상(47.2%)이었다.",
    sources=src("housing_survey"), verified=True)
add(id=f"{Q}-E-002", type="사건", importance=2, date="2026-02-12", actor="농림축산식품부",
    statement="농림축산식품부가 2025년 반려동물 양육현황 조사 결과를 냈다. 반려동물을 기르는 가구는 29.2%였다. 개가 80.5%, 고양이가 14.4%였다. 국가승인통계로 처음 작성돼 이전 조사와 직접 비교하기 어렵다.",
    sources=src("pet_survey", "pet_survey_b"), verified=True)
add(id=f"{Q}-E-003", type="사건", importance=2, date="2026-03-17", actor="국토교통부",
    statement="국토교통부가 2024년 멈췄던 민간 그린리모델링 이자지원을 재개했다. 지원율은 기본 4.5%, 에너지 성능 30% 이상 개선이나 고령·신혼·다자녀 가구는 5.5%다. 에너지 진단 컨설팅을 새로 넣었다.",
    sources=src("gr_private", "gr_private_b"), verified=True)
add(id=f"{Q}-E-004", type="사건", importance=2, date="2026-06-03", actor="국토교통부",
    statement="국토교통부가 2026년 공공건축물 그린리모델링 2.0 대상 318동을 선정했다. 신청은 535동이었다. 경로당이 217동으로 가장 많았다.",
    sources=src("gr_public26", "gr_public26b"), verified=True)
add(id=f"{Q}-E-005", type="사건", importance=1, date="2026-06-22", actor="한국전력공사",
    statement="한국전력이 2026년 3분기 전기요금을 동결했다. 주택용은 13분기 연속 동결이다. 연료비조정단가는 kWh당 +5원을 유지했다.",
    sources=src("tariff"), verified=True)
add(id=f"{Q}-E-006", type="사건", importance=3, date="2026-07-28", actor="국가데이터처",
    statement="국가데이터처가 2025 인구주택총조사 결과를 발표했다. 총주택은 2,018만 1천 호로 처음 2천만 호를 넘었다. 30년 이상 주택은 30.6%, 1인가구는 36.6%, 65세 이상 1인가구는 10.9%였다.",
    sources=src("census25", "news1_census", "herald_census"), verified=True)
add(id=f"{Q}-E-007", type="사건", importance=2, date="2026-07-31", actor="기후에너지환경부",
    statement="기후에너지환경부가 제주에서 난방 전기화 지원사업 첫 공기열 히트펌프 설치를 알렸다. 2026년 국비 약 145억 원으로 온난지역 단독주택의 화석연료 보일러를 바꾼다.",
    sources=src("heat_jeju"), verified=True)
add(id=f"{Q}-E-008", type="사건", importance=1, date="2026-08-08", actor="기후에너지환경부",
    statement="기후에너지환경부가 2026년 난방 전기화 보조금 지침을 고쳤다. 공공이 관리하는 공동주택도 사전승인을 받으면 지원할 수 있게 했다. 올해 총사업비는 361억 2,500만 원이다.",
    sources=src("heat_guide"), verified=True,
    check_flags=["확인 필요: 개정일은 보도 게재일 기준. 기후에너지환경부 원문 미확인"])
add(id=f"{Q}-E-009", type="사건", importance=1, date="2026-08-12", actor="한샘·현대리바트",
    statement="한샘의 2026년 상반기 매출은 9.6% 줄었으나 리모델링 부문(리하우스) 공헌이익은 113억 원 늘었다. 현대리바트 매출은 14% 줄었고 신축 현장용 빌트인 등 B2B(기업 간 거래) 물량 감소가 컸다.",
    sources=src("furniture_h1"), verified=True)
add(id=f"{Q}-E-010", type="사건", importance=1, date="2026-08-16", actor="삼성물산·현대건설·대우건설",
    statement="대형 건설사들이 시니어 주거 서비스를 내놓았다. 삼성물산은 건강·안전 관리 솔루션 '에버링'을 운영 현장에 적용했다. 현대건설은 5월, 대우건설은 6월에 시니어 주거 관련 업무협약을 맺었다.",
    sources=src("senior_builders"), verified=True,
    check_flags=["확인 필요: 날짜는 보도일 기준. 일반 분양 단지 적용 여부와 이용 가구 수 미확인"])

# ---------- 해석 (I) ----------
add(id=f"{Q}-I-001", type="해석", importance=3, target="노후화 → 욕실·주방·설비 교체", direction="강화",
    statement="30년 이상 주택이 30%를 넘었고 1년에 2.6%p씩 늘고 있다. 집의 기능 변화는 새 공간 추가보다 낡은 욕실·주방·설비를 바꾸는 개조가 중심이다. 자발적 이사 이유 1위가 시설·설비 향상이고, 매매가 늘자 리모델링 부문 실적이 먼저 좋아졌다.",
    basis=[f"{Q}-M-007", f"{Q}-E-006", f"{Q}-E-001", f"{Q}-E-009"])
add(id=f"{Q}-I-002", type="해석", importance=3, target="고령화 → 욕실·바닥·문턱 안전 개조", direction="강화",
    statement="65세 이상 가구주 가구 비중의 증가 속도가 빨라졌다. 반면 욕실 안전손잡이, 단차 제거, 낙상 방지 바닥재를 갖춘 비율은 18~25%에 그친다. 고령 가구가 살던 집에 머물수록 안전 개조 수요와 실제 설치 사이의 차이가 커진다.",
    basis=[f"{Q}-M-013", f"{Q}-M-014", f"{Q}-M-012"])
add(id=f"{Q}-I-003", type="해석", importance=2, target="공공 개조 → 동네 고령자 공간", direction="강화",
    statement="공공 그린리모델링은 집 밖의 고령자 생활 공간을 먼저 고친다. 선정 동수가 261동에서 318동으로 늘었고 두 해 모두 경로당이 가장 많다. 민간 주택 이자지원도 고령·신혼 가구를 우대하며 재개됐다.",
    basis=[f"{Q}-M-005", f"{Q}-E-004", f"{Q}-E-003"])
add(id=f"{Q}-I-004", type="해석", importance=2, target="에너지비 → 단열·난방설비", direction="중립",
    statement="가구당 에너지 소비는 줄었지만 주거·수도·광열 지출(명목)은 2019년보다 30% 많다. 주택용 전기요금은 13분기 동결됐다. 보일러를 히트펌프로 바꾸는 난방 전기화는 단독주택 시범 단계라 공간 변화 규모는 아직 작다.",
    basis=[f"{Q}-M-008", f"{Q}-M-009", f"{Q}-E-005", f"{Q}-E-007", f"{Q}-E-008"])
add(id=f"{Q}-I-005", type="해석", importance=2, target="1인화 → 작은 집·적은 에너지", direction="중립",
    statement="1인가구는 가장 큰 집단(36.6%)이지만 증가 속도는 2020~2024년의 절반 수준으로 느려졌다. 가구당 에너지 소비 감소의 원인으로 1인가구 증가가 지목된다. 청년 가구의 1인당 면적은 31.1㎡로 평균보다 좁다.",
    basis=[f"{Q}-M-011", f"{Q}-M-008", f"{Q}-E-001"])
add(id=f"{Q}-I-006", type="해석", importance=1, target="재택 → 홈오피스", direction="약화",
    statement="유연근무제 활용률은 2021년 16.8%에서 2024년 15.0%로 내려왔다. 재택을 위한 별도 업무 공간 수요는 커지는 쪽이 아니다.",
    basis=[f"{Q}-M-004"])
add(id=f"{Q}-I-007", type="해석", importance=1, target="단지 생활서비스·반려동물", direction="중립",
    statement="건설사들이 시니어 건강·안전 서비스를 내놓고 있으나 적용 단지와 이용 가구 수 집계는 없다. 반려동물을 기르는 가구는 29.2%로 규모가 크지만 집 안 공간 변화를 잰 통계는 없다.",
    basis=[f"{Q}-E-010", f"{Q}-E-002"])

# ---------- 세부 전망 (F) ----------
add(id=f"{Q}-F-001", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2026년 기준 인구주택총조사에서 30년 이상 주택 비중은 32.5% 이상일 것이다.",
    due="2027-08-31", condition="없음",
    method="국가데이터처 2026 인구주택총조사 주택 부문 발표(2027년 7월 예상)의 30년 이상 주택 비중 확인",
    basis=[f"{Q}-M-007"])
add(id=f"{Q}-F-002", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 가구주 65세 이상 가구 비중은 29.5% 이상일 것이다.",
    due="2027-08-31", condition="없음",
    method="KOSIS DT_1JC1517 2026년 값으로 가구주 65세 이상 5개 구간 합 ÷ 일반가구 합계 계산",
    basis=[f"{Q}-M-013"])
add(id=f"{Q}-F-003", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 1인가구 비중 증가폭은 0.8%p 미만에 머물 것이다.",
    due="2027-08-31", condition="없음",
    method="KOSIS DT_1PL1502·DT_1JC1517 2026년 값으로 1인가구 비중을 계산해 2025년(36.6%)과 비교",
    basis=[f"{Q}-M-011"])
add(id=f"{Q}-F-004", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2027년 공공건축물 그린리모델링 선정 동수는 2026년(318동) 이상일 것이다.",
    due="2027-07-31", condition="없음",
    method="국토교통부 2027년 공공건축물 그린리모델링 대상 선정 발표의 선정 동수 확인",
    basis=[f"{Q}-M-005"])
add(id=f"{Q}-F-005", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 가구당 월평균 주택유지·수선 지출은 2025년(26,866원)보다 많을 것이다.",
    due="2027-05-31", condition="2026년 주택 매매거래 증가가 하반기에도 이어짐",
    method="KOSIS DT_1L9U101 2026년 연간 주택유지및수선 지출(전국 1인 이상) 확인",
    basis=[f"{Q}-M-002", f"{Q}-E-009"])
add(id=f"{Q}-F-006", type="전망", importance=1, forecast_status="진행 중", result=None,
    statement="2026년 반려동물 양육현황 조사의 양육 가구 비율은 28~31% 범위일 것이다.",
    due="2027-03-31", condition="조사 방법이 2025년과 같음",
    method="농림축산식품부 2026년 반려동물 양육현황 조사 발표값 확인",
    basis=[f"{Q}-E-002"])

# ---------- 메인 질문 시나리오 ----------
add(id=f"{Q}-F-101", type="전망", importance=3, forecast_status="진행 중", scenario="낙관", result=None,
    statement="2027년 말까지 노후화·고령화 속도에 맞춰 집 개조가 늘어난다. 공공 그린리모델링은 규모를 키우고, 가구의 수선 지출이 다시 늘며, 욕실·바닥 안전 개조와 난방 설비 교체가 시범을 넘어 확대된다.",
    milestones=[{"by": "2027-05", "text": "2026년 가구 주택유지·수선 지출이 2025년보다 많음"},
                {"by": "2027-07", "text": "2027년 공공 그린리모델링 선정 318동 이상"},
                {"by": "2027-08", "text": "30년 이상 주택 32.5% 이상, 65세 이상 가구주 가구 29.5% 이상으로 개조 수요 기반 확대 확인"}],
    due="2027-12-31", condition="노후주택·고령가구 증가가 이어지고 개조 지원 예산이 줄지 않음",
    method="세 가지 중 두 가지 이상 충족 시 적중: (1) H2-F-005 적중 (2) H2-F-004 적중 (3) H2-F-001과 H2-F-002 모두 적중",
    basis=[f"{Q}-M-002", f"{Q}-M-005", f"{Q}-M-007", f"{Q}-M-013"],
    signposts=[{"id": f"{Q}-F-005", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-004", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-001", "on_hit": "낙관"},
               {"id": f"{Q}-F-002", "on_hit": "낙관"}])
add(id=f"{Q}-F-102", type="전망", importance=3, forecast_status="진행 중", scenario="비관", result=None,
    statement="2027년 말까지 낡은 집과 고령 가구는 늘지만 개조는 따라가지 못한다. 가구 수선 지출이 정체하고 공공 개조 선정이 줄어 욕실·바닥 안전 설비 부족이 이어진다.",
    milestones=[{"by": "2027-05", "text": "2026년 가구 주택유지·수선 지출이 2025년 이하"},
                {"by": "2027-07", "text": "2027년 공공 그린리모델링 선정 318동 미만"},
                {"by": "2027-08", "text": "30년 이상 주택·고령 가구주 가구 비중은 계속 상승"}],
    due="2027-12-31", condition="없음",
    method="낙관 조건 중 하나 이하 충족 시 적중",
    basis=[f"{Q}-M-002", f"{Q}-M-005", f"{Q}-M-012"],
    signposts=[{"id": f"{Q}-F-005", "on_miss": "비관"}, {"id": f"{Q}-F-004", "on_miss": "비관"},
               {"id": f"{Q}-F-003", "on_hit": "비관"}])

# ---------- 공통 마무리: patches.jsonl 적용 → 검증 → records.jsonl ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from validate import finish
finish(records, Path(__file__).parent)
