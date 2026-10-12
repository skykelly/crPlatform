"""H1 R1 4유형 기록 생성 + 규칙 검증. 출력: 같은 폴더 records.jsonl
실행: python3 build_records.py  (검증 오류가 있으면 exit 1)
"""
import sys
from pathlib import Path

Q, R = "H1", "R1"
# 출처 사전: key → url·publisher·date·grade (A 공식 1차 / B 언론·연구기관 / C 출처 불명)
SRC = {
    # 팩트베이스 (KOSIS 공식 API 수집값)
    "kosis_h01": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1JU1501&conn_path=I2",
                  "publisher": "국가데이터처 KOSIS (DT_1JU1501 주택의 종류별 주택)", "date": "2026-10-10", "grade": "A"},
    "kosis_h02": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1JC1521&conn_path=I2",
                  "publisher": "국가데이터처 KOSIS (DT_1JC1521 주택(오피스텔 포함)의 종류 및 주거면적별 가구)", "date": "2026-10-10", "grade": "A"},
    "kosis_h03_2020": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1PE2002&conn_path=I2",
                       "publisher": "국가데이터처 KOSIS (DT_1PE2002 거처의 종류별/점유형태별 가구, 2020)", "date": "2026-10-11", "grade": "A"},
    "kosis_h03_2015": {"url": "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1PE1502&conn_path=I2",
                       "publisher": "국가데이터처 KOSIS (DT_1PE1502 거처의 종류별/점유형태별 가구, 2015)", "date": "2026-10-11", "grade": "A"},
    # 국가데이터처 보도자료 게시본 (KDI 경제교육·정보센터)
    "kdi_census2025": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=284799",
                       "publisher": "국가데이터처 보도자료 '2025년 인구주택총조사 결과(등록센서스 방식)' (KDI 경제교육·정보센터 게시)", "date": "2026-07-28", "grade": "A"},
    "kdi_centenarian": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=285573",
                        "publisher": "국가데이터처 보도자료 '2025 인구주택총조사 100세 이상 고령자조사 집계 결과' (KDI 경제교육·정보센터 게시)", "date": "2026-08-20", "grade": "A"},
    # 주거실태조사 (국토교통부) 보도
    "newsis_hs2024": {"url": "https://www.newsis.com/view/NISX20251116_0003404516",
                      "publisher": "뉴시스 (국토교통부 2024년도 주거실태조사 인용)", "date": "2025-11-16", "grade": "B"},
    "newdaily_hs2024": {"url": "https://biz.newdaily.co.kr/site/data/html/2025/11/15/2025111500090.html",
                        "publisher": "뉴데일리 (국토교통부 2024년도 주거실태조사 인용)", "date": "2025-11-15", "grade": "B"},
    "hankyung_hs2024": {"url": "https://www.hankyung.com/article/202511218252i",
                        "publisher": "한국경제 (국토교통부 2024년도 주거실태조사 인용)", "date": "2025-11-21", "grade": "B"},
    "newsis_hs2023": {"url": "https://www.newsis.com/view/NISX20241226_0003011167",
                      "publisher": "뉴시스 (국토교통부 2023년도 주거실태조사 인용)", "date": "2024-12-26", "grade": "B"},
    "newsseoul_hs2022": {"url": "https://newsseoul.co.kr/news/view/1065573013228184",
                         "publisher": "뉴스서울 (국토교통부 2022년도 주거실태조사 인용)", "date": "2023-12-22", "grade": "B"},
    "seoul_hs2021": {"url": "https://m.seoul.co.kr/news/2022/12/21/20221221500081",
                     "publisher": "서울신문 (국토교통부 2021년도 주거실태조사 인용)", "date": "2022-12-21", "grade": "B"},
    # 2025 인구주택총조사 보도
    "newsis_census2025": {"url": "https://www.newsis.com/view/NISX20260728_0003726109",
                          "publisher": "뉴시스 (국가데이터처 2025 인구주택총조사 인용)", "date": "2026-07-28", "grade": "B"},
    "news1_census2025": {"url": "https://www.news1.kr/amp/economy/trend/6241227",
                         "publisher": "뉴스1 (국가데이터처 2025 인구주택총조사 인용)", "date": "2026-07-28", "grade": "B"},
    "fnnews_census2025": {"url": "https://www.fnnews.com/news/202607281048203456",
                          "publisher": "파이낸셜뉴스 (국가데이터처 2025 인구주택총조사 인용)", "date": "2026-07-28", "grade": "B"},
    "herald_census2025": {"url": "https://www.heraldk.com/article/2026072722090410402",
                          "publisher": "헤럴드경제 (국가데이터처 2025 인구주택총조사 가구 부문 인용)", "date": "2026-07-27", "grade": "B"},
    # 통계로 보는 1인가구
    "newsis_1p2025": {"url": "https://www.newsis.com/view/NISX20251209_0003433761",
                      "publisher": "뉴시스 (국가데이터처 2025 통계로 보는 1인 가구 인용)", "date": "2025-12-09", "grade": "B"},
    "newdaily_1p2025": {"url": "https://biz.newdaily.co.kr/site/data/html/2025/12/09/2025120900222.amp.html",
                        "publisher": "뉴데일리 (국가데이터처 2025 통계로 보는 1인 가구 인용)", "date": "2025-12-09", "grade": "B"},
    # 주택 재고 면적 구간 (2020 인구주택총조사)
    "bizhankook_size": {"url": "https://www.bizhankook.com/bk/article/24150",
                        "publisher": "비즈한국 (2020 인구주택총조사 주택 연면적 구간 인용)", "date": "2022-07-27", "grade": "B"},
}
def src(*keys): return [dict(SRC[k], key=k) for k in keys]

