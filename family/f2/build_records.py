"""F2 R1 4유형 기록 생성 + 규칙 검증. 출력: 같은 폴더 records.jsonl
실행: python3 build_records.py  (검증 오류가 있으면 exit 1)

고정 질문: 독립·결혼·출산·이사·은퇴는 언제, 얼마나 자주 일어나는가?
판정 척도: 방향×속도. 방향은 최근 5년(비중 지표는 4년) 연평균 변화, 속도는 최근 1년 변화와 직전 추세의 비교.
"""
import sys
from pathlib import Path

Q, R = "F2", "R1"
KOSIS = "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId={}&conn_path=I2"
# 출처 사전: key → url·publisher·date·grade (A 공식 1차 / B 언론·연구기관 / C 출처 불명)
SRC = {
    # 팩트베이스 (KOSIS 공식 API 수집, 등급 A)
    "kosis_1b8000g": {"url": KOSIS.format("DT_1B8000G"), "publisher": "국가데이터처 KOSIS (DT_1B8000G 인구동향: 출생·혼인·이혼)", "date": "2026-10-11", "grade": "A"},
    "kosis_1pl1502": {"url": KOSIS.format("DT_1PL1502"), "publisher": "국가데이터처 KOSIS (DT_1PL1502 성·연령별 1인가구)", "date": "2026-10-11", "grade": "A"},
    "kosis_1b26001": {"url": KOSIS.format("DT_1B26001_A01"), "publisher": "국가데이터처 KOSIS (DT_1B26001_A01 시군구별 이동자수)", "date": "2026-10-11", "grade": "A"},
    # 국가데이터처 보도자료 원문 (KDI 경제교육·정보센터 게재)
    "kdi_move202605": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=283181", "publisher": "국가데이터처 2026년 5월 국내인구이동통계 (KDI 경제교육·정보센터 게재)", "date": "2026-06-24", "grade": "A"},
    "kdi_move202607": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=285830", "publisher": "국가데이터처 2026년 7월 국내인구이동통계 (KDI 경제교육·정보센터 게재)", "date": "2026-08-26", "grade": "A"},
    "kdi_pop202601": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=278446", "publisher": "국가데이터처 2026년 1월 인구동향 (KDI 경제교육·정보센터 게재)", "date": "2026-03-25", "grade": "A"},
    # 국내인구이동 (언론, 국가데이터처·통계청 발표 인용)
    "herald_move2025": {"url": "https://www.heraldk.com/article/2026012818471712823", "publisher": "헤럴드경제 (국가데이터처 2025년 국내인구이동통계 인용)", "date": "2026-01-28", "grade": "B"},
    "newsis_move2024": {"url": "https://www.newsis.com/view/NISX20250124_0003045133", "publisher": "뉴시스 (통계청 2024년 국내인구이동통계 인용)", "date": "2025-01-24", "grade": "B"},
    "etoday_move2023": {"url": "https://www.etoday.co.kr/news/view/2326289", "publisher": "이투데이 (통계청 2023년 국내인구이동통계 인용)", "date": "2024-01-30", "grade": "B"},
    "tomato_move2022": {"url": "https://newstomato.com/ReadNews.aspx?no=1174250", "publisher": "뉴스토마토 (통계청 2022년 국내인구이동통계 인용)", "date": "2023-01-30", "grade": "B"},
    "newsis_move2021": {"url": "https://www.newsis.com/view/NISX20220125_0001735892", "publisher": "뉴시스 (통계청 2021년 국내인구이동통계 인용)", "date": "2022-01-25", "grade": "B"},
    "newsis_move202606": {"url": "https://www.newsis.com/view/NISX20260729_0003727662", "publisher": "뉴시스 (국가데이터처 2026년 6월 국내인구이동통계 인용)", "date": "2026-07-29", "grade": "B"},
    "sbs_move202608": {"url": "https://biz.sbs.co.kr/amp/article/20000336454", "publisher": "SBS Biz (국가데이터처 2026년 8월 국내인구이동통계 인용)", "date": "2026-09-23", "grade": "B"},
    # 혼인
    "mt_marr2025": {"url": "https://www.mt.co.kr/economy/2026/03/20/2026031915130297984", "publisher": "머니투데이 (국가데이터처 2025년 혼인·이혼 통계 인용)", "date": "2026-03-20", "grade": "B"},
    "etoday_marr2025": {"url": "https://www.etoday.co.kr/news/view/2567119", "publisher": "이투데이 (국가데이터처 2025년 혼인·이혼 통계 인용)", "date": "2026-03-19", "grade": "B"},
    "newsis_marr2024": {"url": "https://www.newsis.com/view/NISX20250320_0003106157", "publisher": "뉴시스 (통계청 2024년 혼인·이혼 통계 인용)", "date": "2025-03-20", "grade": "B"},
    "newsis_newlywed2024": {"url": "https://www.newsis.com/view/NISX20251212_0003438790", "publisher": "뉴시스 (국가데이터처 2024년 신혼부부 통계 인용)", "date": "2025-12-12", "grade": "B"},
    # 월간 인구동향 2026
    "wikitree_pop202607": {"url": "https://www.wikitree.co.kr/articles/1161660", "publisher": "위키트리 (국가데이터처 2026년 7월 인구동향 인용)", "date": "2026-09-23", "grade": "B"},
    "fn_pop202606": {"url": "https://www.fnnews.com/news/202608261203103611", "publisher": "파이낸셜뉴스 (국가데이터처 2026년 6월 인구동향 인용)", "date": "2026-08-26", "grade": "B"},
    "segye_pop202605": {"url": "https://www.segye.com/newsView/20260729516289", "publisher": "세계일보 (국가데이터처 2026년 5월 인구동향 인용)", "date": "2026-07-29", "grade": "B"},
    # 출생
    "fn_birth2025": {"url": "https://www.fnnews.com/news/202608261202208775", "publisher": "파이낸셜뉴스·연합뉴스 (국가데이터처 2025년 출생통계 인용)", "date": "2026-08-26", "grade": "B"},
    "nocut_birth2025": {"url": "https://nocutnews.co.kr/news/6568252", "publisher": "노컷뉴스 (국가데이터처 2025년 출생통계 인용)", "date": "2026-08-26", "grade": "B"},
    "dailian_birth2025": {"url": "https://m.dailian.co.kr/news/view/1682540", "publisher": "데일리안 (국가데이터처 2025년 출생통계 인용)", "date": "2026-08-26", "grade": "B"},
    "newsis_birth2024": {"url": "https://www.newsis.com/view/NISX20250827_0003305090", "publisher": "뉴시스 (통계청 2024년 출생통계 인용)", "date": "2025-08-27", "grade": "B"},
    "newsis_birth2022": {"url": "https://www.newsis.com/view/NISX20230830_0002431412", "publisher": "뉴시스 (통계청 2022년 출생통계 인용)", "date": "2023-08-30", "grade": "B"},
    # 독립·1인가구
    "keis_youth": {"url": "https://www.newsis.com/view/NISX20260806_0003739331", "publisher": "뉴시스 (한국고용정보원 고용동향브리프 2026년 5호, 청년패널조사 인용)", "date": "2026-08-06", "grade": "B"},
    "newsis_1p2025": {"url": "https://www.newsis.com/view/NISX20251209_0003433761", "publisher": "뉴시스 (국가데이터처 2025 통계로 보는 1인 가구 인용)", "date": "2025-12-09", "grade": "B"},
    "news1_census2025": {"url": "https://www.news1.kr/amp/economy/trend/6241212", "publisher": "뉴스1 (국가데이터처 2025 인구주택총조사 등록센서스 인용)", "date": "2026-07-28", "grade": "B"},
    # 주거실태·주거이동
    "newdaily_housing2024": {"url": "https://biz.newdaily.co.kr/site/data/html/2025/11/15/2025111500090.html", "publisher": "뉴데일리 (국토교통부 2024년도 주거실태조사 인용)", "date": "2025-11-15", "grade": "B"},
    "kgnews_housing2024": {"url": "https://www.kgnews.co.kr/mobile/article.html?no=877661", "publisher": "경기신문 (국토교통부 2024년도 주거실태조사 인용)", "date": "2025-12-11", "grade": "B"},
    "tf_krihs": {"url": "https://news.tf.co.kr/read/economy/2289736.htm", "publisher": "더팩트 (국토연구원 '계층별 주거위상 진단과 향후 정책방향' 인용)", "date": "2026-02-12", "grade": "B"},
    # 은퇴
    "newsis_old2026": {"url": "https://www.newsis.com/view/NISX20260805_0003737146", "publisher": "뉴시스 (국가데이터처 2026년 5월 경제활동인구조사 고령층 부가조사 인용)", "date": "2026-08-05", "grade": "B"},
    "newsis_old2025": {"url": "https://www.newsis.com/view/NISX20250806_0003280363", "publisher": "뉴시스 (국가데이터처 2025년 5월 고령층 부가조사 인용)", "date": "2025-08-06", "grade": "B"},
    "newsis_old2024": {"url": "https://www.newsis.com/view/NISX20240730_0002831020", "publisher": "뉴시스 (통계청 2024년 5월 고령층 부가조사 인용)", "date": "2024-07-30", "grade": "B"},
    "dailian_old2024": {"url": "https://www.dailian.co.kr/news/view/1389881/", "publisher": "데일리안 (통계청 2024년 5월 고령층 부가조사 인용)", "date": "2024-07-30", "grade": "B"},
    "segye_old2026": {"url": "https://www.segye.com/newsView/20260906500772", "publisher": "세계일보 (국가데이터처 고령층 부가조사·한국보건사회연구원 분석 인용)", "date": "2026-09-06", "grade": "B"},
    "khanweekly_retire": {"url": "https://weekly.khan.co.kr/article/202608291624001", "publisher": "주간경향 (정년연장 입법 경과 정리)", "date": "2026-08-29", "grade": "B"},
    # 주택 정책
    "herald_1015": {"url": "https://www.heraldk.com/article/2025101417000026673", "publisher": "헤럴드경제 (정부 10·15 주택시장 안정화 대책 보도)", "date": "2025-10-14", "grade": "B"},
}
def src(*keys): return [dict(SRC[k], key=k) for k in keys]

