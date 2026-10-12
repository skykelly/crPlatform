"""N2 R1 4유형 기록 생성 + 규칙 검증. 출력: 같은 폴더 records.jsonl
실행: python3 build_records.py  (검증 오류가 있으면 exit 1)
"""
import sys
from pathlib import Path

Q, R = "N2", "R1"
# 출처 사전: key → url·publisher·date·grade (A 공식 1차 / B 언론·연구기관 / C 출처 불명)
SRC = {
    # 팩트베이스 (KOSIS 공식 API)
    "kosis_hhexp": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1L9U101&conn_path=I2",
                    "publisher": "국가데이터처 KOSIS (DT_1L9U101 가구당 월평균 가계수지, 가계동향조사)", "date": "2026-10-11", "grade": "A"},
    "kosis_hh": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1JC1517&conn_path=I2",
                 "publisher": "국가데이터처 KOSIS (DT_1JC1517 가구주의 연령·성별 가구, 인구총조사)", "date": "2026-10-11", "grade": "A"},
    "kosis_dual": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1ES4F09S&conn_path=I2",
                   "publisher": "국가데이터처 KOSIS (DT_1ES4F09S 시도별 맞벌이 가구, 지역별고용조사)", "date": "2026-10-11", "grade": "A"},
    "kosis_mig": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1B26001_A01&conn_path=I2",
                  "publisher": "국가데이터처 KOSIS (DT_1B26001_A01 시군구별 이동자수, 국내인구이동통계)", "date": "2026-10-11", "grade": "A"},
    # 공식 발표 게재
    "kdi_msit": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=278744",
                 "publisher": "과학기술정보통신부 보도자료 2025 인터넷이용실태조사 (KDI 경제정보센터 게재)", "date": "2026-03-31", "grade": "A"},
    # 언론·연구기관·업계
    "herald_mig": {"url": "https://www.heraldk.com/article/2026012818471712823",
                   "publisher": "헤럴드경제 (국가데이터처 2025년 국내인구이동통계 인용)", "date": "2026-01-28", "grade": "B"},
    "newsis_mig": {"url": "https://www.newsis.com/view/NISX20260729_0003727662",
                   "publisher": "뉴시스 (국가데이터처 2026년 6월 국내인구이동통계 인용)", "date": "2026-07-29", "grade": "B"},
    "korcham_sub": {"url": "https://www.fnnews.com/news/202502190600589487",
                    "publisher": "파이낸셜뉴스·연합뉴스 (대한상공회의소·마크로밀엠브레인 구독서비스 이용 조사 인용)", "date": "2025-02-19", "grade": "B"},
    "hk_embrain": {"url": "https://www.hankyung.com/article/202602118933g",
                   "publisher": "한국경제 (엠브레인 트렌드모니터 가전 구독 조사 인용)", "date": "2026-02-12", "grade": "B"},
    "herald_coway": {"url": "https://www.heraldk.com/article/2026050717254859414",
                     "publisher": "헤럴드경제 (코웨이 2026년 1분기 실적 인용)", "date": "2026-05-07", "grade": "B"},
    "newdaily_lg": {"url": "https://biz.newdaily.co.kr/site/data/html/2026/01/30/2026013000355.amp.html",
                    "publisher": "뉴데일리경제 (LG전자 2025년 실적 발표 인용)", "date": "2026-01-30", "grade": "B"},
    "inews_sub": {"url": "https://inews24.com/view/2011740",
                  "publisher": "아이뉴스24 (삼성전자·LG전자 가전 구독 사업 인용)", "date": "2026-10-04", "grade": "B"},
    "woori_card": {"url": "https://www.smarttoday.co.kr/ko-kr/articles/100191",
                   "publisher": "스마트투데이 (우리카드 결제 데이터 인용)", "date": "2025-12-31", "grade": "B"},
    "mk_care": {"url": "https://v.daum.net/v/XgKVjmpXTy",
                "publisher": "매일경제 (삼성전자·LG전자 가전 세척 서비스 인용)", "date": "2026-05-06", "grade": "B"},
    "iboss_move": {"url": "https://www.i-boss.co.kr/ab-74668-1466",
                   "publisher": "엠브레인 트렌드모니터 이사 관련 조사 (아이보스 게재, 조사 종료일 기준 날짜)", "date": "2019-12-26", "grade": "B"},
    "khan_pet": {"url": "https://www.khan.co.kr/article/202602121457001/",
                 "publisher": "경향신문 (농림축산식품부 2025 반려동물 양육현황조사 인용)", "date": "2026-02-12", "grade": "B"},
    "dailyvet_pet": {"url": "https://www.dailyvet.co.kr/v/273697",
                     "publisher": "데일리벳 (농림축산식품부 2025 반려동물 양육현황조사 인용)", "date": "2026-02-18", "grade": "B"},
    "newsseoul_pet": {"url": "https://www.newsseoul.co.kr/news/view/1065584423215514",
                      "publisher": "뉴스서울 (농림축산식품부 2025 동물복지 국민의식조사 인용)", "date": "2026-02-12", "grade": "B"},
    "tf_pet": {"url": "https://news.tf.co.kr/read/ogmeta/2292707.htm",
               "publisher": "더팩트 (농림축산식품부 2025 동물복지 국민의식조사 인용)", "date": "2026-02-12", "grade": "B"},
    "dailyvet_pet23": {"url": "https://www.dailyvet.co.kr/?p=203237",
                       "publisher": "데일리벳 (농림축산식품부 2023 동물복지 국민의식조사 인용)", "date": "2024-01-22", "grade": "B"},
    "kb_pet": {"url": "https://kbthink.com/investment/deepdive/research/250629-2.html",
               "publisher": "KB경영연구소 2025 한국 반려동물 보고서 (KB Think 게재)", "date": "2025-06-29", "grade": "B"},
    "segye_emerg": {"url": "https://www.segye.com/newsView/20250902515670",
                    "publisher": "세계일보 (보건복지부 응급안전안심서비스 계획 인용)", "date": "2025-09-02", "grade": "B"},
    "sbs_care": {"url": "https://biz.sbs.co.kr/amp/article/20000283543",
                 "publisher": "SBS Biz (보건복지부 2026 통합돌봄 계획 인용)", "date": "2026-01-08", "grade": "B"},
    "mt_msit": {"url": "https://www.mt.co.kr/tech/2026/03/31/2026033111234563860",
                "publisher": "머니투데이 (과학기술정보통신부 2025 인터넷이용실태조사 인용)", "date": "2026-03-31", "grade": "B"},
    "khan_kca": {"url": "https://www.khan.co.kr/article/202512191430001/",
                 "publisher": "경향신문 (한국소비자원 2025 한국의 소비생활지표 인용)", "date": "2025-12-19", "grade": "B"},
}
def src(*keys): return [dict(SRC[k], key=k) for k in keys]