HS = ("newsis_hs2024", "newdaily_hs2024")          # 2024년도 주거실태조사
HS_SERIES = HS + ("newsis_hs2023", "newsseoul_hs2022", "seoul_hs2021")
CEN = ("news1_census2025", "newsis_census2025", "fnnews_census2025")

base = dict(question=Q, question_version="v1.0", first_seen=R, last_seen=R, status="유효", replaces=None, check_flags=[])
records = []
def add(**kw):
    r = dict(base); r.update(kw); records.append(r)

# =====================================================================================
# 지표 (M)
# =====================================================================================
# ---- K1 점유 형태 ----
add(id=f"{Q}-M-001", type="지표", indicator=f"{Q}-K1", importance=3, representative=True,
    statement="2024년 자가점유율은 58.4%로 1년 전보다 1.0%p 올랐다. 2020~2023년에는 57.3~57.9% 사이에 머물렀다. 임차 가구는 38.0%, 무상 거주는 3.6%다.",
    value=58.4, unit="%", as_of="2024", region="KR",
    definition="국토교통부 주거실태조사(표본 약 6.1만 가구), 자기 집에 사는 가구 비율. 자가보유율(집을 가진 가구)은 61.4%로 별도.",
    prev_value=57.4, extra={"series": {"2020": 57.9, "2021": 57.3, "2022": 57.5, "2023": 57.4, "2024": 58.4},
                            "임차_2024": 38.0, "무상_2024": 3.6, "수도권_자가점유_2024": 52.7, "자가보유율_2024": 61.4},
    sources=src(*HS_SERIES), verified=True,
    check_flags=["확인 필요: 국토교통부 보도자료 원문(molit.go.kr)이 열리지 않아 언론 보도 수치로 확인. 전세·월세 구분값은 보도에 없음"])

add(id=f"{Q}-M-002", type="지표", indicator=f"{Q}-K1", importance=2,
    statement="2020년 인구주택총조사에서 일반가구의 57.3%가 자기 집, 15.5%가 전세, 23.4%가 월세(보증부·무보증·사글세 합)에 살았다. 2015년은 자기 집 56.8%, 전세 15.5%, 월세 23.7%였다.",
    value=57.3, unit="%", as_of="2020", region="KR",
    definition="팩트베이스(KOSIS API) 값. 표 이름·항목 확인함(거처의 종류별/점유형태별 가구, 일반가구). 비율 = 점유형태별 가구 ÷ 일반가구(2020년 20,926,710가구). 5년 주기 표본 집계.",
    prev_value=56.8, extra={"series_자가": {"2015": 56.8, "2020": 57.3}, "series_전세": {"2015": 15.5, "2020": 15.5},
                            "series_월세": {"2015": 23.7, "2020": 23.4}, "series_무상": {"2015": 4.0, "2020": 3.7}},
    sources=src("kosis_h03_2020", "kosis_h03_2015"), verified=True)

add(id=f"{Q}-M-003", type="지표", indicator=f"{Q}-K1", importance=3,
    statement="2024년 청년 가구의 자가점유율은 12.2%로 1년 전보다 2.4%p 내렸다. 같은 해 전체 자가점유율은 1.0%p 올랐다.",
    value=12.2, unit="%", as_of="2024", region="KR",
    definition="주거실태조사 청년 가구(가구주 만 19~34세) 자가점유율.",
    prev_value=14.6, extra={"series": {"2023": 14.6, "2024": 12.2}, "주택_외_거처_2024": 17.9},
    sources=src(*HS), verified=True,
    check_flags=["확인 필요: 2023년 14.6%는 '2.4%p 하락'에서 역산한 값", "확인 필요: 청년 임차 비율이 보도에 '826%'로 표기돼 82.6%로 추정되나 원문 미확인"])

add(id=f"{Q}-M-004", type="지표", indicator=f"{Q}-K1", importance=3,
    statement="2024년 신혼부부 가구의 자가점유율은 43.9%로 1년 전보다 2.5%p 내렸다. 2021년에도 43.9%였다.",
    value=43.9, unit="%", as_of="2024", region="KR",
    definition="주거실태조사 신혼부부 가구(혼인 7년 이하) 자가점유율.",
    prev_value=46.4, extra={"series": {"2021": 43.9, "2022": 43.6, "2023": 46.4, "2024": 43.9}},
    sources=src("newsis_hs2024", "newsseoul_hs2022", "seoul_hs2021"), verified=True,
    check_flags=["확인 필요: 2023년 46.4%는 '2.5%p 하락'에서 역산한 값. 2022년 43.6%는 보도의 '자가 비율' 표현으로 자가점유율과 정의가 같은지 원문 확인 필요"])

# ---- K2 소득 대비 임대료 비율(RIR) ----
add(id=f"{Q}-M-005", type="지표", indicator=f"{Q}-K2", importance=3, representative=True,
    statement="2024년 임차 가구의 소득 대비 임대료 비율(RIR, 중위수)은 15.8%로 2023년과 같았다. 2020년 16.6%에서 내려온 뒤 15.7~16.0%에 머문다. 수도권은 18.4%다.",
    value=15.8, unit="%", as_of="2024", region="KR",
    definition="주거실태조사, 임차 가구의 월 소득 대비 월 임대료 비율 중위수. 전세는 월세로 환산.",
    prev_value=15.8, extra={"series": {"2020": 16.6, "2021": 15.7, "2022": 16.0, "2023": 15.8, "2024": 15.8},
                            "수도권_series": {"2020": 18.6, "2021": 17.8, "2022": 18.3, "2023": 20.3, "2024": 18.4}},
    sources=src(*HS_SERIES), verified=True,
    check_flags=["확인 필요: 국토교통부 보도자료 원문(molit.go.kr)이 열리지 않아 언론 보도 수치로 확인. 2023년 수도권 RIR 20.3%는 보도 간 서술이 달라 원문 대조 필요"])