base = dict(question=Q, question_version="v1.0", first_seen=R, last_seen=R, status="유효", replaces=None, check_flags=[])
records = []
def add(**kw):
    r = dict(base); r.update(kw); records.append(r)

FB = "팩트베이스(KOSIS API) 값"

# =====================================================================
# 지표 (M)
# =====================================================================
# --- F2-K1 청년 독립 ---
add(id=f"{Q}-M-001", type="지표", indicator=f"{Q}-K1", importance=3, representative=True,
    statement="2025년 20~34세 1인가구는 222만 5천 가구로 1년 전보다 0.9% 줄었다. 2020년 188만 5천 가구에서 2024년 224만 5천 가구까지 늘다가 처음 꺾였다. 20~24세 1인가구는 2023년 이후 2년 연속 줄었다.",
    value=2225010, unit="가구", as_of="2025", region="KR",
    definition=f"{FB}. 인구총조사 등록센서스 1인가구 중 가구주 20~24세·25~29세·30~34세 합계. 청년 인구 대비 비율이 아닌 가구 수.",
    prev_value=2244848,
    extra={"series": {"2020": 1885312, "2021": 2068435, "2022": 2161262, "2023": 2232104, "2024": 2244848, "2025": 2225010},
           "series_20_24": {"2020": 492331, "2023": 494745, "2024": 480880, "2025": 456531},
           "share_of_all_1p": {"2020": 28.4, "2024": 27.9, "2025": 27.0},
           "calc": "DT_1PL1502 1인가구 연령별 값 합산. 비중 = 20~34세 합 ÷ 1인가구 합계"},
    check_flags=["확인 필요: 지표 정의는 '20~34세 중 부모와 따로 사는 비율'이나 가구 수로 대신 잼. 청년 인구가 줄어 수 감소가 독립률 하락을 뜻하지는 않음"],
    sources=src("kosis_1pl1502"), verified=True)