base = dict(question=Q, question_version="v1.0", first_seen=R, last_seen=R, status="유효", replaces=None, check_flags=[])
records = []
def add(**kw):
    r = dict(base); r.update(kw); records.append(r)

# ======================================================================
# 지표 (M)
# ======================================================================
# --- N2-K1 가전 렌탈·구독 ---
add(id=f"{Q}-M-001", type="지표", indicator=f"{Q}-K1", importance=3, representative=True,
    statement="2026년 1월 전국 성인 1,000명 조사에서 가전 구독 서비스를 현재 이용한다는 응답은 11.1%였다. 대형 가전 구독을 잘 모른다는 응답은 68.8%였다.",
    value=11.1, unit="%", as_of="2026-01", region="KR",
    definition="엠브레인 트렌드모니터 가전 구독 이용 조사(2026-01-23~27, 성인 1,000명). 개인 응답 기준이며 가구 이용률이 아니다.",
    prev_value=None, sources=src("hk_embrain"), verified=True,
    check_flags=["확인 필요: 개인 응답 기준이라 가구 이용률과 다르고, '가전 구독'에 정수기 렌탈이 포함되는지 정의가 기사에 없음"])
add(id=f"{Q}-M-002", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="2025년 2월 대한상공회의소 조사에서 성인 응답자의 33.8%가 정수기 구독(렌탈)을 이용했다고 답했다. 같은 조사에서 쇼핑 멤버십 이용은 52.4%였다.",
    value=33.8, unit="%", as_of="2025-02", region="KR",
    definition="대한상공회의소·마크로밀엠브레인 구독서비스 이용 조사(성인 1,000명, 복수응답). 개인 응답 기준, 현재 이용과 경험 여부 구분이 기사에 없음.",
    prev_value=None, sources=src("korcham_sub"), verified=True,
    check_flags=["확인 필요: 문항이 현재 이용인지 이용 경험인지 기사에 없음. 조사 기간 미기재. 생활용품 정기배송 항목은 따로 없음"])
add(id=f"{Q}-M-003", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="코웨이의 국내 렌탈 계정은 2026년 1분기 748만 개였다. 해외를 합친 전체 계정은 1,173만 개로 1년 전보다 10.9% 늘었다.",
    value=748, unit="만 계정", as_of="2026-Q1", region="KR",
    definition="코웨이 2026년 1분기 실적 기준 국내 렌탈 계정 수. 계정은 제품 단위라 가구 수로 바꿀 수 없다.",
    prev_value=None, sources=src("herald_coway"), verified=True)