add(id=f"{Q}-M-006", type="지표", indicator=f"{Q}-K2", importance=3,
    statement="2024년 고령 임차 가구의 소득 대비 임대료 비율(RIR)은 25.4%다. 2022년 30.6%보다 낮지만 전체 가구(15.8%)보다 9.6%p 높다.",
    value=25.4, unit="%", as_of="2024", region="KR",
    definition="주거실태조사 고령 가구(가구주 65세 이상) 임차 가구 RIR.",
    prev_value=30.6, extra={"series": {"2021": 29.4, "2022": 30.6, "2024": 25.4}},
    sources=src("newsis_hs2024", "newsseoul_hs2022"), verified=True)

add(id=f"{Q}-M-007", type="지표", indicator=f"{Q}-K2", importance=2,
    statement="2024년 청년 임차 가구의 소득 대비 임대료 비율(RIR)은 16.0%로 1년 전보다 1.4%p 내렸다.",
    value=16.0, unit="%", as_of="2024", region="KR",
    definition="주거실태조사 청년 가구 임차 가구 RIR.",
    prev_value=17.4, extra={"series": {"2021": 16.8, "2022": 17.4, "2023": 17.4, "2024": 16.0}},
    sources=src("newsis_hs2024", "newsseoul_hs2022"), verified=True,
    check_flags=["확인 필요: 2023년 17.4%는 '1.4%p 하락'에서 역산한 값"])

# ---- K8 소득 대비 주택가격 배수(PIR) ----
add(id=f"{Q}-M-008", type="지표", indicator=f"{Q}-K8", importance=3, representative=True,
    statement="2024년 자가 가구의 소득 대비 주택가격 배수(PIR, 중위수)는 6.3배로 3년째 같다. 2020년 5.5배에서 2021년 6.7배로 뛴 뒤 내려왔다. 수도권은 8.7배로 1년 전 8.5배보다 올랐다.",
    value=6.3, unit="배", as_of="2024", region="KR",
    definition="주거실태조사, 자가 가구의 연소득 대비 현재 주택가격 배수 중위수. 명목 비율(분자·분모 모두 명목이라 물가 보정 불필요).",
    prev_value=6.3, extra={"series": {"2020": 5.5, "2021": 6.7, "2022": 6.3, "2023": 6.3, "2024": 6.3},
                           "수도권_series": {"2020": 8.0, "2021": 10.1, "2022": 9.3, "2023": 8.5, "2024": 8.7}},
    sources=src(*HS_SERIES), verified=True)

add(id=f"{Q}-M-009", type="지표", indicator=f"{Q}-K8", importance=2,
    statement="2024년 PIR은 고령 자가 가구 9.1배, 청년 6.0배, 신혼부부 6.0배다. 고령 가구는 2022년 10.6배에서 내려왔다.",
    value=9.1, unit="배", as_of="2024", region="KR",
    definition="주거실태조사 생애단계별 자가 가구 PIR 중위수. 대표값은 고령 가구.",
    prev_value=9.2, extra={"고령_series": {"2021": 9.5, "2022": 10.6, "2023": 9.2, "2024": 9.1},
                           "청년_series": {"2021": 6.4, "2022": 6.7, "2023": 6.0, "2024": 6.0},
                           "신혼_series": {"2021": 6.9, "2022": 6.5, "2023": 5.9, "2024": 6.0}},
    sources=src("newsis_hs2024", "newdaily_hs2024", "newsseoul_hs2022", "seoul_hs2021"), verified=True)

add(id=f"{Q}-M-010", type="지표", indicator=f"{Q}-K8", importance=2,
    statement="가구주가 된 뒤 첫 집을 마련하기까지 걸린 기간은 2024년 7.9년이다. 2022년 7.4년, 2023년 7.7년에서 늘었다.",
    value=7.9, unit="년", as_of="2024", region="KR",
    definition="주거실태조사 생애최초 주택 마련 소요연수(가구주 된 시점부터).",
    prev_value=7.7, extra={"series": {"2019": 6.9, "2020": 7.7, "2021": 7.7, "2022": 7.4, "2023": 7.7, "2024": 7.9}, "수도권_2024": 8.7},
    sources=src("newsis_hs2024", "hankyung_hs2024", "newsis_hs2023", "seoul_hs2021"), verified=True)

# ---- K4 1인당 주거면적·최저주거기준 미달 ----
add(id=f"{Q}-M-011", type="지표", indicator=f"{Q}-K4", importance=3, representative=True,
    statement="2025년 등록센서스 기준 1인당 주거면적은 32.4㎡로 1년 새 0.5㎡ 늘었다. 2020년 29.7㎡에서 해마다 0.5~0.6㎡씩 늘었다.",
    value=32.4, unit="㎡", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 주택·오피스텔 거주 일반가구의 주거면적 합 ÷ 가구원. 주거실태조사 1인당 면적(2024년 36.0㎡)과 조사 방식이 달라 값이 다르다.",
    prev_value=31.9, extra={"series": {"2015": 26.9, "2020": 29.7, "2021": 30.3, "2022": 30.9, "2023": 31.4, "2024": 31.9, "2025": 32.4}},
    sources=src("kosis_h02"), verified=True)