add(id=f"{Q}-M-002", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="청년패널조사 2021 코호트(2021년 19~28세)의 주거 독립 비율은 2024년 30.4%로 2021년 26.4%보다 4.0%p 올랐다. 부모와 함께 사는 비율은 약 70%다. 남성 32.6%, 여성 28.4%가 주거 독립 상태다.",
    value=30.4, unit="%", as_of="2024", region="KR",
    definition="한국고용정보원 청년패널조사 2021 코호트(표본 약 1만 2천 명) 중 부모와 따로 사는 비율. 같은 사람을 추적하므로 나이가 들며 오르는 효과가 섞여 있다.",
    prev_value=26.4, extra={"series": {"2021": 26.4, "2024": 30.4}, "economic_independence": {"2021": 65.9, "2024": 75.4}},
    check_flags=["확인 필요: 코호트 추적 표본이라 연령 구성이 해마다 바뀜. 국가 통계의 20~34세 부모 비동거율과 정의가 다름. 고용동향브리프 원문 미열람(보도 인용)"],
    sources=src("keis_youth"), verified=True)
add(id=f"{Q}-M-003", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="1인가구의 49.6%는 주거면적 40㎡ 이하에 산다. 60㎡ 이하를 모두 더하면 74.2%이고, 60~85㎡는 18.0%, 85㎡ 초과는 7.6%다. 1인가구 중 29세 이하는 17.8%, 30대는 17.4%다.",
    value=74.2, unit="%", as_of="2024", region="KR",
    definition="국가데이터처 '2025 통계로 보는 1인 가구'의 주거면적 구간별 1인가구 비중. 60㎡ 이하·85㎡ 초과 합계는 구간 값을 더한 계산값. 청년만이 아닌 1인가구 전체 기준.",
    extra={"bands": {"40㎡ 이하": 49.6, "40~50㎡": 13.0, "50~60㎡": 11.6, "60~85㎡": 18.0, "85~102㎡": 3.9, "102~135㎡": 3.2, "135㎡ 초과": 0.5},
           "age_share": {"29세 이하": 17.8, "30대": 17.4, "70세 이상": 19.8}, "home_ownership": 32.0},
    check_flags=["확인 필요: 기준 연도(2024년 인구주택총조사 추정)와 청년 1인가구만의 면적 분포는 보도자료 원문으로 확인 필요"],
    sources=src("newsis_1p2025"), verified=True)

# --- F2-K2 혼인 건수 ---
add(id=f"{Q}-M-004", type="지표", indicator=f"{Q}-K2", importance=3, representative=True,
    statement="2025년 혼인 건수는 24만 326건으로 1년 전보다 8.1% 늘었다. 2018년 이후 가장 많다. 2022년 19만 1,690건으로 바닥을 찍은 뒤 3년 연속 늘었다. 조혼인율(인구 천 명당 혼인 건수)은 4.7건이다.",
    value=240326, unit="건", as_of="2025", region="KR",
    definition=f"{FB}. 혼인 신고 기준 연간 혼인 건수.", prev_value=222412,
    extra={"series": {"2015": 302828, "2020": 213502, "2021": 192507, "2022": 191690, "2023": 193657, "2024": 222412, "2025": 240326},
           "crude_rate": {"2020": 4.2, "2021": 3.8, "2022": 3.7, "2023": 3.8, "2024": 4.4, "2025": 4.7}},
    sources=src("kosis_1b8000g", "etoday_marr2025"), verified=True)
add(id=f"{Q}-M-005", type="지표", indicator=f"{Q}-K2", importance=3, representative=False,
    statement="2026년 1~7월 혼인 건수는 14만 6,656건으로 같은 기간 기준 2018년 이후 가장 많다. 월별로는 1월 12.4% 늘고 5월 6.4% 줄었다가 6월 14.0%, 7월 9.3% 늘었다.",
    value=146656, unit="건", as_of="2026-07", region="KR",
    definition="국가데이터처 월간 인구동향 잠정치. 1~7월 누적. 누적 전년 대비 증감률은 보도에 없음.",
    extra={"monthly_yoy_pct": {"2026-01": 12.4, "2026-05": -6.4, "2026-06": 14.0, "2026-07": 9.3},
           "monthly_count": {"2026-01": 22640, "2026-05": 20368, "2026-06": 21075, "2026-07": 22282}},
    check_flags=["확인 필요: 1~7월 누적값은 단일 언론 보도. 보도자료 원문과 누적 증감률 확인 필요"],
    sources=src("wikitree_pop202607", "fn_pop202606", "segye_pop202605", "kdi_pop202601"), verified=True)
add(id=f"{Q}-M-006", type="지표", indicator=f"{Q}-K2", importance=2, representative=False,
    statement="2024년 결혼 1년차 신혼부부는 21만 2천 쌍으로 9.8% 늘었다. 결혼 5년 이내 신혼부부는 95만 2,026쌍으로 2.3% 줄었다. 초혼 신혼부부의 77.0%가 아파트에 살고 42.7%가 집을 가지고 있다.",
    value=212000, unit="쌍", as_of="2024-11-01", region="KR",
    definition="국가데이터처 2024년 신혼부부 통계(행정자료, 11월 1일 기준 혼인 신고 5년 이내 부부). 1년차 신혼부부 수.",
    extra={"newlyweds_5y": 952026, "with_children_pct": 51.2, "apartment_pct": 77.0, "home_owner_pct": 42.7, "home_owner_y1_pct": 35.8, "home_owner_y5_pct": 50.9},
    sources=src("newsis_newlywed2024"), verified=True)

# --- F2-K3 평균 초혼 연령 ---
add(id=f"{Q}-M-007", type="지표", indicator=f"{Q}-K3", importance=3, representative=True,
    statement="2025년 남성 평균 초혼 연령은 33.9세로 1년 전과 같다. 2023년 34.0세에서 2024년 33.9세로 내려간 뒤 멈췄다. 10년 전보다 1.3세 높다.",
    value=33.9, unit="세", as_of="2025", region="KR",
    definition="국가데이터처 혼인·이혼 통계, 남성 초혼 평균 연령. 2015년 값(32.6세)은 '10년 전보다 1.3세 상승' 보도로 역산.",
    prev_value=33.9, extra={"series": {"2015": 32.6, "2023": 34.0, "2024": 33.9, "2025": 33.9}},
    check_flags=["확인 필요: 2015년 값은 역산값. 2020~2022년 값은 원문 미확인"],
    sources=src("mt_marr2025", "etoday_marr2025", "newsis_marr2024"), verified=True)