add(id=f"{Q}-M-004", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="LG전자의 2025년 가전 구독 매출은 약 2조 5천억 원으로 1년 전보다 29% 늘었다. 2026년 상반기 구독 매출은 약 1조 3천억 원이다.",
    value=2.5, unit="조 원", as_of="2025", region="KR+해외",
    definition="LG전자 가전 구독 매출(국내·해외 합산, 언론 보도 기준). 회사 공시는 '2조 원 돌파'로 표현됨.",
    prev_value=None, extra={"series": {"2025": 2.5, "2026H1": 1.3}}, sources=src("inews_sub", "newdaily_lg"), verified=True,
    check_flags=["확인 필요: 2조 5천억 원은 언론 추정치이며 국내 매출 비중은 공개되지 않음"])
add(id=f"{Q}-M-005", type="지표", indicator=f"{Q}-K1", importance=1, representative=False,
    statement="우리카드 결제 데이터에서 가전 구독 결제는 2023년 대비 2025년(10월까지) 72.2% 늘었다. 이용자의 60.4%가 40~50대였다.",
    value=72.2, unit="% (2023년 대비 증가)", as_of="2025-10", region="KR",
    definition="우리카드 신용카드 결제 데이터, 2023년 대비 2025년 1~10월 증가율. 결제액 기준이며 이용 가구 비율이 아니다.",
    prev_value=None, sources=src("woori_card"), verified=True,
    check_flags=["확인 필요: 한 카드사 결제 데이터라 시장 전체를 대표하지 않음"])

# --- N2-K2 가사·청소 서비스 ---
add(id=f"{Q}-M-006", type="지표", indicator=f"{Q}-K2", importance=3, representative=True,
    statement="2025년 전체 가구의 월평균 가사서비스 지출은 10,103원으로 2024년(13,606원)보다 25.7% 줄었다. 2019~2024년에는 12,000~15,000원 사이에 머물렀다.",
    value=10103, unit="원/월", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 가계동향조사 전체가구 월평균 소비지출 중 가사서비스(명목). 이용 가구 비율이 아니라 전체 가구 평균 지출이다.",
    prev_value=13606, extra={"series": {"2019": 14122, "2020": 12369, "2021": 15001, "2022": 12849, "2023": 13470, "2024": 13606, "2025": 10103}},
    sources=src("kosis_hhexp"), verified=True,
    check_flags=["확인 필요: 명목값이며 소비자물가로 실질화하지 않음. 2025년 감소 폭이 커서 분류·표본 변경 여부 확인 필요"])
add(id=f"{Q}-M-007", type="지표", indicator=f"{Q}-K2", importance=2, representative=False,
    statement="우리카드 결제 데이터에서 가사도우미 결제는 2023년 대비 2025년(10월까지) 25.7% 늘었다. 세탁대행은 9.4% 늘었다. 가사도우미 이용자의 60% 이상이 30~40대였다. 가사도우미·세탁대행·가전 구독 이용자의 60~70%는 자녀가 있는 가구였다.",
    value=25.7, unit="% (2023년 대비 증가)", as_of="2025-10", region="KR",
    definition="우리카드 신용카드 결제 데이터, 2023년 대비 2025년 1~10월 증가율. 결제액 기준.",
    prev_value=None, sources=src("woori_card"), verified=True,
    check_flags=["확인 필요: 한 카드사 결제 데이터라 시장 전체를 대표하지 않으며, 가계동향 가사서비스 지출 감소(M-006)와 방향이 다름"])
add(id=f"{Q}-M-008", type="지표", indicator=f"{Q}-K2", importance=2, representative=False,
    statement="2025년 유배우 가구 중 맞벌이 가구는 48.6%(615만 가구)였다. 2020년 45.0%에서 5년간 3.6%p 늘었다.",
    value=48.6, unit="%", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 지역별고용조사 유배우 가구 중 맞벌이 가구 비율. 가사 외주 수요를 만드는 생활 변화(수요 동인) 기록.",
    prev_value=48.0, extra={"series": {"2020": 45.0, "2021": 45.9, "2022": 46.1, "2023": 48.2, "2024": 48.0, "2025": 48.6}},
    sources=src("kosis_dual"), verified=True)