add(id=f"{Q}-M-012", type="지표", indicator=f"{Q}-K4", importance=2,
    statement="주거실태조사의 1인당 주거면적은 2024년 36.0㎡로 2023년과 같았다. 가구당 주거면적은 68.1㎡로 0.8㎡ 줄었다.",
    value=36.0, unit="㎡", as_of="2024", region="KR",
    definition="국토교통부 주거실태조사 1인당 주거면적 평균.",
    prev_value=36.0, extra={"series": {"2020": 33.9, "2021": 33.9, "2022": 34.8, "2023": 36.0, "2024": 36.0}, "가구당_2024": 68.1, "가구당_2023": 68.9},
    sources=src(*HS_SERIES), verified=True)

add(id=f"{Q}-M-013", type="지표", indicator=f"{Q}-K4", importance=3,
    statement="2024년 신혼부부 가구의 1인당 주거면적은 27.4㎡로 1년 전 27.8㎡보다 줄었다. 생애단계 중 가장 좁다.",
    value=27.4, unit="㎡", as_of="2024", region="KR",
    definition="주거실태조사 신혼부부 가구 1인당 주거면적.",
    prev_value=27.8, extra={"series": {"2022": 26.6, "2023": 27.8, "2024": 27.4}},
    sources=src("newdaily_hs2024", "newsseoul_hs2022"), verified=True)

add(id=f"{Q}-M-014", type="지표", indicator=f"{Q}-K4", importance=3,
    statement="2024년 고령 가구의 1인당 주거면적은 46.6㎡로 전체 가구(36.0㎡)보다 10.6㎡ 넓다. 2022년 45.7㎡에서 늘었다.",
    value=46.6, unit="㎡", as_of="2024", region="KR",
    definition="주거실태조사 고령 가구(가구주 65세 이상) 1인당 주거면적.",
    prev_value=45.7, extra={"series": {"2022": 45.7, "2024": 46.6}},
    sources=src("newdaily_hs2024", "newsseoul_hs2022"), verified=True)

add(id=f"{Q}-M-015", type="지표", indicator=f"{Q}-K4", importance=2,
    statement="2024년 청년 가구의 1인당 주거면적은 31.1㎡다. 2022년 30.4㎡보다 조금 넓다.",
    value=31.1, unit="㎡", as_of="2024", region="KR",
    definition="주거실태조사 청년 가구 1인당 주거면적.",
    prev_value=30.4, extra={"series": {"2022": 30.4, "2024": 31.1}},
    sources=src("newdaily_hs2024", "newsseoul_hs2022"), verified=True)

add(id=f"{Q}-M-016", type="지표", indicator=f"{Q}-K4", importance=3,
    statement="2024년 최저주거기준에 못 미치는 가구는 3.8%로 1년 전보다 0.2%p 늘었다. 2020년 4.6%에서 2023년 3.6%까지 줄던 흐름이 멈췄다.",
    value=3.8, unit="%", as_of="2024", region="KR",
    definition="주거실태조사, 면적·방 수·필수설비 중 하나라도 최저주거기준에 못 미치는 가구 비율.",
    prev_value=3.6, extra={"series": {"2020": 4.6, "2021": 4.5, "2022": 3.9, "2023": 3.6, "2024": 3.8}},
    sources=src("newdaily_hs2024", "newsis_hs2023", "newsseoul_hs2022", "seoul_hs2021"), verified=True)

add(id=f"{Q}-M-017", type="지표", indicator=f"{Q}-K4", importance=3,
    statement="2024년 청년 가구의 최저주거기준 미달 비율은 8.2%로 1년 새 2.1%p 늘었다. 신혼부부는 2.5%, 고령 가구는 2.1%다.",
    value=8.2, unit="%", as_of="2024", region="KR",
    definition="주거실태조사 청년 가구 최저주거기준 미달 비율. 신혼부부·고령 가구 값 병기.",
    prev_value=6.1, extra={"청년_series": {"2022": 8.0, "2023": 6.1, "2024": 8.2},
                           "신혼_series": {"2022": 1.9, "2023": 1.8, "2024": 2.5},
                           "고령_series": {"2022": 2.8, "2023": 2.5, "2024": 2.1}},
    sources=src("newdaily_hs2024", "newsis_hs2024", "newsseoul_hs2022"), verified=True,
    check_flags=["확인 필요: 2023년 청년 6.1%, 신혼 1.8%는 보도의 증감폭에서 역산한 값"])

# ---- K3 주거면적 구간별 가구 ----
add(id=f"{Q}-M-018", type="지표", indicator=f"{Q}-K3", importance=3, representative=True,
    statement="2024년 1인가구의 74.2%가 전용 60㎡ 이하에 산다. 40㎡ 이하만 49.6%다. 60~85㎡는 18.0%, 85㎡ 초과는 7.6%다.",
    value=74.2, unit="%", as_of="2024", region="KR",
    definition="국가데이터처 '2025 통계로 보는 1인 가구'의 1인가구 주거면적 구간(40㎡ 이하 49.6, 40~50 13.0, 50~60 11.6, 60~85 18.0, 85~102 3.9, 102~135 3.2, 135 초과 0.5). 60㎡ 이하·85㎡ 초과는 구간 합산.",
    prev_value=None, extra={"bands": {"40이하": 49.6, "40-50": 13.0, "50-60": 11.6, "60-85": 18.0, "85-102": 3.9, "102-135": 3.2, "135초과": 0.5},
                            "size_lens": {"소형": 74.2, "중형": 18.0, "대형": 7.6}},
    sources=src("newsis_1p2025"), verified=True,
    check_flags=["확인 필요: 1인가구만의 분포. 전체 일반가구의 면적 구간 분포는 KOSIS 원표(인구총조사 주거면적별 가구)를 열지 못해 비교값 없음"])