add(id=f"{Q}-M-008", type="지표", indicator=f"{Q}-K3", importance=3, representative=True,
    statement="2025년 여성 평균 초혼 연령은 31.6세로 10년 전보다 1.7세 높다. 1년 전 변화는 보도마다 달라 0.1세 상승 또는 보합으로 읽힌다. 남녀 차이는 2.2세다.",
    value=31.6, unit="세", as_of="2025", region="KR",
    definition="국가데이터처 혼인·이혼 통계, 여성 초혼 평균 연령. 2015년 값(29.9세)은 역산.",
    prev_value=31.6, extra={"series": {"2015": 29.9, "2023": 31.5, "2024": 31.6, "2025": 31.6}},
    check_flags=["확인 필요: 2015년·2023년 값은 역산값, 2024~2025년 증감은 보도 간 상충(머니투데이 +0.1세, 뉴시스 2024년 31.6세). 2020~2022년 값 원문 미확인"],
    sources=src("mt_marr2025", "etoday_marr2025", "newsis_marr2024"), verified=True)

# --- F2-K4 출생아 수·합계출산율 ---
add(id=f"{Q}-M-009", type="지표", indicator=f"{Q}-K4", importance=3, representative=True,
    statement="2025년 출생아는 25만 4,341명으로 1년 전보다 6.7% 늘었다. 2023년 23만 28명이 바닥이었고 2년 연속 늘었다. 그래도 2020년 27만 2,337명보다 적다.",
    value=254341, unit="명", as_of="2025", region="KR",
    definition=f"{FB}. 연간 출생아 수(출생통계 확정).", prev_value=238317,
    extra={"series": {"2015": 438420, "2020": 272337, "2021": 260562, "2022": 249186, "2023": 230028, "2024": 238317, "2025": 254341}},
    sources=src("kosis_1b8000g", "fn_birth2025"), verified=True)
add(id=f"{Q}-M-010", type="지표", indicator=f"{Q}-K4", importance=3, representative=False,
    statement="2025년 합계출산율(여성 1명이 평생 낳을 것으로 기대되는 자녀 수)은 0.80명으로 2023년 0.72명에서 2년 연속 올랐다. 0.8명대는 4년 만이다.",
    value=0.799, unit="명", as_of="2025", region="KR",
    definition=f"{FB}. 팩트베이스 값 0.799, 공표 반올림 값 0.80.", prev_value=0.748,
    extra={"series": {"2015": 1.24, "2020": 0.84, "2021": 0.81, "2022": 0.78, "2023": 0.72, "2024": 0.748, "2025": 0.799}},
    sources=src("kosis_1b8000g", "fn_birth2025"), verified=True)
add(id=f"{Q}-M-011", type="지표", indicator=f"{Q}-K4", importance=3, representative=False,
    statement="2026년 1~7월 출생아는 17만 79명으로 1년 전보다 14.7% 늘었다. 7월 합계출산율은 0.89명, 2분기 합계출산율은 0.88명이다. 1~5월 누적 증가율 15.2%에 이어 높은 증가가 이어진다.",
    value=170079, unit="명", as_of="2026-07", region="KR",
    definition="국가데이터처 월간 인구동향 잠정치. 1~7월 누적 출생아.",
    extra={"cum_yoy_pct": {"2026-05": 15.2, "2026-06": 15.4, "2026-07": 14.7}, "monthly_tfr": {"2026-01": 0.99, "2026-06": 0.88, "2026-07": 0.89}, "q2_tfr": 0.88},
    sources=src("wikitree_pop202607", "fn_pop202606", "segye_pop202605", "kdi_pop202601"), verified=True)

# --- F2-K5 첫째아 출산 모 연령 ---
add(id=f"{Q}-M-012", type="지표", indicator=f"{Q}-K5", importance=3, representative=True,
    statement="2025년 첫째아를 낳은 어머니의 평균 연령은 33.2세로 1년 전보다 0.1세 올랐다. 2022년 33.0세, 2024년 33.1세로 해마다 0.1세 안팎 오른다.",
    value=33.2, unit="세", as_of="2025", region="KR",
    definition="국가데이터처 출생통계(확정), 첫째아 출산 시 모의 평균 연령.", prev_value=33.1,
    extra={"series": {"2022": 33.0, "2024": 33.1, "2025": 33.2}},
    check_flags=["확인 필요: 2023년 값과 KOSIS 통계표 값 원문 미확인(언론 보도 값)"],
    sources=src("nocut_birth2025", "dailian_birth2025", "newsis_birth2024", "newsis_birth2022"), verified=True)
add(id=f"{Q}-M-013", type="지표", indicator=f"{Q}-K5", importance=2, representative=False,
    statement="2025년 출생아 중 첫째아는 15만 8,700명으로 62.4%를 차지했다. 결혼 후 첫째아를 낳기까지 평균 2.4년이 걸렸고, 첫째아의 53.2%가 결혼 2년 이내에 태어났다. 전체 출산 모의 평균 연령은 33.8세, 35세 이상 산모 비중은 37.3%다.",
    value=62.4, unit="%", as_of="2025", region="KR",
    definition="국가데이터처 2025년 출생통계(확정). 첫째아 비중 = 첫째아 출생아 ÷ 전체 출생아.", prev_value=61.3,
    extra={"first_births": 158700, "first_share_2015": 52.3, "marriage_to_first_birth_years": 2.4, "first_within_2y_pct": 53.2,
           "mother_mean_age": {"2022": 33.5, "2023": 33.6, "2024": 33.7, "2025": 33.8}, "mother_35plus_pct": 37.3},
    sources=src("fn_birth2025", "nocut_birth2025", "dailian_birth2025"), verified=True)

# --- F2-K6 국내 이동 ---
add(id=f"{Q}-M-014", type="지표", indicator=f"{Q}-K6", importance=3, representative=True,
    statement="2025년 국내 이동자는 611만 8천 명으로 1년 전보다 2.6% 줄었다. 인구이동률은 12.0%로 0.3%p 내렸다. 2020년 773만 5천 명에서 5년 동안 연평균 4.6% 줄었다.",
    value=6117784, unit="명", as_of="2025", region="KR",
    definition=f"{FB}(총전입). 읍면동 경계를 넘어 전입 신고한 사람 수. 이동률은 언론 인용 공표값.",
    prev_value=6283319,
    extra={"series": {"2015": 7755286, "2020": 7735491, "2021": 7213422, "2022": 6152155, "2023": 6128738, "2024": 6283319, "2025": 6117784},
           "rate_pct": {"2021": 14.1, "2022": 12.0, "2023": 12.0, "2024": 12.3, "2025": 12.0},
           "inter_province": {"2020": 2534114, "2025": 2185913}, "within_sigungu": {"2020": 2926406, "2025": 2095832}},
    sources=src("kosis_1b26001", "herald_move2025", "newsis_move2024", "etoday_move2023", "tomato_move2022", "newsis_move2021"), verified=True)