add(id=f"{Q}-M-009", type="지표", indicator=f"{Q}-K2", importance=2, representative=False,
    statement="2025년 1인가구는 일반가구의 36.6%(824만 가구)로 1년 전보다 0.6%p 늘었다. 2020년 31.7%에서 5년간 4.9%p 늘었다.",
    value=36.6, unit="%", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 인구총조사 일반가구 중 1인가구 비율(1인가구 수 ÷ 일반가구 수, DT_1JC1517 가구주 연령 합계). 수요 동인 기록.",
    prev_value=36.1, extra={"series": {"2020": 31.7, "2021": 33.4, "2022": 34.5, "2023": 35.5, "2024": 36.1, "2025": 36.6}},
    sources=src("kosis_hh"), verified=True)

# --- N2-K3 홈케어 ---
add(id=f"{Q}-M-010", type="지표", indicator=f"{Q}-K3", importance=3, representative=True,
    statement="LG전자 가전 세척 서비스(베스트 케어)는 2025년 전년 대비 20% 성장했고, 2026년 1분기에도 전년 동기 대비 20% 이상 성장했다.",
    value=20, unit="% (전년 대비 성장)", as_of="2025", region="KR",
    definition="LG전자 관계자 발언 기준 서비스 성장률. 이용 건수·가구 비율은 공개되지 않음.",
    prev_value=None, sources=src("mk_care"), verified=True,
    check_flags=["확인 필요: 성장률의 기준(건수·매출)이 기사에 없고 회사 발언만 있음"])
add(id=f"{Q}-M-011", type="지표", indicator=f"{Q}-K3", importance=1, representative=False,
    statement="LG전자는 구독 가전을 방문 점검·분해 세척·소모품 교체하는 케어 매니저 약 4,000명을 운영한다.",
    value=4000, unit="명", as_of="2026-10", region="KR",
    definition="LG전자 구독 관리 인력 규모(언론 보도 기준). 공급 측 지표.",
    prev_value=None, sources=src("inews_sub"), verified=True)

# --- N2-K4 이사·입주 서비스 ---
add(id=f"{Q}-M-012", type="지표", indicator=f"{Q}-K4", importance=3, representative=True,
    statement="2025년 국내 이동자는 611만 8천 명으로 1년 전보다 2.6% 줄었다. 1974년 이후 가장 적다. 인구 100명당 이동자는 12.0명이다.",
    value=6117784, unit="명", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값(총전입). 이동률·최저 기록은 국가데이터처 발표 보도. 이사 서비스 수요의 모수.",
    prev_value=6283319, extra={"series": {"2021": 7213422, "2022": 6152155, "2023": 6128738, "2024": 6283319, "2025": 6117784}},
    sources=src("kosis_mig", "herald_mig"), verified=True)
add(id=f"{Q}-M-013", type="지표", indicator=f"{Q}-K4", importance=2, representative=False,
    statement="2026년 6월 이동자는 48만 1천 명으로 1년 전보다 0.6% 늘어 6월 기준 5년 만에 가장 많았다. 1~6월 누적 이동자는 전년 동기보다 2.1% 늘었다.",
    value=2.1, unit="% (1~6월 누적, 전년 동기 대비)", as_of="2026-06", region="KR",
    definition="국가데이터처 2026년 6월 국내인구이동통계 보도.",
    prev_value=None, sources=src("newsis_mig"), verified=True)
add(id=f"{Q}-M-014", type="지표", indicator=f"{Q}-K4", importance=2, representative=False,
    statement="2019년 12월 이사 경험자 1,000명 조사에서 완전포장이사 이용은 52.9%, 일반 이사는 27.6%였다. 40대 이상과 아파트 거주자에서 포장이사 비율이 높았다.",
    value=52.9, unit="%", as_of="2019-12", region="KR",
    definition="엠브레인 트렌드모니터 이사 관련 조사(이사 경험자 만 16~64세 1,000명, 2019-12-20~26). 분모는 이사 경험자이며 전체 가구가 아니다.",
    prev_value=None, sources=src("iboss_move"), verified=True,
    check_flags=["확인 필요: 2019년 조사로 오래됨. 게재일 미확인. 최근 포장이사·입주청소 이용률 공개 조사 미확보"])

# --- N2-K5 생활용품 정기배송 --- (가구 이용률 미확보: 이번 회차 기록 없음)

# --- N2-K6 반려동물 돌봄 서비스 ---
add(id=f"{Q}-M-015", type="지표", indicator=f"{Q}-K6", importance=3, representative=True,
    statement="2025년 최근 1년 반려동물 관련 서비스 이용 경험에서 미용업체 이용은 50.8%, 호텔 이용은 12.9%였다. 동물병원 이용은 95.1%였다.",
    value=50.8, unit="%", as_of="2025", region="KR",
    definition="농림축산식품부 2025 동물복지 국민의식조사(온라인 5,000명), 최근 1년 반려동물 관련 서비스 이용 경험. 분모는 반려동물 양육자로 보이나 기사에 명시 없음.",
    prev_value=51.8, extra={"series_grooming": {"2023": 51.8, "2025": 50.8}, "series_hotel": {"2023": 16.0, "2025": 12.9}},
    sources=src("newsseoul_pet", "tf_pet"), verified=True,
    check_flags=["확인 필요: 서비스 이용률의 분모(양육자 여부) 기사에 명시 없음. 개인 온라인 조사로 가구 방문조사(M-016)와 직접 비교 불가"])