add(id=f"{Q}-M-019", type="지표", indicator=f"{Q}-K3", importance=2,
    statement="2025년 주택·오피스텔에 사는 일반가구의 가구당 주거면적은 70.5㎡다. 2019년 70.4㎡ 이후 70㎡ 안팎에 머문다. 같은 기간 가구원 수는 줄었다.",
    value=70.5, unit="㎡", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. DT_1JC1521의 '가구당 주거면적' 항목. 이 표는 면적 구간별 가구 수가 아니라 평균 면적만 담고 있다.",
    prev_value=70.3, extra={"series": {"2015": 68.4, "2019": 70.4, "2020": 70.1, "2021": 69.9, "2022": 69.9, "2023": 70.0, "2024": 70.3, "2025": 70.5},
                            "가구원_series": {"2020": 48299924, "2025": 47870977}, "일반가구_series": {"2020": 20464080, "2025": 21990449}},
    sources=src("kosis_h02"), verified=True,
    check_flags=["확인 필요: 팩트베이스 H02 매핑 불일치. 지표 정의는 '면적 구간별 가구 비중'이나 표(DT_1JC1521)에는 가구 수·가구원·가구당 면적·1인당 면적 4개 항목만 있다"])

add(id=f"{Q}-M-020", type="지표", indicator=f"{Q}-K3", importance=2,
    statement="2025년 주택 재고의 주거용 연면적은 40㎡ 이하 12.9%, 40~60㎡ 28.2%, 60~100㎡ 43.1%다. 60㎡ 이하는 41.1%다. 2020년에는 60㎡ 이하가 약 42%, 60~85㎡가 37%, 85㎡ 초과가 약 20%였다.",
    value=41.1, unit="%", as_of="2025", region="KR",
    definition="주택총조사 주거용 연면적 구간별 주택 비중(가구 기준이 아니라 주택 재고 기준). 60㎡ 이하는 구간 합산. 2025년 공표 구간은 100㎡를 경계로 써서 85㎡ 경계 값이 없다.",
    prev_value=42.0, extra={"bands_2025": {"40이하": 12.9, "40-60": 28.2, "60-100": 43.1, "100초과_차감": 15.8},
                            "bands_2020": {"20이하": 2, "20-40": 11, "40-60": 29, "60-85": 37, "85-100": 5, "100-130": 7, "130-165": 4, "165-230": 2, "230초과": 2}},
    sources=src("news1_census2025", "bizhankook_size"), verified=True,
    check_flags=["확인 필요: 주택 재고 기준이라 가구 분포와 다르다", "확인 필요: 2025년 85㎡ 경계 값 없음. 100㎡ 초과 15.8%는 차감 계산", "확인 필요: 2020년 구간값은 언론 재인용(정수 반올림)"])

# ---- K5 주택 종류별 비중 ----
add(id=f"{Q}-M-021", type="지표", indicator=f"{Q}-K5", importance=3, representative=True,
    statement="2025년 주택 2,018만 호 중 아파트는 65.8%다. 2020년 62.9%에서 해마다 0.5~0.7%p씩 늘었다. 단독주택은 19.0%, 연립·다세대는 14.1%다.",
    value=65.8, unit="%", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. 아파트 ÷ 주택_계(2025년 13,289,220 ÷ 20,181,352). 다가구주택은 1호로 셈.",
    prev_value=65.3, extra={"series": {"2015": 59.9, "2020": 62.9, "2021": 63.5, "2022": 64.0, "2023": 64.6, "2024": 65.3, "2025": 65.8},
                            "단독_series": {"2020": 21.0, "2025": 19.0}, "연립다세대_series": {"2020": 14.9, "2025": 14.1}},
    sources=src("kosis_h01"), verified=True)

add(id=f"{Q}-M-022", type="지표", indicator=f"{Q}-K5", importance=2,
    statement="2025년 오피스텔에 사는 일반가구는 86.9만 가구로 1년 새 2.4% 늘었다. 2015년 32.0만 가구의 2.7배다. 가구당 주거면적은 40.7㎡다.",
    value=868566, unit="가구", as_of="2025", region="KR",
    definition="팩트베이스(KOSIS API) 값. DT_1JC1521 오피스텔 거주 일반가구 수와 가구당 주거면적.",
    prev_value=848017, extra={"series": {"2015": 320194, "2020": 626691, "2024": 848017, "2025": 868566},
                              "가구당면적_series": {"2015": 43.7, "2020": 40.8, "2025": 40.7}},
    sources=src("kosis_h02"), verified=True)

add(id=f"{Q}-M-023", type="지표", indicator=f"{Q}-K5", importance=2,
    statement="2024년 1인가구는 단독주택 39.0%, 아파트 35.9%, 연립·다세대 11.7%, 주택 이외 거처 11.6%에 산다. 아파트 거주 비중이 전체 가구보다 18%p 낮다.",
    value=35.9, unit="%", as_of="2024", region="KR",
    definition="국가데이터처 '2025 통계로 보는 1인 가구'의 1인가구 거처 종류. 비교값 전체 가구 아파트 53.9%는 같은 보도의 값.",
    prev_value=None, extra={"단독": 39.0, "아파트": 35.9, "연립다세대": 11.7, "주택이외거처": 11.6, "전체가구_아파트": 53.9},
    sources=src("newsis_1p2025", "newdaily_1p2025"), verified=True)