add(id=f"{Q}-M-015", type="지표", indicator=f"{Q}-K6", importance=3, representative=False,
    statement="2026년 8월 국내 이동자는 47만 1천 명으로 1년 전보다 4.5% 줄었다. 이동률은 10.9%로 2000년 통계 작성 이후 8월 기준 가장 낮다. 6월에는 48만 1천 명으로 0.6% 늘었으나 7월 46만 8천 명(-15.5%)으로 다시 줄었다.",
    value=471000, unit="명", as_of="2026-08", region="KR",
    definition="국가데이터처 월간 국내인구이동통계. 8월 이동자 수.",
    extra={"monthly": {"2026-05": {"movers": 466000, "yoy_pct": -1.5, "rate": 10.8}, "2026-06": {"movers": 481000, "yoy_pct": 0.6, "rate": 11.5},
                       "2026-07": {"movers": 468000, "yoy_pct": -15.5, "rate": 10.8}, "2026-08": {"movers": 471000, "yoy_pct": -4.5, "rate": 10.9}},
           "h1_cum_yoy_pct": 2.1},
    sources=src("sbs_move202608", "kdi_move202607", "newsis_move202606", "kdi_move202605"), verified=True)
add(id=f"{Q}-M-016", type="지표", indicator=f"{Q}-K6", importance=2, representative=False,
    statement="2025년 연령별 이동률은 20대 24.3%, 30대 20.4%로 가장 높다. 20대만 1년 전(23.9%)보다 올랐고 30대는 21.0%에서 내렸다. 10세 미만은 12.9%다. 70대와 80세 이상은 1년 전과 비슷하다.",
    value=24.3, unit="%", as_of="2025", region="KR",
    definition="국가데이터처 국내인구이동통계, 연령대 인구 100명당 이동자 수.", prev_value=23.9,
    extra={"20s": {"2024": 23.9, "2025": 24.3}, "30s": {"2024": 21.0, "2025": 20.4}, "under10_2025": 12.9},
    sources=src("herald_move2025", "newsis_move2024"), verified=True)

# --- F2-K7 주택·가족 사유 이동 비중 ---
add(id=f"{Q}-M-017", type="지표", indicator=f"{Q}-K7", importance=3, representative=True,
    statement="2025년 전입 사유 중 주택 사유는 33.7%로 1년 전보다 0.8%p 내렸다. 주택 사유 이동자는 206만 5천 명으로 10만 5천 명 줄어 모든 사유 중 가장 많이 줄었다. 2021년 37.6%에서 4년 동안 3.9%p 내렸다. 시도 안 이동에서는 주택 사유가 42.5%로 가장 많다.",
    value=33.7, unit="%", as_of="2025", region="KR",
    definition="국가데이터처 국내인구이동통계 전입 사유별 이동자 비중(주택 사유). 연도별 값은 각 해 발표 보도 인용.",
    prev_value=34.5, extra={"series": {"2021": 37.6, "2022": 34.4, "2023": 34.0, "2024": 34.5, "2025": 33.7}, "within_province_2025": 42.5},
    check_flags=["확인 필요: 팩트베이스 L02(DT_1B26B24 전입사유별 1인이동) 값이 비어 있어 보도 인용값 사용. KOSIS 표로 대조 필요"],
    sources=src("herald_move2025", "newsis_move2024", "etoday_move2023", "tomato_move2022", "newsis_move2021"), verified=True)
add(id=f"{Q}-M-018", type="지표", indicator=f"{Q}-K7", importance=3, representative=True,
    statement="2025년 전입 사유 중 가족 사유는 25.9%로 1년 전보다 1.2%p 올랐다. 2021년 23.0%에서 해마다 올랐다. 주택과 가족 사유를 합하면 59.6%다. 직업 사유는 21.4%로 시도 간 이동에서 가장 많은 사유(32.5%)다.",
    value=25.9, unit="%", as_of="2025", region="KR",
    definition="국가데이터처 국내인구이동통계 전입 사유별 이동자 비중(가족 사유).",
    prev_value=24.7, extra={"series": {"2021": 23.0, "2022": 23.7, "2023": 24.1, "2024": 24.7, "2025": 25.9},
                            "housing_plus_family": {"2021": 60.6, "2022": 58.1, "2023": 58.1, "2024": 59.2, "2025": 59.6},
                            "job": {"2021": 22.0, "2022": 23.4, "2023": 22.8, "2024": 21.7, "2025": 21.4}},
    check_flags=["확인 필요: 팩트베이스 L02 값이 비어 있어 보도 인용값 사용. KOSIS 표로 대조 필요"],
    sources=src("herald_move2025", "newsis_move2024", "etoday_move2023", "tomato_move2022", "newsis_move2021"), verified=True)
add(id=f"{Q}-M-019", type="지표", indicator=f"{Q}-K7", importance=2, representative=False,
    statement="2024년도 주거실태조사에서 현재 집에 산 지 2년 이내인 가구는 30.3%로 1.9%p 줄었다. 평균 거주기간은 8.4년(자가 11.5년, 임차 3.6년)이다. 자발적 이사 이유는 시설·설비 상향 47.2%, 직주근접 30.6% 순이고, 비자발적 이유는 계약 만기 18.1%가 가장 많다. 1인당 주거면적은 전체 36.0㎡, 청년가구 31.1㎡, 신혼부부 27.4㎡, 고령가구 46.6㎡다.",
    value=30.3, unit="%", as_of="2024", region="KR",
    definition="국토교통부 2024년도 주거실태조사(표본조사). 현 주택 거주기간 2년 이내 가구 비율. 이사 이유는 이사 경험 가구 중복 응답.",
    extra={"avg_tenure_years": 8.4, "tenure_owner": 11.5, "tenure_renter": 3.6,
           "move_reason_voluntary": {"시설·설비 상향": 47.2, "직주근접": 30.6, "교통 편리 등": 25.5},
           "move_reason_involuntary": {"계약 만기": 18.1, "집값 부담": 8.3, "재개발·재건축": 3.7},
           "area_per_person": {"전체": 36.0, "청년가구": 31.1, "신혼부부": 27.4, "고령가구": 46.6}, "area_per_household": 68.1,
           "newlywed_owner_occupancy": 43.9, "youth_below_min_standard": 8.2},
    check_flags=["확인 필요: 발표일이 보도마다 다름(2025-11-15 보도와 2025-12-11 보도). 주거실태조사 보고서 원문 미열람"],
    sources=src("newdaily_housing2024", "kgnews_housing2024"), verified=True)