add(id=f"{Q}-M-016", type="지표", indicator=f"{Q}-K6", importance=3, representative=False,
    statement="2025년 반려동물 양육 가구는 전체 가구의 29.2%였다. 첫 국가승인통계로 3,000가구를 방문 조사했다. 마리당 월평균 양육비는 약 12만 1천 원이다.",
    value=29.2, unit="%", as_of="2025", region="KR",
    definition="농림축산식품부 2025 반려동물 양육현황조사(인구주택총조사 표본 3,000가구 방문면접, 2025-10-31~12-12, 오차 ±1.79%p). 이전 조사와 방식이 달라 시계열 비교 불가. 수요 동인 기록.",
    prev_value=None, sources=src("khan_pet", "dailyvet_pet"), verified=True)
add(id=f"{Q}-M-017", type="지표", indicator=f"{Q}-K6", importance=2, representative=False,
    statement="2023년 조사에서 개·고양이 보호자의 1년 내 미용 이용은 51.8%, 호텔 16.0%, 유치원 10.6%였다.",
    value=16.0, unit="% (호텔)", as_of="2023-11", region="KR",
    definition="농림축산식품부 2023 동물복지 국민의식조사(20~64세 5,000명 온라인 패널, 2023-11-03~13), 복수응답.",
    prev_value=None, sources=src("dailyvet_pet23"), verified=True)
add(id=f"{Q}-M-018", type="지표", indicator=f"{Q}-K6", importance=1, representative=False,
    statement="KB경영연구소는 2024년 말 반려가구를 591만 가구, 전체 가구의 26.7%로 추산했다.",
    value=26.7, unit="%", as_of="2024-12", region="KR",
    definition="KB경영연구소 2025 한국 반려동물 보고서 추정치. 농식품부 방문조사(29.2%)와 방식이 다름.",
    prev_value=None, sources=src("kb_pet"), verified=True,
    check_flags=["확인 필요: 민간 추정치로 농식품부 국가승인통계(M-016)와 2.5%p 차이"])

# --- N2-K7 시니어 안전·돌봄 ---
add(id=f"{Q}-M-019", type="지표", indicator=f"{Q}-K7", importance=3, representative=True,
    statement="2024년 공공 응급안전안심서비스를 이용한 가구는 약 27만 가구였다. 정부는 2026년까지 약 30만 가구로 늘릴 계획이다.",
    value=27, unit="만 가구", as_of="2024", region="KR",
    definition="보건복지부 응급안전안심서비스(독거노인 등 대상 공공 서비스) 이용 가구, 언론 보도 기준. 민간 서비스가 아니다.",
    prev_value=None, sources=src("segye_emerg"), verified=True,
    check_flags=["확인 필요: 공공 서비스 값이라 지표 정의(민간 서비스)와 다름. 민간 시니어 안전·돌봄 이용률 미확보"])
add(id=f"{Q}-M-020", type="지표", indicator=f"{Q}-K7", importance=3, representative=False,
    statement="2025년 가구주가 65세 이상인 가구는 637만 가구로 일반가구의 28.3%였다. 1년 새 1.4%p 늘어 2020~2024년 연평균 증가폭(1.1%p)보다 빨랐다.",
    value=28.3, unit="%", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 인구총조사 가구주 연령 65세 이상 일반가구 ÷ 일반가구(DT_1JC1517 연령별 합산). 수요 동인 기록.",
    prev_value=26.9, extra={"series": {"2020": 22.6, "2021": 23.4, "2022": 24.5, "2023": 25.6, "2024": 26.9, "2025": 28.3}},
    sources=src("kosis_hh"), verified=True)
add(id=f"{Q}-M-021", type="지표", indicator=f"{Q}-K7", importance=2, representative=False,
    statement="2025년 65세 이상 1인가구는 246만 가구였다. 2020년 166만 가구에서 5년간 80만 가구 늘었다.",
    value=2455947, unit="가구", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 인구총조사 1인가구 중 가구주 65세 이상(DT_1JC1517 연령별 합산).",
    prev_value=2288807, extra={"series": {"2020": 1660711, "2021": 1824434, "2022": 1973416, "2023": 2138107, "2024": 2288807, "2025": 2455947}},
    sources=src("kosis_hh"), verified=True)