add(id=f"{Q}-M-024", type="지표", indicator=f"{Q}-K5", importance=2,
    statement="2024년 신혼부부 가구의 73.4%가 아파트에 산다. 전체 가구는 53.1%다. 고령 가구는 39.2%가 단독주택에 산다.",
    value=73.4, unit="%", as_of="2024", region="KR",
    definition="주거실태조사 생애단계별 거주 주택 유형.",
    prev_value=None, extra={"신혼_아파트": 73.4, "전체_아파트": 53.1, "고령_단독": 39.2},
    sources=src("newsis_hs2024", "newdaily_hs2024"), verified=True)

# ---- K6 30년 이상 노후주택 ----
add(id=f"{Q}-M-025", type="지표", indicator=f"{Q}-K6", importance=3, representative=True,
    statement="2025년 지은 지 30년이 넘은 주택은 618만 호로 전체의 30.6%다. 처음으로 30%를 넘었다. 1년 전보다 2.6%p, 5년 전보다 11.2%p 높다. 단독주택은 60.3%, 아파트는 22.2%가 30년 이상이다.",
    value=30.6, unit="%", as_of="2025", region="KR",
    definition="주택총조사, 건축 후 30년 이상 주택 비중. 20년 이상은 56.0%.",
    prev_value=28.0, extra={"series": {"2020": 19.4, "2024": 28.0, "2025": 30.6}, "20년이상_2025": 56.0,
                            "종류별_2025": {"단독": 60.3, "아파트": 22.2, "연립다세대": 28.5, "비주거용건물내": 51.1}},
    sources=src(*CEN, "kdi_census2025"), verified=True,
    check_flags=["확인 필요: 2024년 28.0%, 2020년 19.4%는 보도의 증감폭에서 역산한 값. 팩트베이스 H04에 수집값 없음"])

# ---- K7 빈집(미거주 주택) ----
add(id=f"{Q}-M-026", type="지표", indicator=f"{Q}-K7", importance=3, representative=True,
    statement="2025년 사람이 살지 않는 주택은 172.2만 호로 전체의 8.5%다. 1년 새 12.2만 호(7.7%) 늘어 1995년 집계 이후 가장 많다. 5년 전보다 13.9% 늘어 같은 기간 주택 증가율 8.9%를 웃돈다.",
    value=1722000, unit="호", as_of="2025", region="KR",
    definition="주택총조사 미거주 주택. 기준일에 사람이 살지 않는 모든 주택으로, 장기 빈집뿐 아니라 입주 전 신축·매매·이사 중 일시 공실을 포함한다.",
    prev_value=1599000, extra={"series": {"2020": 1512000, "2024": 1599000, "2025": 1722000}, "share_series": {"2024": 8.0, "2025": 8.5},
                               "종류별_미거주율_2025": {"비주거용건물내": 14.9, "연립": 14.7, "다세대": 11.4, "단독": 10.3, "아파트": 7.1},
                               "1989년이전_미거주율": 16.7, "2025년준공_미거주율": 20.6},
    sources=src(*CEN, "kdi_census2025"), verified=True,
    check_flags=["확인 필요: 2020년 151.2만 호는 '5년 전 대비 21만 호 증가'에서 역산한 값. 2024년 값은 보도마다 159.9만·160.0만으로 다름", "확인 필요: 1년 이상 비어 있는 주택 수는 공표값 미확인"])

# =====================================================================================
# 사건 (E) — 최근 12개월
# =====================================================================================
add(id=f"{Q}-E-001", type="사건", importance=3, date="2025-11-16", actor="국토교통부",
    statement="국토교통부가 2024년도 주거실태조사 결과를 발표했다. 자가점유율 58.4%, 소득 대비 임대료 비율(RIR) 15.8%, 소득 대비 주택가격 배수(PIR) 6.3배, 최저주거기준 미달 3.8%다.",
    sources=src(*HS), verified=True)

add(id=f"{Q}-E-002", type="사건", importance=2, date="2025-12-09", actor="국가데이터처",
    statement="국가데이터처가 '2025 통계로 보는 1인 가구'를 발표했다. 2024년 1인가구는 804.5만 가구(36.1%)이고 주택 소유율은 32.0%다.",
    sources=src("newsis_1p2025", "newdaily_1p2025"), verified=True)

add(id=f"{Q}-E-003", type="사건", importance=3, date="2026-07-28", actor="국가데이터처",
    statement="국가데이터처가 2025년 인구주택총조사 주택 부문 결과를 발표했다. 주택이 처음으로 2,000만 호를 넘었고 30년 이상 주택 비중이 처음 30%를 넘었다. 미거주 주택은 172.2만 호로 집계 이후 가장 많다.",
    sources=src("kdi_census2025", *CEN), verified=True)

add(id=f"{Q}-E-004", type="사건", importance=3, date="2026-07-28", actor="국가데이터처",
    statement="같은 발표에서 2025년 1인가구는 824.4만 가구(일반가구의 36.6%), 2인가구는 29.4%로 1·2인가구가 66.1%다. 고령자 1인가구는 245.6만 가구로 1년 새 7.3% 늘었다. 4인 이상 가구는 340.8만 가구로 4.6% 줄었다. 평균 가구원 수는 2.16명이다.",
    sources=src("kdi_census2025", "herald_census2025"), verified=True)