add(id=f"{Q}-M-020", type="지표", indicator=f"{Q}-K7", importance=1, representative=False,
    statement="국토연구원 보고서는 평균 거주기간을 청년 1.6년, 신혼부부 2.5년, 고령가구 14.7년으로 제시한다. 일반가구는 8.0년이다.",
    value=1.6, unit="년", as_of="확인 필요", region="KR",
    definition="국토연구원 '계층별 주거위상 진단과 향후 정책방향'의 계층별 평균 거주기간. 기준 연도 미표기.",
    extra={"tenure_years": {"청년": 1.6, "신혼부부": 2.5, "고령가구": 14.7, "일반가구": 8.0}},
    check_flags=["확인 필요: 보고서 원문 미열람, 기준 연도 불명. 언론 인용만 확인"],
    sources=src("tf_krihs"), verified=False)

# --- F2-K8 주된 일자리 퇴직 연령 ---
add(id=f"{Q}-M-021", type="지표", indicator=f"{Q}-K8", importance=3, representative=True,
    statement="2026년 5월 55~79세가 가장 오래 근무한 일자리를 그만둔 평균 연령은 53.0세다. 남성 55.3세, 여성 51.1세다. 2024년 52.8세, 2025년 52.9세에서 해마다 0.1세씩 올랐다.",
    value=53.0, unit="세", as_of="2026-05", region="KR",
    definition="국가데이터처 경제활동인구조사 고령층 부가조사(매년 5월). 55~79세 중 가장 오래 근무한 일자리를 그만둔 사람의 이직 당시 평균 연령.",
    prev_value=52.9, extra={"series": {"2024": 52.8, "2025": 52.9, "2026": 53.0}, "by_sex_2026": {"남": 55.3, "여": 51.1}, "by_sex_2025": {"남": 55.0, "여": 51.1}},
    check_flags=["확인 필요: 2024년 값의 연령 기준이 보도마다 다름(뉴시스 55~79세 52.8세·55~64세 49.4세, 데일리안은 49.4세를 55~79세로 표기). KOSIS 표로 대조 필요"],
    sources=src("newsis_old2026", "newsis_old2025", "newsis_old2024", "dailian_old2024"), verified=True)
add(id=f"{Q}-M-022", type="지표", indicator=f"{Q}-K8", importance=2, representative=False,
    statement="55~64세로 좁히면 가장 오래 근무한 일자리를 그만둔 평균 연령은 2026년 49.0세다. 남성 51.3세, 여성 47.0세다. 2024년에는 49.4세였다. 정년퇴직으로 그만둔 사람은 9.0%뿐이다.",
    value=49.0, unit="세", as_of="2026-05", region="KR",
    definition="고령층 부가조사 55~64세 기준 주된 일자리 이직 연령. 법정 정년은 60세 이상.",
    prev_value=49.4, extra={"series": {"2023": 49.4, "2024": 49.4, "2026": 49.0}, "retirement_reason_pct": 9.0},
    check_flags=["확인 필요: 2025년 55~64세 값 원문 미확인. 2024년 값 연령 기준 보도 상충"],
    sources=src("segye_old2026", "newsis_old2024"), verified=True)
add(id=f"{Q}-M-023", type="지표", indicator=f"{Q}-K8", importance=2, representative=False,
    statement="2026년 주된 일자리를 그만둔 이유는 사업 부진·조업 중단·휴폐업 24.9%, 건강 악화 22.1%, 가족 돌봄 15.2% 순이다. 55~79세의 69.2%가 앞으로도 일하기를 원하고, 평균 73.6세까지 일하고 싶어 한다.",
    value=69.2, unit="%", as_of="2026-05", region="KR",
    definition="고령층 부가조사. 장래 근로 희망 비중과 희망 근로 연령.", prev_value=69.4,
    extra={"reasons_2026": {"사업부진·조업중단·휴폐업": 24.9, "건강 악화": 22.1, "가족 돌봄": 15.2},
           "reasons_2025": {"사업부진·조업중단·휴폐업": 25.0, "건강 악화": 22.4, "가족 돌봄": 14.7},
           "desired_work_age": {"2025": 73.4, "2026": 73.6}},
    sources=src("newsis_old2026", "newsis_old2025"), verified=True)

# =====================================================================
# 사건 (E) 최근 12개월
# =====================================================================
add(id=f"{Q}-E-001", type="사건", importance=2, date="2025-10-15", actor="재정경제부·국토교통부",
    statement="정부가 10·15 주택시장 안정화 대책을 발표했다. 서울 전역과 경기 12곳을 규제지역·토지거래허가구역으로 묶었다. 허가구역에서 집을 사면 2년간 실거주해야 하고, 규제지역 주택담보대출비율(LTV)은 무주택자 40%로 낮췄다.",
    sources=src("herald_1015"), verified=True)
add(id=f"{Q}-E-002", type="사건", importance=2, date="2025-11-03", actor="더불어민주당",
    statement="여당 정년연장 특별위원회가 첫 회의를 열었다. 약 한 달 뒤 법정 정년을 단계적으로 65세까지 올리는 세 가지 안을 냈으나 노사가 모두 반대해 2025년 입법은 무산됐다.",
    sources=src("khanweekly_retire"), verified=True)
add(id=f"{Q}-E-003", type="사건", importance=1, date="2025-12-12", actor="국가데이터처",
    statement="2024년 신혼부부 통계를 발표했다. 결혼 1년차 신혼부부가 9.8% 늘어 통계 작성 이후 가장 크게 늘었다.",
    sources=src("newsis_newlywed2024"), verified=True)