# --- N2-K8 스마트홈 ---
add(id=f"{Q}-M-022", type="지표", indicator=f"{Q}-K8", importance=3, representative=True,
    statement="2025년 인터넷이용실태조사에서 주거 편의(가사 지원 로봇·IoT 가전 등) 분야 AI 서비스 경험은 35.9%로 분야 중 가장 높았다.",
    value=35.9, unit="%", as_of="2025", region="KR",
    definition="과학기술정보통신부 2025 인터넷이용실태조사(22,671가구, 가구원 50,750명). 개인 응답 기준 경험률이며 분모가 전체 응답자인지 AI 경험자인지 기사에 없음.",
    prev_value=None, sources=src("mt_msit"), verified=True,
    check_flags=["확인 필요: 분모 미명시. 스마트홈 기기 이용 가구 비율이 아니라 AI 서비스 경험 분야 응답임"])
add(id=f"{Q}-M-023", type="지표", indicator=f"{Q}-K8", importance=2, representative=False,
    statement="2025년 국민의 67.0%가 AI 서비스를 경험했다. 생성형 AI 경험은 44.5%로 1년 전보다 11.2%p 늘었다.",
    value=67.0, unit="%", as_of="2025", region="KR",
    definition="과학기술정보통신부 2025 인터넷이용실태조사 보도자료. 스마트홈 기기 이용의 배경 지표.",
    prev_value=None, sources=src("kdi_msit"), verified=True)

# ======================================================================
# 사건 (E) — 최근 12개월
# ======================================================================
add(id=f"{Q}-E-001", type="사건", importance=3, date="2026-09-28", actor="삼성전자",
    statement="삼성전자가 가전 구독을 'AI 구독'으로 개편했다. 신혼부부용 '신혼 패스'와 고령층용 '이지케어 패스' 등 생애 단계별 관리 상품을 내놨다.",
    sources=src("inews_sub"), verified=True)
add(id=f"{Q}-E-002", type="사건", importance=3, date="2026-01-30", actor="LG전자",
    statement="LG전자가 2025년 가전 구독 매출이 2조 원을 넘었다고 밝혔다. 대형 가전 구독 확대와 아시아 시장 진출을 성장 요인으로 들었다.",
    sources=src("newdaily_lg"), verified=True)
add(id=f"{Q}-E-003", type="사건", importance=3, date="2026-01-08", actor="보건복지부",
    statement="보건복지부가 의료·요양 등 지역 돌봄 통합지원(통합돌봄)을 2026년 3월 27일부터 전국 229개 시·군·구에서 시행한다고 밝혔다. 2026년 예산은 914억 원이다.",
    sources=src("sbs_care"), verified=True,
    check_flags=["확인 필요: 3월 27일 실제 시행 여부는 시행 이후 보도로 다시 확인"])
add(id=f"{Q}-E-004", type="사건", importance=2, date="2026-02-12", actor="농림축산식품부",
    statement="농림축산식품부가 반려동물 양육현황조사를 처음 국가승인통계로 발표했다. 양육 가구 비율은 29.2%였다.",
    sources=src("khan_pet", "dailyvet_pet"), verified=True)
add(id=f"{Q}-E-005", type="사건", importance=2, date="2026-03-31", actor="과학기술정보통신부",
    statement="과학기술정보통신부가 2025 인터넷이용실태조사를 발표했다. AI 서비스 경험률은 67.0%였다.",
    sources=src("kdi_msit", "mt_msit"), verified=True)
add(id=f"{Q}-E-006", type="사건", importance=2, date="2026-05-07", actor="코웨이",
    statement="코웨이가 2026년 1분기 렌탈 계정 1,173만 개와 분기 최대 영업이익을 발표했다. 국내 계정은 748만 개였다.",
    sources=src("herald_coway"), verified=True,
    check_flags=["확인 필요: 기사 게재는 5월 7일이나 기사 본문은 발표일을 8일로 적음"])
add(id=f"{Q}-E-007", type="사건", importance=1, date="2025-12-19", actor="한국소비자원",
    statement="한국소비자원이 2025 한국의 소비생활지표를 발표했다. 온라인 구독 서비스에 돈을 낸 응답자는 24.3%였고, 20대는 30.1%로 높았다.",
    sources=src("khan_kca"), verified=True)
add(id=f"{Q}-E-008", type="사건", importance=1, date="2026-07-29", actor="국가데이터처",
    statement="국가데이터처가 2026년 6월 이동자가 6월 기준 5년 만에 가장 많았다고 발표했다. 주택 매매 증가를 요인으로 들었다.",
    sources=src("newsis_mig"), verified=True)