add(id=f"{Q}-E-005", type="사건", importance=2, date="2026-08-20", actor="국가데이터처",
    statement="국가데이터처가 2025 인구주택총조사 100세 이상 고령자조사 결과를 발표했다. 집에 사는 100세 이상 고령자의 48.5%가 단독주택에 살고, 47.9%가 집 구조나 설비가 불편하다고 답했다.",
    sources=src("kdi_centenarian"), verified=True)

add(id=f"{Q}-E-006", type="사건", importance=2, date="2025-10-15", actor="정부(국토교통부 등)",
    statement="정부가 수도권 주택시장 안정을 위한 10·15 대책을 발표했다. 이후 서울시장과 국토교통부 장관이 2025-11-13 공급 확대를 논의했다.",
    sources=src("hankyung_hs2024"), verified=False,
    check_flags=["원문 미확인: 대책 내용·범위를 담은 정부 보도자료를 열지 못했다. 관련 기사 제목에서만 확인"])

# =====================================================================================
# 해석 (I)
# =====================================================================================
add(id=f"{Q}-I-001", type="해석", importance=3, target="생애단계 간 면적 배분", direction="강화",
    statement="집의 면적이 생애단계와 거꾸로 배분돼 있다. 아이를 낳고 키울 신혼부부 가구는 1인당 27.4㎡로 가장 좁고 1년 새 더 좁아졌다. 고령 가구는 1인당 46.6㎡로 1.7배 넓고 2022년보다 넓어졌다. 이 차이가 이번 회차에서 확인한 가장 큰 가구-집 불일치다.",
    basis=[f"{Q}-M-013", f"{Q}-M-014", f"{Q}-M-012"])

add(id=f"{Q}-I-002", type="해석", importance=3, target="집 크기와 가구 크기", direction="강화",
    statement="1인당 주거면적이 늘어난 것은 집이 커져서가 아니라 가구가 작아져서다. 가구당 주거면적은 2019년 이후 70㎡ 안팎에 머물렀고, 같은 기간 1인당 면적은 해마다 0.5㎡ 이상 늘었다. 1·2인가구가 66.1%가 된 지금도 집의 평균 크기는 그대로다.",
    basis=[f"{Q}-M-019", f"{Q}-M-011", f"{Q}-E-004"])

add(id=f"{Q}-I-003", type="해석", importance=3, target="젊은 가구의 점유·주거 수준", direction="강화",
    statement="전체 자가점유율 상승은 젊은 가구에 닿지 않았다. 2024년 전체는 1.0%p 올랐지만 청년은 2.4%p, 신혼부부는 2.5%p 내렸다. 청년의 최저주거기준 미달은 8.2%로 고령 가구(2.1%)의 약 4배다.",
    basis=[f"{Q}-M-001", f"{Q}-M-003", f"{Q}-M-004", f"{Q}-M-017"])

add(id=f"{Q}-I-004", type="해석", importance=3, target="노후 주택과 고령 거주의 겹침", direction="강화",
    statement="노후 주택은 고령 가구가 많이 사는 단독주택에 몰려 있다. 단독주택의 60.3%가 지은 지 30년이 넘었고 고령 가구의 39.2%가 단독주택에 산다. 고령자 1인가구는 1년 새 7.3% 늘었다. 100세 이상 고령자의 절반 가까이가 집 구조·설비를 불편하다고 답했다.",
    basis=[f"{Q}-M-025", f"{Q}-M-024", f"{Q}-E-004", f"{Q}-E-005"])

add(id=f"{Q}-I-005", type="해석", importance=2, target="빈집과 소형 수요의 공존", direction="강화",
    statement="재고 총량보다 위치·유형·연식이 수요와 어긋난다. 미거주 주택은 172.2만 호로 늘었고 연립(14.7%)·다세대(11.4%)·1989년 이전 주택(16.7%)의 미거주율이 높다. 같은 시기 1인가구의 절반은 40㎡ 이하에 살고 오피스텔 거주 가구는 계속 늘었다.",
    basis=[f"{Q}-M-026", f"{Q}-M-018", f"{Q}-M-022"])

add(id=f"{Q}-I-006", type="해석", importance=2, target="주거비 부담", direction="중립",
    statement="전국 평균 주거비 부담은 3년째 비슷하다. 2022~2024년 임대료 비율은 15.8~16.0%, 주택가격 배수는 6.3배다. 다만 부담은 고령 임차 가구(RIR 25.4%)와 수도권 자가 가구(PIR 8.7배)에 쏠려 있다. 첫 집 마련 기간은 7.9년으로 늘었다.",
    basis=[f"{Q}-M-005", f"{Q}-M-006", f"{Q}-M-008", f"{Q}-M-010"])

add(id=f"{Q}-I-007", type="해석", importance=2, target="아파트 집중과 1인가구 거처", direction="강화",
    statement="주택 재고는 아파트로 모이지만 1인가구는 아파트 밖에 더 많이 산다. 아파트는 재고의 65.8%이고 신혼부부의 73.4%가 아파트에 산다. 1인가구의 아파트 거주는 35.9%에 그치고 단독주택과 주택 이외 거처 비중이 높다.",
    basis=[f"{Q}-M-021", f"{Q}-M-023", f"{Q}-M-024"])

# =====================================================================================
# 세부 전망 (F)
# =====================================================================================
add(id=f"{Q}-F-001", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 등록센서스의 1인당 주거면적은 32.8㎡ 이상이고, 가구당 주거면적은 71.5㎡ 미만일 것이다.",
    due="2027-08-31", condition="없음",
    method="국가데이터처 2026년 인구주택총조사(2027년 7월 말 발표 예상) KOSIS DT_1JC1521의 1인당·가구당 주거면적 확인. 두 조건 모두 충족 시 적중.",
    basis=[f"{Q}-M-011", f"{Q}-M-019"])