add(id=f"{Q}-E-004", type="사건", importance=2, date="2026-01-29", actor="국가데이터처",
    statement="2025년 국내인구이동통계를 발표했다. 이동자 611만 8천 명, 이동률 12.0%로 51년 만에 가장 적은 수준이다.",
    sources=src("herald_move2025"), verified=True)
add(id=f"{Q}-E-005", type="사건", importance=3, date="2026-03-19", actor="국가데이터처",
    statement="2025년 혼인·이혼 통계를 발표했다. 혼인 24만 건으로 7년 만에 가장 많았고, 초혼 부부 중 아내가 연상인 비중이 20.2%로 처음 20%를 넘었다.",
    sources=src("etoday_marr2025", "mt_marr2025"), verified=True)
add(id=f"{Q}-E-006", type="사건", importance=1, date="2026-06", actor="농림축산식품부",
    statement="농어촌 기본소득 시범사업 지역을 7곳 늘렸다. 국가데이터처는 6월 인구이동 증가 요인 중 하나로 일부 새 시범 지역의 전입 증가를 들었다.",
    check_flags=["확인 필요: 지역 추가 정확한 일자 미확인(7월 29일 보도의 '지난달' 표기)"],
    sources=src("newsis_move202606"), verified=True)
add(id=f"{Q}-E-007", type="사건", importance=2, date="2026-08-04", actor="고용노동부",
    statement="대통령 업무보고에서 '세대 상생형 정년연장 법제화'를 하반기 과제로 올렸다. 6월 여당 초안은 2029년 정년 61세에서 2년마다 1세씩 올려 2037년 65세로 하는 안이지만 아직 통과된 법은 없다.",
    sources=src("khanweekly_retire"), verified=True)
add(id=f"{Q}-E-008", type="사건", importance=2, date="2026-08-05", actor="국가데이터처",
    statement="2026년 5월 고령층 부가조사 결과를 발표했다. 주된 일자리 이직 연령은 53.0세, 희망 근로 연령은 73.6세다.",
    sources=src("newsis_old2026"), verified=True)
add(id=f"{Q}-E-009", type="사건", importance=3, date="2026-08-26", actor="국가데이터처",
    statement="2025년 출생통계(확정)를 발표했다. 출생아 25만 4천 명, 합계출산율 0.80명으로 2년 연속 늘었고 증가분 대부분이 첫째아다.",
    sources=src("fn_birth2025", "nocut_birth2025"), verified=True)
add(id=f"{Q}-E-010", type="사건", importance=2, date="2026-09-23", actor="국가데이터처",
    statement="7월 인구동향과 8월 국내인구이동통계를 발표했다. 1~7월 출생아는 14.7% 늘었고, 8월 이동자는 1973년 이후 8월 기준 가장 적었다.",
    sources=src("wikitree_pop202607", "sbs_move202608"), verified=True)

# =====================================================================
# 해석 (I)
# =====================================================================
add(id=f"{Q}-I-001", type="해석", importance=3, target="결혼 빈도", direction="강화",
    statement="결혼은 3년 연속 늘었고 2025년 증가 폭이 직전 4년 평균보다 크다. 2026년 1~7월도 2018년 이후 가장 많아 증가가 이어진다. 월별로는 5월에 줄어든 달이 있어 매달 늘지는 않는다.",
    basis=[f"{Q}-M-004", f"{Q}-M-005", f"{Q}-E-005"])
add(id=f"{Q}-I-002", type="해석", importance=3, target="출산 빈도", direction="강화",
    statement="출생아는 5년 추세로는 줄었지만 2024년부터 2년 연속 늘었고 2026년 1~7월에는 14.7% 늘었다. 증가분 대부분이 첫째아이고 첫째아의 절반 이상이 결혼 2년 안에 태어난다. 2024~2025년 늘어난 결혼이 1~2년 뒤 첫째아 출산으로 이어지는 구조다.",
    basis=[f"{Q}-M-009", f"{Q}-M-011", f"{Q}-M-013", f"{Q}-M-004"])
add(id=f"{Q}-I-003", type="해석", importance=3, target="결혼·출산 시기", direction="중립",
    statement="초혼 연령(남 33.9세, 여 31.6세)은 2023년 이후 오르지 않고, 첫째아 출산 연령(33.2세)은 해마다 0.1세 안팎만 오른다. 시기가 늦어지는 흐름은 멈춘 상태다.",
    basis=[f"{Q}-M-007", f"{Q}-M-008", f"{Q}-M-012", f"{Q}-M-013"])
add(id=f"{Q}-I-004", type="해석", importance=3, target="이사 빈도", direction="약화",
    statement="이사는 5년째 줄어드는 추세이고 2026년 8월 이동률도 8월 기준 가장 낮다. 줄어드는 몫은 주로 주택 사유 이동이다. 가족 사유 비중은 해마다 올라 결혼·출산 같은 가족 전환이 이사의 이유로 차지하는 몫이 커진다. 2025년 10월 규제지역 확대와 실거주 의무로 주택 거래 이동이 늘기 어려운 조건이다.",
    basis=[f"{Q}-M-014", f"{Q}-M-015", f"{Q}-M-017", f"{Q}-M-018", f"{Q}-E-001"])
add(id=f"{Q}-I-005", type="해석", importance=2, target="청년 독립", direction="약화",
    statement="20~34세 1인가구 수는 2024년을 정점으로 2025년 줄었다. 20~24세 인구가 줄어든 영향이 크다. 청년패널의 주거 독립 비율은 30% 안팎으로 청년 10명 중 7명은 아직 부모와 산다. 청년 독립 비율 자체를 재는 국가 통계는 이번에 확보하지 못했다.",
    basis=[f"{Q}-M-001", f"{Q}-M-002"])
add(id=f"{Q}-I-006", type="해석", importance=2, target="은퇴 시기", direction="중립",
    statement="주된 일자리를 그만두는 나이는 53세 안팎에서 거의 움직이지 않는다. 법정 정년 60세보다 7년 이르고, 정년퇴직으로 그만둔 사람은 9.0%뿐이다. 희망 근로 연령은 73.6세라 주된 일자리를 떠난 뒤 20년 가까이 다른 일자리를 찾는 구간이 생긴다. 정년연장 법은 아직 통과되지 않았다.",
    basis=[f"{Q}-M-021", f"{Q}-M-022", f"{Q}-M-023", f"{Q}-E-007"])