# ======================================================================
# 해석 (I)
# ======================================================================
add(id=f"{Q}-I-001", type="해석", importance=3, target="가전 렌탈·구독", direction="강화",
    statement="렌탈·구독은 가장 앞선 Home & Living 서비스다. 정수기 같은 관리형 소형 가전은 성인 3명 중 1명이 쓰는 확산 단계로 보인다. 냉장고·세탁기 같은 대형 가전 구독은 성인 이용 11.1%로 아직 얼리어답터 단계다. 업체 매출과 계정은 두 자릿수로 늘고 있다.",
    basis=[f"{Q}-M-001", f"{Q}-M-002", f"{Q}-M-003", f"{Q}-M-004", f"{Q}-E-002"])
add(id=f"{Q}-I-002", type="해석", importance=3, target="가사·청소 외주화", direction="중립",
    statement="가사 외주를 늘릴 생활 변화는 커지고 있다. 맞벌이 48.6%, 1인가구 36.6%다. 그러나 전체 가구의 가사서비스 지출은 2025년 줄었다. 카드 결제는 늘어 신호가 엇갈린다. 가구 이용률을 직접 재는 통계는 없다.",
    basis=[f"{Q}-M-006", f"{Q}-M-007", f"{Q}-M-008", f"{Q}-M-009"])
add(id=f"{Q}-I-003", type="해석", importance=3, target="고령 가구 안전·돌봄", direction="강화",
    statement="수요 동인 중 가장 빠르게 커지는 것은 고령 가구다. 65세 이상 가구주 가구 비중은 2025년 1.4%p 늘어 증가가 빨라졌다. 다만 2026년 3월 27일 통합돌봄 전국 시행 일정이 잡혀 공공이 먼저 공급을 넓히고 있다. 민간 안전·돌봄 서비스 이용은 수치로 확인되지 않는다.",
    basis=[f"{Q}-M-020", f"{Q}-M-021", f"{Q}-M-019", f"{Q}-E-003"])
add(id=f"{Q}-I-004", type="해석", importance=2, target="반려동물 서비스", direction="중립",
    statement="반려동물 양육 가구는 전체의 29.2%로 큰 수요층이다. 양육자 기준 미용 이용은 절반 수준에서 유지된다. 호텔 이용은 2023년 16.0%에서 2025년 12.9%로 낮아졌다. 돌봄 위탁은 아직 얼리어답터 단계다.",
    basis=[f"{Q}-M-015", f"{Q}-M-016", f"{Q}-M-017"])
add(id=f"{Q}-I-005", type="해석", importance=2, target="이사 연계 서비스", direction="약화",
    statement="이사 가구 안에서 포장이사는 2019년에 이미 과반이었다. 그러나 국내 이동자는 2025년 1974년 이후 최저다. 이사에 묶인 서비스는 전체 수요가 줄고 있다. 2026년 상반기에는 이동이 2.1% 늘어 반등 여부를 지켜봐야 한다.",
    basis=[f"{Q}-M-012", f"{Q}-M-013", f"{Q}-M-014"])
add(id=f"{Q}-I-006", type="해석", importance=2, target="스마트홈·AI 주거 편의", direction="강화",
    statement="AI 서비스 경험은 국민의 67.0%까지 넓어졌다. 그중 주거 편의 분야 경험이 35.9%로 가장 높다. 스마트홈 기기를 쓰는 가구 비율은 공식 통계로 확인되지 않는다.",
    basis=[f"{Q}-M-022", f"{Q}-M-023", f"{Q}-E-005"])
add(id=f"{Q}-I-007", type="해석", importance=2, target="생애 단계별 서비스 묶음", direction="강화",
    statement="가전 기업이 판매보다 관리 서비스로 경쟁한다. 삼성전자는 신혼부부와 고령층용 관리 상품을 따로 냈다. LG전자는 방문 관리 인력 약 4,000명을 운영한다. 가전 구독 결제는 40~50대, 가사도우미 결제는 30~40대 비중이 크다.",
    basis=[f"{Q}-E-001", f"{Q}-M-011", f"{Q}-M-005", f"{Q}-M-007"])

# ======================================================================
# 세부 전망 (F)
# ======================================================================
add(id=f"{Q}-F-001", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 국내 이동자 수는 2025년(611만 8천 명)보다 많을 것이다.",
    due="2027-01-31", condition="없음",
    method="국가데이터처 2026년 연간 국내인구이동통계(2027년 1월 발표)의 이동자 수 확인",
    basis=[f"{Q}-M-012", f"{Q}-M-013"])