add(id=f"{Q}-F-002", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2025년도 주거실태조사에서 청년 가구의 최저주거기준 미달 비율은 7.0% 이상일 것이다.",
    due="2027-02-28", condition="없음",
    method="국토교통부 2025년도 주거실태조사 결과 발표(2026년 11~12월 예상)의 청년 가구 최저주거기준 미달 비율 확인.",
    basis=[f"{Q}-M-017"])

add(id=f"{Q}-F-003", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2025년도 주거실태조사에서 신혼부부 가구의 자가점유율은 45.0% 미만일 것이다.",
    due="2027-02-28", condition="없음",
    method="국토교통부 2025년도 주거실태조사 결과 발표의 신혼부부 가구 자가점유율 확인.",
    basis=[f"{Q}-M-004"])

add(id=f"{Q}-F-004", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 주택총조사에서 30년 이상 주택 비중은 32.5% 이상일 것이다.",
    due="2027-08-31", condition="없음",
    method="국가데이터처 2026년 인구주택총조사 주택 부문 발표(2027년 7월 말 예상)의 30년 이상 주택 비중 확인.",
    basis=[f"{Q}-M-025"])

add(id=f"{Q}-F-005", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2026년 주택총조사에서 미거주 주택은 175만 호 이상일 것이다.",
    due="2027-08-31", condition="없음",
    method="국가데이터처 2026년 인구주택총조사 주택 부문 발표의 미거주 주택 수 확인.",
    basis=[f"{Q}-M-026"])

add(id=f"{Q}-F-006", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2025년도 주거실태조사에서 전국 자가 가구의 소득 대비 주택가격 배수(PIR, 중위수)는 6.5배 이상일 것이다.",
    due="2027-02-28", condition="없음",
    method="국토교통부 2025년도 주거실태조사 결과 발표의 전국 PIR 중위수 확인.",
    basis=[f"{Q}-M-008"])

# ---------- 메인 질문 시나리오 ----------
add(id=f"{Q}-F-101", type="전망", importance=3, forecast_status="진행 중", scenario="낙관", result=None,
    statement="2027년 말까지 젊은 가구의 주거 조건이 다시 나아지고 빈집 증가가 멈춰 가구-집 어긋남이 줄어든다.",
    milestones=[{"by": "2027-02", "text": "2025년도 주거실태조사에서 청년 최저주거기준 미달 7.0% 미만, 신혼부부 자가점유율 45.0% 이상"},
                {"by": "2027-02", "text": "같은 조사에서 전국 PIR 6.5배 미만 유지"},
                {"by": "2027-08", "text": "2026년 주택총조사에서 미거주 주택 175만 호 미만"}],
    due="2027-12-31", condition="주택담보대출 규제와 금리가 2026년 수준보다 크게 강해지지 않는다.",
    method="네 가지 중 세 가지 이상 충족 시 적중: (1) 청년 최저주거기준 미달 7.0% 미만 (2) 신혼부부 자가점유율 45.0% 이상 (3) 전국 PIR 6.5배 미만 (4) 2026년 미거주 주택 175만 호 미만.",
    basis=[f"{Q}-M-017", f"{Q}-M-004", f"{Q}-M-008", f"{Q}-M-026"],
    signposts=[{"id": f"{Q}-F-002", "on_hit": "비관", "on_miss": "낙관"},
               {"id": f"{Q}-F-003", "on_hit": "비관", "on_miss": "낙관"},
               {"id": f"{Q}-F-006", "on_hit": "비관", "on_miss": "낙관"},
               {"id": f"{Q}-F-005", "on_hit": "비관", "on_miss": "낙관"}])

add(id=f"{Q}-F-102", type="전망", importance=3, forecast_status="진행 중", scenario="비관", result=None,
    statement="2027년 말까지 젊은 가구의 점유·주거 수준이 더 나빠지고, 고령 가구의 넓고 오래된 집과 빈집이 함께 늘어 어긋남이 커진다.",
    milestones=[{"by": "2027-02", "text": "2025년도 주거실태조사에서 청년 최저주거기준 미달 7.0% 이상, 신혼부부 자가점유율 45.0% 미만"},
                {"by": "2027-08", "text": "2026년 주택총조사에서 30년 이상 주택 32.5% 이상, 미거주 주택 175만 호 이상"},
                {"by": "2027-12", "text": "2026년도 주거실태조사 발표 전후로 고령 가구 1인당 주거면적이 46.6㎡ 이상 유지"}],
    due="2027-12-31", condition="없음",
    method="낙관 조건 네 가지 중 두 가지 이하 충족 시 적중.",
    basis=[f"{Q}-M-017", f"{Q}-M-004", f"{Q}-M-025", f"{Q}-M-026", f"{Q}-M-014"],
    signposts=[{"id": f"{Q}-F-002", "on_hit": "비관"}, {"id": f"{Q}-F-003", "on_hit": "비관"},
               {"id": f"{Q}-F-004", "on_hit": "비관"}, {"id": f"{Q}-F-005", "on_hit": "비관"},
               {"id": f"{Q}-F-006", "on_hit": "비관"}])

# ---------- 공통 마무리: patches.jsonl 적용 → 검증 → records.jsonl ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from validate import finish
finish(records, Path(__file__).parent)