add(id=f"{Q}-I-007", type="해석", importance=2, target="전환이 일어나는 평형대", direction="중립",
    statement="1인가구의 74.2%가 전용 60㎡ 이하에 살아 청년 독립은 소형 평형에서 시작된다. 신혼부부는 77.0%가 아파트에 살지만 1인당 면적은 27.4㎡로 전체 평균(36.0㎡)보다 좁다. 고령가구는 1인당 46.6㎡로 가장 넓다. 신혼·자녀양육 전환이 중형으로 옮겨 가는지는 면적 구간 통계로 확인하지 못했다.",
    basis=[f"{Q}-M-003", f"{Q}-M-006", f"{Q}-M-019"])

# =====================================================================
# 세부 전망 (F)
# =====================================================================
add(id=f"{Q}-F-001", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2026년 연간 혼인 건수는 25만 건 이상일 것이다.", due="2027-03-31", condition="없음",
    method="국가데이터처 2026년 혼인·이혼 통계(2027년 3월 발표)의 연간 혼인 건수가 250,000건 이상이면 적중",
    basis=[f"{Q}-M-004", f"{Q}-M-005"])
add(id=f"{Q}-F-002", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2026년 출생아는 27만 명 이상, 합계출산율은 0.85명 이상일 것이다.", due="2027-02-28", condition="없음",
    method="국가데이터처 2026년 출생·사망통계 잠정 결과(2027년 2월 발표)에서 출생아 270,000명 이상이고 합계출산율 0.85명 이상이면 적중",
    basis=[f"{Q}-M-009", f"{Q}-M-010", f"{Q}-M-011"])
add(id=f"{Q}-F-003", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 국내 이동자는 2025년(611만 8천 명)보다 적을 것이다.", due="2027-01-31", condition="없음",
    method="국가데이터처 2026년 국내인구이동통계(2027년 1월 발표)의 연간 이동자 수가 6,117,784명 미만이면 적중",
    basis=[f"{Q}-M-014", f"{Q}-M-015"])
add(id=f"{Q}-F-004", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 전입 사유 중 가족 사유 비중은 26% 이상으로 오르고 주택 사유 비중은 33.7% 이하로 내려갈 것이다.", due="2027-01-31", condition="없음",
    method="국가데이터처 2026년 국내인구이동통계의 전입 사유별 비중에서 가족 사유 26.0% 이상, 주택 사유 33.7% 이하를 모두 충족하면 적중",
    basis=[f"{Q}-M-017", f"{Q}-M-018"])
add(id=f"{Q}-F-005", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2027년 5월 고령층 부가조사의 주된 일자리 이직 연령(55~79세)은 52.8~53.4세 범위에 머물 것이다.", due="2027-08-31", condition="정년연장 법이 2027년 5월 이전에 시행되지 않음",
    method="국가데이터처 2027년 5월 고령층 부가조사(2027년 7~8월 발표)의 55~79세 가장 오래 근무한 일자리 이직 평균 연령이 52.8세 이상 53.4세 이하면 적중",
    basis=[f"{Q}-M-021", f"{Q}-M-022"])
add(id=f"{Q}-F-006", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 20~34세 1인가구 수는 2025년(222만 5천 가구)보다 적을 것이다.", due="2027-07-31", condition="없음",
    method="국가데이터처 2026년 인구주택총조사 등록센서스(2027년 7월 발표) 성·연령별 1인가구 표에서 20~34세 합계가 2,225,010가구 미만이면 적중",
    basis=[f"{Q}-M-001"])

# =====================================================================
# 메인 질문 시나리오
# =====================================================================
add(id=f"{Q}-F-101", type="전망", importance=3, forecast_status="진행 중", scenario="낙관", result=None,
    statement="2027년 말까지 결혼과 출산이 함께 늘어 생애 전환 빈도가 다시 높아진다. 혼인은 2년 더 늘고 출생아는 27만 명을 넘으며, 결혼·출산에 따른 가족 사유 이사가 늘어 전체 이사 감소 폭을 줄인다.",
    milestones=[{"by": "2027-02", "text": "2026년 출생아 27만 명 이상, 합계출산율 0.85명 이상"},
                {"by": "2027-03", "text": "2026년 혼인 건수 25만 건 이상"},
                {"by": "2027-12", "text": "2027년 1~10월 누적 출생아가 2026년 같은 기간보다 많음"}],
    due="2027-12-31", condition="주택 대출 규제가 더 강해지지 않음",
    method="세 가지 중 두 가지 이상 충족 시 적중: (1) 2026년 혼인 건수 25만 건 이상 (2) 2026년 출생아 27만 명 이상 (3) 2027년 1~10월 누적 출생아가 1년 전보다 많음(2027년 12월 인구동향)",
    basis=[f"{Q}-M-004", f"{Q}-M-005", f"{Q}-M-009", f"{Q}-M-011", f"{Q}-M-018"],
    signposts=[{"id": f"{Q}-F-001", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-002", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-004", "on_hit": "낙관"}])
add(id=f"{Q}-F-102", type="전망", importance=3, forecast_status="진행 중", scenario="비관", result=None,
    statement="2027년 말까지 결혼 증가가 멈추고 출생아 증가도 둔해진다. 혼인 건수는 24만 건대에 머물고, 이사는 계속 줄며, 청년 1인가구도 줄어 독립·결혼·이사 모두 빈도가 낮아진다.",
    milestones=[{"by": "2027-01", "text": "2026년 국내 이동자 수가 2025년보다 적음"},
                {"by": "2027-03", "text": "2026년 혼인 건수 25만 건 미만"},
                {"by": "2027-07", "text": "2026년 20~34세 1인가구 수가 2025년보다 적음"}],
    due="2027-12-31", condition="없음", method="낙관 조건 중 하나 이하 충족 시 적중",
    basis=[f"{Q}-M-001", f"{Q}-M-014", f"{Q}-M-015", f"{Q}-M-005"],
    signposts=[{"id": f"{Q}-F-001", "on_miss": "비관"}, {"id": f"{Q}-F-003", "on_hit": "비관"},
               {"id": f"{Q}-F-006", "on_hit": "비관"}])

# ---------- 공통 마무리: patches.jsonl 적용 → 검증 → records.jsonl ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from validate import finish
finish(records, Path(__file__).parent)