add(id=f"{Q}-F-002", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="LG전자의 2026년 연간 가전 구독 매출은 3조 원 이상일 것이다.",
    due="2027-02-28", condition="없음",
    method="LG전자 2026년 연간 실적 발표 또는 이를 인용한 주요 언론 보도에서 구독 매출 확인",
    basis=[f"{Q}-M-004", f"{Q}-E-002"])
add(id=f"{Q}-F-003", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="코웨이의 2026년 말 국내 렌탈 계정은 760만 개 이상일 것이다.",
    due="2027-03-31", condition="없음",
    method="코웨이 2026년 4분기 실적 자료의 국내 렌탈 계정 수 확인",
    basis=[f"{Q}-M-003"])
add(id=f"{Q}-F-004", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2026년 전체 가구의 월평균 가사서비스 지출은 2025년(10,103원)보다 많을 것이다.",
    due="2027-03-31", condition="가계동향조사 분류가 바뀌지 않는다",
    method="KOSIS DT_1L9U101 가계동향조사 2026년 연간 전체가구 가사서비스 지출 확인",
    basis=[f"{Q}-M-006", f"{Q}-M-008"])
add(id=f"{Q}-F-005", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 반려동물 양육 가구 비율은 29% 이상을 유지할 것이다.",
    due="2027-03-31", condition="농식품부가 같은 방문조사 방식으로 2026년 조사를 발표한다",
    method="농림축산식품부 2026 반려동물 양육현황조사 발표값 확인",
    basis=[f"{Q}-M-016"])
add(id=f"{Q}-F-006", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026 인터넷이용실태조사의 AI 서비스 경험률은 2025년(67.0%)보다 높을 것이다.",
    due="2027-04-30", condition="조사 문항이 유지된다",
    method="과학기술정보통신부 2026 인터넷이용실태조사 발표값 확인",
    basis=[f"{Q}-M-023", f"{Q}-M-022"])

# ======================================================================
# 메인 질문 시나리오
# ======================================================================
add(id=f"{Q}-F-101", type="전망", importance=3, forecast_status="진행 중", scenario="낙관", result=None,
    statement="2027년 말까지 관리형 가전 구독이 대형 가전으로 넓어지고, 가사·홈케어 서비스 지출도 다시 늘어 새 수요가 한 단계씩 올라선다.",
    milestones=[{"by": "2027-02", "text": "LG전자 2026년 구독 매출 3조 원 이상, 코웨이 국내 계정 760만 개 이상"},
                {"by": "2027-03", "text": "2026년 가계동향 가사서비스 지출이 2025년보다 증가"},
                {"by": "2027-12", "text": "대형 가전 구독 이용 성인 15% 이상을 보여 주는 이용 조사 공표"}],
    due="2027-12-31", condition="가전 구독 해지·약관 규제가 크게 강화되지 않는다",
    method="세 가지 중 두 가지 이상 충족 시 적중: (1) N2-F-002와 N2-F-003 모두 적중 (2) N2-F-004 적중 (3) 2027년 안에 공표된 이용 조사에서 대형 가전 구독 현재 이용률 15% 이상",
    basis=[f"{Q}-M-001", f"{Q}-M-004", f"{Q}-M-006", f"{Q}-M-003"],
    signposts=[{"id": f"{Q}-F-002", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-003", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-004", "on_hit": "낙관", "on_miss": "비관"}])
add(id=f"{Q}-F-102", type="전망", importance=3, forecast_status="진행 중", scenario="비관", result=None,
    statement="2027년 말까지 렌탈·구독은 정수기 같은 기존 품목에 머물고, 가사·홈케어 서비스는 지출이 늘지 않아 단계가 그대로다.",
    milestones=[{"by": "2027-02", "text": "LG전자 구독 매출 증가율이 10%대 이하로 둔화"},
                {"by": "2027-03", "text": "2026년 가계동향 가사서비스 지출이 2025년 수준 이하"},
                {"by": "2027-12", "text": "대형 가전 구독 이용률 15% 이상 조사 없음"}],
    due="2027-12-31", condition="없음",
    method="낙관 조건 중 하나 이하 충족 시 적중",
    basis=[f"{Q}-M-001", f"{Q}-M-006", f"{Q}-M-012"],
    signposts=[{"id": f"{Q}-F-002", "on_miss": "비관"}, {"id": f"{Q}-F-003", "on_miss": "비관"},
               {"id": f"{Q}-F-004", "on_miss": "비관"}])

# ---------- 공통 마무리: patches.jsonl 적용 → 검증 → records.jsonl ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from validate import finish
finish(records, Path(__file__).parent)
