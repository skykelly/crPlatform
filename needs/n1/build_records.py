"""N1 R1 4유형 기록 생성 + 규칙 검증. 출력: 같은 폴더 records.jsonl
실행: python3 build_records.py  (검증 오류가 있으면 exit 1)

실질화 방법 (모든 금액 지표 공통)
  실질 지출(2020년 가격) = 명목 지출(가계동향조사, 원/월) ÷ 해당 품목 소비자물가지수(2020=100, 연평균) × 100
  품목 대응: 가전및가정용기기 ↔ 가정용 기기(E03) / 가구및조명 ↔ 가구·가사비품 및 카페트(E01)
            주택유지및수선 ↔ 주거시설 유지·보수(D03) / 가사서비스 ↔ 가구내 고용 및 가사 서비스(E062)
            연료비 ↔ 전기·가스 및 기타연료(D05) / 기타주거관련서비스 ↔ 기타 주거관련 서비스(D042)
  방향: 2022→2025 실질 연평균 변화율(3년, 방역 해제 이후 구간). 속도: 2025년 전년 대비 실질 변화율 ÷ 그 연평균.
"""
import sys
from pathlib import Path

Q, R = "N1", "R1"
KOSIS_HH = "https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1L9U101&conn_path=I2"
ECOS = "https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/"
SRC = {
    "kosis_hh": {"url": KOSIS_HH, "publisher": "국가데이터처 KOSIS (DT_1L9U101 가구당 월평균 가계수지, 전국 1인 이상)", "date": "2026-10-11", "grade": "A"},
    "cpi_e03": {"url": ECOS + "901Y009/A/2019/2025/E03", "publisher": "국가데이터처 소비자물가지수 지출목적별 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_e01": {"url": ECOS + "901Y009/A/2019/2025/E01", "publisher": "국가데이터처 소비자물가지수 지출목적별 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_d03": {"url": ECOS + "901Y009/A/2019/2025/D03", "publisher": "국가데이터처 소비자물가지수 지출목적별 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_e062": {"url": ECOS + "901Y009/A/2019/2025/E062", "publisher": "국가데이터처 소비자물가지수 지출목적별 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_d05": {"url": ECOS + "901Y009/A/2019/2025/D05", "publisher": "국가데이터처 소비자물가지수 지출목적별 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_d042": {"url": ECOS + "901Y009/A/2019/2025/D042", "publisher": "국가데이터처 소비자물가지수 지출목적별 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_d04201": {"url": ECOS + "901Y009/A/2019/2025/D04201", "publisher": "국가데이터처 소비자물가지수 품목 공동주택관리비 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_all": {"url": ECOS + "901Y009/A/2019/2025/0", "publisher": "국가데이터처 소비자물가지수 총지수 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "cpi_q": {"url": ECOS + "901Y009/Q/2025Q1/2026Q3/E03", "publisher": "국가데이터처 소비자물가지수 분기 (한국은행 ECOS 901Y009 재수록)", "date": "2026-10-12", "grade": "A"},
    "retail_g12": {"url": ECOS + "901Y100/A/2019/2025/G12/T2", "publisher": "국가데이터처 산업활동동향 재별·상품군별 소매판매액지수 (한국은행 ECOS 901Y100 재수록)", "date": "2026-10-12", "grade": "A"},
    "retail_g14": {"url": ECOS + "901Y100/A/2019/2025/G14/T2", "publisher": "국가데이터처 산업활동동향 재별·상품군별 소매판매액지수 (한국은행 ECOS 901Y100 재수록)", "date": "2026-10-12", "grade": "A"},
    "kdi_2q": {"url": "https://eiec.kdi.re.kr/policy/materialView.do?num=285882", "publisher": "KDI 경제정보센터 (국가데이터처 2026년 2/4분기 가계동향조사 결과 요약)", "date": "2026-08-27", "grade": "B"},
    "fn_2q": {"url": "https://www.fnnews.com/news/202608271139505699", "publisher": "파이낸셜뉴스 (국가데이터처 2026년 2분기 가계동향조사 인용)", "date": "2026-08-27", "grade": "B"},
    "sbs_2q": {"url": "https://biz.sbs.co.kr/amp/article/20000331131", "publisher": "SBS Biz (국가데이터처 2026년 2분기 가계동향조사 인용)", "date": "2026-08-27", "grade": "B"},
    "newsseoul_2q": {"url": "https://newsseoul.co.kr/news/view/1065586816756608", "publisher": "뉴스서울 (재정경제부 2026년 2/4분기 가계동향 평가 인용)", "date": "2026-08-27", "grade": "B"},
    "newsis_1q": {"url": "https://www.newsis.com/view/NISX20260528_0003646801", "publisher": "뉴시스 (국가데이터처 2026년 1분기 가계동향조사 인용)", "date": "2026-05-28", "grade": "B"},
    "newsis_jun": {"url": "https://www.newsis.com/view/NISX20260803_0003733704", "publisher": "뉴시스 (국가데이터처 2026년 6월 온라인쇼핑동향 인용)", "date": "2026-08-03", "grade": "B"},
    "cpi_rev": {"url": "https://dazabi.com/insurance_magazine/article.php?id=33969", "publisher": "다자비 인슈어런스 매거진 (국가데이터처 2025년 소비자물가지수 개편 안내 인용)", "date": "2026-07-07", "grade": "B"},
    "newsis_1p": {"url": "https://www.newsis.com/view/NISX20251209_0003433761", "publisher": "뉴시스 (국가데이터처 2025 통계로 보는 1인 가구 인용)", "date": "2025-12-09", "grade": "B"},
    "ytn_kapt": {"url": "https://www.ytn.co.kr/_ln/0102_202603041015500867", "publisher": "YTN (한국부동산원 공동주택관리정보시스템(K-apt) 자료 인용)", "date": "2026-03-04", "grade": "B"},
    "newsis_kapt": {"url": "https://www.newsis.com/view/NISX20250408_0003131504", "publisher": "뉴시스 (한국부동산원 공동주택관리정보시스템(K-apt) 자료 인용)", "date": "2025-04-09", "grade": "B"},
}
def src(*keys): return [dict(SRC[k], key=k) for k in keys]

base = dict(question=Q, question_version="v1.0", first_seen=R, last_seen=R, status="유효", replaces=None, check_flags=[])
records = []
def add(**kw):
    r = dict(base); r.update(kw); records.append(r)

YEARS = [str(y) for y in range(2019, 2026)]
def ser(vals, nd=0):
    return {y: (round(v) if nd == 0 else round(v, nd)) for y, v in zip(YEARS, vals)}

# 명목 지출 (KOSIS DT_1L9U101, 전체가구, 원/월) — 팩트베이스 원자료 data/raw/2026-10-11/DT_1L9U101_2019.json
NOM = {
    "가전": [37428.903, 41344.068, 38660.211, 32764.094, 31858.577, 34910.355, 33804.078],
    "가구": [17549.025, 19739.859, 22440.09, 18084.117, 18835.315, 18471.596, 18210.286],
    "수선": [26669.776, 30967.555, 37114.605, 25823.424, 26173.646, 30362.56, 26866.071],
    "가사": [14121.989, 12369.002, 15000.772, 12849.401, 13469.763, 13605.908, 10103.214],
    "연료": [79339.549, 80802.942, 82109.636, 89474.956, 103850.577, 106882.584, 111856.249],
    "관리": [50916.954, 53473.586, 58316.074, 61615.363, 65246.288, 68389.757, 71219.208],
}
# 소비자물가지수 연평균 (2020=100)
CPI = {
    "가전": [101.582, 100, 99.82, 100.1, 103.02, 103.63, 105.91],      # E03 가정용 기기
    "가구": [99.629, 100, 104.57, 112.55, 121.25, 125.95, 130.64],     # E01 가구, 가사비품 및 카페트
    "수선": [97.863, 100, 104.96, 112.47, 116.63, 118.78, 121.37],     # D03 주거시설 유지·보수
    "가사": [97.896, 100, 104.22, 111.37, 120.11, 125.25, 128.96],     # E062 가구내 고용 및 가사 서비스
    "연료": [101.949, 100, 98.63, 115.65, 138.69, 142.93, 145.03],     # D05 전기, 가스 및 기타연료
    "관리": [95.31, 100, 105.1, 109.99, 115.56, 120.75, 125.57],       # D042 기타 주거관련 서비스
    "총지수": [99.466, 100, 102.5, 107.72, 111.59, 114.18, 116.61],
    "공동주택관리비": [95.115, 100, 105.3, 110.46, 116.3, 121.69, 126.62],
}
REAL = {k: [n / c * 100 for n, c in zip(NOM[k], CPI[k])] for k in NOM}
def cagr(v, a=3, b=6): return ((v[b] / v[a]) ** (1 / (b - a)) - 1) * 100
def yoy(v): return (v[6] / v[5] - 1) * 100
def stats(k):
    v = REAL[k]
    return {"real_cagr_2022_2025": round(cagr(v), 2), "real_yoy_2025": round(yoy(v), 1),
            "nominal_yoy_2025": round(yoy(NOM[k]), 1), "real_cagr_2019_2025": round(cagr(v, 0, 6), 2)}

DEF = ("팩트베이스(KOSIS API) 값. 가계동향조사 전체가구(1인 이상) 가구당 월평균 명목 지출을 소비자물가지수 {cpi}(2020=100, 연평균)로 나눠 "
       "2020년 가격 실질값으로 환산. 실질 = 명목 ÷ 지수 × 100")

# ---------- 지표 (M) ----------
# K1 가전
add(id=f"{Q}-M-001", type="지표", indicator=f"{Q}-K1", importance=3, representative=True,
    statement="2025년 가구당 월평균 가전·가정용기기 실질 지출은 3만 1,918원(2020년 가격)으로 1년 전보다 5.3% 줄었다. 2022년 이후 3년 연평균 변화는 -0.8%다.",
    value=round(REAL["가전"][6]), unit="원/월(2020년 가격)", as_of="2025", region="KR", prev_value=round(REAL["가전"][5]),
    definition=DEF.format(cpi="가정용 기기(E03)"),
    extra={"series": ser(REAL["가전"]), "nominal": ser(NOM["가전"]), "cpi": ser(CPI["가전"], 3), **stats("가전")},
    sources=src("kosis_hh", "cpi_e03"), verified=True)
add(id=f"{Q}-M-002", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="가전제품 소매판매액지수(불변)는 2022년 103.5에서 2025년 81.0으로 떨어졌다. 2026년 1·2분기는 각각 78.7, 88.6으로 1년 전보다 높다.",
    value=81.0, unit="지수(2020=100)", as_of="2025", region="KR", prev_value=86.1,
    definition="산업활동동향 재별·상품군별 소매판매액지수 가전제품 불변지수(가격 변동 제거). 소매 판매 기준이라 가계동향 가구 지출과 범위가 다르다.",
    extra={"series": {"2019": 82.8, "2020": 100, "2021": 110.4, "2022": 103.5, "2023": 89.9, "2024": 86.1, "2025": 81.0},
           "quarterly": {"2025Q1": 75.7, "2025Q2": 84.2, "2026Q1": 78.7, "2026Q2": 88.6}},
    sources=src("retail_g12"), verified=True)
add(id=f"{Q}-M-003", type="지표", indicator=f"{Q}-K1", importance=2, representative=False,
    statement="2026년 2분기 가전·가정용기기 명목 지출은 1년 전보다 40.1% 늘었다. 같은 기간 가정용 기기 물가는 3.2% 올랐다.",
    value=40.1, unit="% (전년 동기 대비, 명목)", as_of="2026Q2", region="KR", prev_value=None,
    definition="가계동향조사 2026년 2분기 전년 동기 대비 명목 증감률(언론 보도 인용). 소비자물가 가정용 기기 분기 지수 2025Q2 106.43 → 2026Q2 109.81. 단순 실질 환산 약 +35.8%(1.401 ÷ 1.032 − 1).",
    extra={"cpi_e03_q": {"2025Q2": 106.43, "2026Q2": 109.81}},
    sources=src("fn_2q", "cpi_q"), verified=True,
    check_flags=["확인 필요: 분기 품목 증감률은 언론 인용값이며 국가데이터처 보도자료 원표를 열지 못함"])
# K2 가구
add(id=f"{Q}-M-004", type="지표", indicator=f"{Q}-K2", importance=3, representative=True,
    statement="2025년 가구당 월평균 가구·조명 실질 지출은 1만 3,939원(2020년 가격)으로 1년 전보다 5.0% 줄었다. 2022년 이후 3년 연평균 -4.6%다.",
    value=round(REAL["가구"][6]), unit="원/월(2020년 가격)", as_of="2025", region="KR", prev_value=round(REAL["가구"][5]),
    definition=DEF.format(cpi="가구·가사비품 및 카페트(E01)") + ". 가계동향 '가구및조명' 항목 기준이며 실내장식(2025년 명목 1,965원)은 별도 항목이라 제외",
    extra={"series": ser(REAL["가구"]), "nominal": ser(NOM["가구"]), "cpi": ser(CPI["가구"], 3), **stats("가구"),
           "interior_nominal": {"2019": 1607, "2025": 1965}},
    sources=src("kosis_hh", "cpi_e01"), verified=True)
add(id=f"{Q}-M-005", type="지표", indicator=f"{Q}-K2", importance=2, representative=False,
    statement="가구 소매판매액지수(불변)는 2022년 88.2에서 2025년 77.8로 떨어졌다. 2026년 상반기는 1년 전보다 1.8% 낮다.",
    value=77.8, unit="지수(2020=100)", as_of="2025", region="KR", prev_value=83.9,
    definition="산업활동동향 재별·상품군별 소매판매액지수 가구 불변지수. 2026년 상반기 비교는 1·2분기 합계 기준.",
    extra={"series": {"2019": 81.1, "2020": 100, "2021": 104.2, "2022": 88.2, "2023": 78.6, "2024": 83.9, "2025": 77.8},
           "quarterly": {"2025Q1": 82.6, "2025Q2": 74.6, "2026Q1": 80.0, "2026Q2": 74.4}},
    sources=src("retail_g14"), verified=True)
# K3 수선
add(id=f"{Q}-M-006", type="지표", indicator=f"{Q}-K3", importance=3, representative=True,
    statement="2025년 가구당 월평균 주택 유지·수선 실질 지출은 2만 2,136원(2020년 가격)으로 1년 전보다 13.4% 줄었다. 2024년에는 13.9% 늘어 해마다 등락이 크다.",
    value=round(REAL["수선"][6]), unit="원/월(2020년 가격)", as_of="2025", region="KR", prev_value=round(REAL["수선"][5]),
    definition=DEF.format(cpi="주거시설 유지·보수(D03)"),
    extra={"series": ser(REAL["수선"]), "nominal": ser(NOM["수선"]), "cpi": ser(CPI["수선"], 3), **stats("수선")},
    sources=src("kosis_hh", "cpi_d03"), verified=True)
# K4 가사서비스
add(id=f"{Q}-M-007", type="지표", indicator=f"{Q}-K4", importance=3, representative=True,
    statement="2025년 가구당 월평균 가사서비스 실질 지출은 7,834원(2020년 가격)으로 1년 전보다 27.9% 줄었다. 2022년 이후 3년 연평균 -12.1%다.",
    value=round(REAL["가사"][6]), unit="원/월(2020년 가격)", as_of="2025", region="KR", prev_value=round(REAL["가사"][5]),
    definition=DEF.format(cpi="가구내 고용 및 가사 서비스(E062)"),
    extra={"series": ser(REAL["가사"]), "nominal": ser(NOM["가사"]), "cpi": ser(CPI["가사"], 3), **stats("가사"), "nominal_yoy_2025": -25.7},
    sources=src("kosis_hh", "cpi_e062"), verified=True,
    check_flags=["확인 필요: 2025년 명목 -25.7%(13,606원→10,103원)의 원인이 실제 지출 감소인지 분류·표본 변경인지 확인하지 못함. 가구 단위 이용 가구 비율과 표본오차 미확인",
                 "확인 필요: 월 1만 원 안팎의 소액 항목이라 표본 변동이 클 수 있음. 판정은 잠정"])
# K5 연료비(광열)
add(id=f"{Q}-M-008", type="지표", indicator=f"{Q}-K5", importance=3, representative=True,
    statement="2025년 가구당 월평균 연료비(전기·가스·기타연료)는 명목 11만 1,856원이다. 실질로는 7만 7,126원(2020년 가격)으로 1년 전보다 3.1% 늘었고, 2022년 이후 3년 연평균은 -0.1%다.",
    value=round(REAL["연료"][6]), unit="원/월(2020년 가격)", as_of="2025", region="KR", prev_value=round(REAL["연료"][5]),
    definition=DEF.format(cpi="전기, 가스 및 기타연료(D05)") + ". 팩트베이스 S05는 주거·수도·광열 전체(2025년 36만 650원)로 매핑돼 있어 세부 항목 '연료비'를 같은 원자료에서 꺼냄",
    extra={"series": ser(REAL["연료"]), "nominal": ser(NOM["연료"]), "cpi": ser(CPI["연료"], 3), **stats("연료"),
           "housing_utilities_total_nominal_2025": 360650, "housing_utilities_share_2025_pct": 12.3},
    sources=src("kosis_hh", "cpi_d05"), verified=True,
    check_flags=["확인 필요: 팩트베이스 S05가 '주거·수도·광열' 대분류로 매핑돼 지표 정의(연료비)와 다름. 원자료 세부 항목으로 대체"])
add(id=f"{Q}-M-009", type="지표", indicator=f"{Q}-K5", importance=2, representative=False,
    statement="1인가구 소비지출에서 주거·수도·광열이 차지하는 비중은 18.4%로 가장 크다. 같은 해 전체가구는 12.2%다.",
    value=18.4, unit="% (소비지출 중 비중)", as_of="2024", region="KR", prev_value=None,
    definition="1인가구 값은 국가데이터처 '2025 통계로 보는 1인 가구'(2024년 가계동향 기준) 보도 인용. 전체가구 12.2%는 KOSIS DT_1L9U101 2024년 주거·수도·광열 35만 1,613원 ÷ 소비지출 289만 478원으로 계산.",
    extra={"one_person_spending_2024": 1689000, "all_spending_2024": 2890478,
           "one_person_floor_area_pct": {"40㎡ 이하": 49.6, "40~50㎡": 13.0, "50~60㎡": 11.6, "60~85㎡": 18.0, "85~102㎡": 3.9, "102~135㎡": 3.2, "135㎡ 초과": 0.5},
           "one_person_le60_pct": 74.2, "one_person_share_households_2024": 36.1},
    sources=src("newsis_1p", "kosis_hh"), verified=True,
    check_flags=["확인 필요: 1인가구 비중·면적 분포는 언론 인용값. 면적 분포의 기준 통계·연도는 보도자료 원문으로 확인 필요"])
# K6 관리비
add(id=f"{Q}-M-010", type="지표", indicator=f"{Q}-K6", importance=3, representative=True,
    statement="2026년 1월 전국 아파트 관리비는 ㎡당 3,343원으로 1년 전보다 4.3% 올랐다. 같은 기간 소비자물가 총지수 상승률 2.0%를 빼면 실질 약 2.2% 올랐다.",
    value=3343, unit="원/㎡", as_of="2026-01", region="KR", prev_value=3206,
    definition="공동주택관리정보시스템(K-apt) 전국 아파트 ㎡당 월 관리비(공용관리비+개별사용료+장기수선충당금). 실질 = (3,343 ÷ 2026년 1월 총지수 118.03) ÷ (3,206 ÷ 2025년 1월 총지수 115.71) − 1.",
    extra={"components_2025_01_to_2026_01": {"공용관리비": [1368, 1394], "개별사용료": [1562, 1654], "난방비": [393, 444], "전기료": [718, 740],
                                              "수도료": [247, 257], "장기수선충당금": [276, 295]},
           "apt84_monthly_won": {"2025-01": 269304, "2026-01": 280812}, "cpi_all_m": {"2025-01": 115.71, "2026-01": 118.03}, "real_change_pct": 2.2},
    sources=src("ytn_kapt"), verified=True,
    check_flags=["확인 필요: K-apt 원표를 직접 열지 못하고 보도 인용값을 씀. 1월은 난방 영향이 커 연평균과 다를 수 있음"])
add(id=f"{Q}-M-011", type="지표", indicator=f"{Q}-K6", importance=2, representative=False,
    statement="전국 아파트 ㎡당 월 관리비 연평균은 2015년 2,091원에서 2024년 2,920원으로 약 40% 올랐다. 같은 기간 소비자물가는 약 20% 올랐다.",
    value=2920, unit="원/㎡", as_of="2024", region="KR", prev_value=2091,
    definition="K-apt 전국 아파트 ㎡당 월 관리비 연평균(보도 인용). 소비자물가 20.0%는 같은 보도 값. 총지수로 실질화하면 9년 연평균 약 +1.7%.",
    extra={"series": {"2015": 2091, "2024": 2920}, "common_fee": {"2015": 882, "2024": 1247}, "individual_fee": {"2015": 1077, "2024": 1392},
           "long_term_repair_reserve": {"2015": 131, "2024": 281}},
    sources=src("newsis_kapt"), verified=True,
    check_flags=["확인 필요: 2016~2023년 연평균 값을 확보하지 못해 3~5년 추세 판정에 쓰지 못함"])
add(id=f"{Q}-M-012", type="지표", indicator=f"{Q}-K6", importance=2, representative=False,
    statement="가계동향의 기타주거관련서비스(공동주택관리비 등) 지출은 2025년 명목 7만 1,219원이다. 실질로는 5만 6,717원(2020년 가격)으로 2022년 이후 연평균 0.4% 늘어 거의 그대로다.",
    value=round(REAL["관리"][6]), unit="원/월(2020년 가격)", as_of="2025", region="KR", prev_value=round(REAL["관리"][5]),
    definition=DEF.format(cpi="기타 주거관련 서비스(D042)") + ". 명목 증가분 대부분이 단가 상승이라는 뜻. 총지수로 나누면 2022→2025 연평균 +2.2%",
    extra={"series": ser(REAL["관리"]), "nominal": ser(NOM["관리"]), "cpi": ser(CPI["관리"], 3), **stats("관리"),
           "general_cpi_deflated_cagr_2022_2025": 2.21},
    sources=src("kosis_hh", "cpi_d042"), verified=True,
    check_flags=["확인 필요: 가계동향 '기타주거관련서비스'는 공동주택관리비 외 항목을 포함할 수 있어 K6(㎡당 관리비)와 정의가 다름"])
# K7 온라인 거래액
add(id=f"{Q}-M-017", type="지표", indicator=f"{Q}-K7", importance=2, representative=True,
    statement="2026년 6월 온라인쇼핑 가전·전자 거래액은 1조 6,776억원으로 1년 전보다 11.9% 늘었다. 통신기기는 8,924억원으로 144.4% 늘었다.",
    value=16776, unit="억원", as_of="2026-06", region="KR", prev_value=None,
    definition="국가데이터처 온라인쇼핑동향 상품군별 거래액 중 가전·전자(통신기기 별도). 보도 인용값이며 명목 금액이다. 생활용품·가구 상품군 값은 확인하지 못했다. 같은 달 전체 온라인쇼핑은 24조 6,067억원(+10.7%).",
    extra={"telecom_devices_eok": 8924, "telecom_yoy_pct": 144.4, "total_eok": 246067, "total_yoy_pct": 10.7},
    sources=src("newsis_jun"), verified=True,
    check_flags=["확인 필요: 생활용품·가구 상품군 거래액과 연간 시계열을 열지 못함. 국가데이터처 원표 확인 필요", "확인 필요: 명목값이라 가전·가구 판정에는 쓰지 않음"])
# K8 관련 품목 소비자물가
add(id=f"{Q}-M-013", type="지표", indicator=f"{Q}-K8", importance=3, representative=True,
    statement="2025년 가구내 고용 및 가사 서비스 물가지수는 128.96(2020=100)으로 1년 전보다 3.0% 올랐다. 2026년 3분기는 1년 전보다 4.2% 높다.",
    value=128.96, unit="지수(2020=100)", as_of="2025", region="KR", prev_value=125.25,
    definition="소비자물가지수 지출목적별 E062 연평균. 분기 값 2025Q3 129.39, 2026Q3 134.83.",
    extra={"series": ser(CPI["가사"], 3), "quarterly": {"2025Q3": 129.39, "2026Q3": 134.83}},
    sources=src("cpi_e062"), verified=True)
add(id=f"{Q}-M-014", type="지표", indicator=f"{Q}-K8", importance=2, representative=False,
    statement="2020년 이후 가구·가사비품 물가는 30.6%, 주거시설 유지·보수 물가는 21.4% 올랐다. 가정용 기기 물가는 5.9% 올라 소비자물가 총지수(16.6%)보다 덜 올랐다.",
    value=130.64, unit="지수(2020=100)", as_of="2025", region="KR", prev_value=125.95,
    definition="소비자물가지수 지출목적별 연평균: E01 가구·가사비품 및 카페트 130.64, D03 주거시설 유지·보수 121.37, E03 가정용 기기 105.91, 총지수 116.61 (모두 2025년, 2020=100). value는 E01.",
    extra={"E01": ser(CPI["가구"], 3), "D03": ser(CPI["수선"], 3), "E03": ser(CPI["가전"], 3), "총지수": ser(CPI["총지수"], 3),
           "2026Q3_yoy_pct": {"E01": 3.2, "D03": 4.4, "E03": 3.3}},
    sources=src("cpi_e01", "cpi_d03", "cpi_e03", "cpi_all"), verified=True)
add(id=f"{Q}-M-015", type="지표", indicator=f"{Q}-K8", importance=2, representative=False,
    statement="전기·가스 및 기타연료 물가는 2022~2023년에 크게 올라 2025년 145.03(2020=100)이다. 2025년 상승률은 1.5%로 둔화했다.",
    value=145.03, unit="지수(2020=100)", as_of="2025", region="KR", prev_value=142.93,
    definition="소비자물가지수 지출목적별 D05 연평균. 분기 값 2025Q3 140.83, 2026Q3 142.83(+1.4%).",
    extra={"series": ser(CPI["연료"], 3), "quarterly": {"2025Q3": 140.83, "2026Q3": 142.83}},
    sources=src("cpi_d05"), verified=True)
add(id=f"{Q}-M-016", type="지표", indicator=f"{Q}-K8", importance=2, representative=False,
    statement="공동주택관리비 물가지수는 2025년 126.62(2020=100)로 1년 전보다 4.1% 올랐다. 2020년 이후 해마다 4~6%씩 올랐다.",
    value=126.62, unit="지수(2020=100)", as_of="2025", region="KR", prev_value=121.69,
    definition="소비자물가지수 품목 D04201 공동주택관리비 연평균. 분기 값 2025Q3 127.03, 2026Q3 131.12(+3.2%).",
    extra={"series": ser(CPI["공동주택관리비"], 3), "D042_기타주거관련서비스": ser(CPI["관리"], 3), "quarterly": {"2025Q3": 127.03, "2026Q3": 131.12}},
    sources=src("cpi_d04201", "cpi_d042"), verified=True)

# ---------- 사건 (E) ----------
add(id=f"{Q}-E-001", type="사건", importance=3, date="2026-08-27", actor="국가데이터처",
    statement="2026년 2분기 가계동향조사를 발표했다. 가정용품·가사서비스 지출이 17.9% 늘어 2020년 이후 가장 크게 증가했다. 가전·가정용기기는 40.1% 늘었고, 대형 가전업체 판촉 행사가 배경으로 언급됐다.",
    sources=src("kdi_2q", "fn_2q", "sbs_2q"), verified=True,
    check_flags=["확인 필요: 행사 성격(할인·환급)이 보도마다 다르게 적힘"])
add(id=f"{Q}-E-002", type="사건", importance=2, date="2026-08-27", actor="재정경제부",
    statement="2분기 가계 소득 증가에 고유가 지원금 등 이전소득(+20.4%)이 기여했다고 평가했다. 같은 분기 실질 소비지출 증가율은 0.4%에 그쳤다.",
    sources=src("newsseoul_2q", "fn_2q"), verified=True)
add(id=f"{Q}-E-003", type="사건", importance=2, date="2026-05-28", actor="국가데이터처",
    statement="2026년 1분기 가계동향조사를 발표했다. 실질 소비지출이 3.1% 늘어 2023년 1분기 이후 가장 큰 폭이었고, 가구 등 내구재 구매 증가가 언급됐다.",
    sources=src("newsis_1q"), verified=True)
add(id=f"{Q}-E-004", type="사건", importance=2, date="2026-03-04", actor="한국부동산원",
    statement="K-apt 집계상 2026년 1월 전국 아파트 ㎡당 관리비가 1년 전보다 4.3% 올랐다는 보도가 나왔다. 난방비(+13.0%)와 장기수선충당금 인상이 컸다.",
    sources=src("ytn_kapt"), verified=True)
add(id=f"{Q}-E-005", type="사건", importance=2, date="2025-12-09", actor="국가데이터처",
    statement="'2025 통계로 보는 1인 가구'를 발표했다. 1인가구는 804만 5천 가구로 전체의 36.1%이며, 소비지출 가운데 주거·수도·광열 비중이 가장 컸다.",
    sources=src("newsis_1p"), verified=True)

add(id=f"{Q}-E-006", type="사건", importance=3, date="2026-07-07", actor="국가데이터처",
    statement="소비자물가지수 기준연도를 2020년에서 2025년으로 바꾸는 개편안의 의견 수렴(7월 7~17일)을 시작했다. 새 지수는 2026년 12월 18일 공표하며, 2020년 기준으로 계산한 2025년 1월~2026년 11월 값이 달라질 수 있다.",
    sources=src("cpi_rev"), verified=True,
    check_flags=["확인 필요: 개편 공표일(2026-12-18)은 예정일이며 국가데이터처 원문을 열지 못함. 실질화 값은 새 기준으로 다시 계산해야 함"])

# ---------- 해석 (I) ----------
add(id=f"{Q}-I-001", type="해석", importance=3, target="가사서비스 외주", direction="약화",
    statement="가사서비스는 6개 품목 중 실질 감소가 가장 빠르다. 2022년 이후 연평균 12.1% 줄었고 2025년에는 27.9% 줄었다. 같은 기간 서비스 단가는 해마다 3~8% 올랐다.",
    basis=[f"{Q}-M-007", f"{Q}-M-013"])
add(id=f"{Q}-I-002", type="해석", importance=3, target="가구·인테리어 내구재", direction="약화",
    statement="가구는 가계 지출과 소매 판매 모두 실질 감소가 3년째 이어진다. 가구 물가가 2020년 이후 30% 넘게 올라 명목 지출은 거의 그대로인데 실제 구매량은 줄었다.",
    basis=[f"{Q}-M-004", f"{Q}-M-005", f"{Q}-M-014"])
add(id=f"{Q}-I-003", type="해석", importance=3, target="가전 교체 수요", direction="중립",
    statement="가전 실질 지출은 2022년 이후 3만 1천~3만 4천 원대에서 오르내린다. 2025년에는 줄었지만 2026년 상반기 소매 판매와 2분기 가계 지출이 크게 늘어 방향 전환 여부는 2026년 연간값으로 판단해야 한다.",
    basis=[f"{Q}-M-001", f"{Q}-M-002", f"{Q}-M-003", f"{Q}-E-001"])
add(id=f"{Q}-I-004", type="해석", importance=3, target="관리비·연료비 같은 고정 주거비", direction="강화",
    statement="관리비와 연료비는 실질 사용량으로는 거의 그대로다. 그러나 단가가 일반 물가보다 빨리 올라 총지수로 나눈 실질 부담은 2022년 이후 관리비 연 2.2%, 연료비 연 4.9% 늘었다.",
    basis=[f"{Q}-M-008", f"{Q}-M-012", f"{Q}-M-010", f"{Q}-M-016"])
add(id=f"{Q}-I-005", type="해석", importance=2, target="주택 수선·보수", direction="약화",
    statement="주택 유지·수선 실질 지출은 해마다 10% 넘게 오르내리지만 2022년 이후 평균으로는 연 1.2% 줄었다. 수선 단가는 2026년 3분기에 1년 전보다 4.4% 올라 부담이 커지고 있다.",
    basis=[f"{Q}-M-006", f"{Q}-M-014"])
add(id=f"{Q}-I-006", type="해석", importance=2, target="1인가구의 주거비 비중", direction="강화",
    statement="1인가구는 소비지출의 18.4%를 주거·수도·광열에 쓴다. 전체가구 12.2%보다 6%p 넘게 높다. 1인가구의 74%가 전용 60㎡ 이하에 살아 면적당 고정비 부담이 크다.",
    basis=[f"{Q}-M-009", f"{Q}-E-005"])

# ---------- 세부 전망 (F) ----------
add(id=f"{Q}-F-001", type="전망", importance=3, forecast_status="진행 중", result=None,
    statement="2026년 가구당 월평균 가전·가정용기기 실질 지출(2020년 가격)은 2025년 3만 1,918원보다 많을 것이다.",
    due="2027-03-31", condition="없음",
    method="국가데이터처 2026년 연간 가계동향(KOSIS DT_1L9U101) 가전및가정용기기 명목값 ÷ 2026년 가정용 기기 물가지수(E03) 연평균 × 100이 31,918원 초과면 적중. 소비자물가 기준연도가 2025년으로 바뀌면 2025년 값도 새 지수로 다시 계산해 비교",
    basis=[f"{Q}-M-001", f"{Q}-M-002", f"{Q}-M-003"])
add(id=f"{Q}-F-002", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 가사서비스 실질 지출(2020년 가격)은 2025년 7,834원 이하에 머물 것이다.",
    due="2027-03-31", condition="없음",
    method="2026년 연간 가계동향 가사서비스 명목값 ÷ 2026년 E062 물가지수 연평균 × 100이 7,834원 이하이면 적중. 소비자물가 기준연도가 2025년으로 바뀌면 2025년 값도 새 지수로 다시 계산해 비교",
    basis=[f"{Q}-M-007", f"{Q}-M-013"])
add(id=f"{Q}-F-003", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 가구·조명 실질 지출(2020년 가격)은 2025년 1만 3,939원보다 적을 것이다.",
    due="2027-03-31", condition="없음",
    method="2026년 연간 가계동향 가구및조명 명목값 ÷ 2026년 E01 물가지수 연평균 × 100이 13,939원 미만이면 적중. 소비자물가 기준연도가 2025년으로 바뀌면 2025년 값도 새 지수로 다시 계산해 비교",
    basis=[f"{Q}-M-004", f"{Q}-M-005"])
add(id=f"{Q}-F-004", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2027년 1월 전국 아파트 ㎡당 관리비는 2026년 1월 3,343원보다 3% 이상 높을 것이다.",
    due="2027-03-31", condition="겨울 기온이 평년 수준",
    method="K-apt 또는 한국부동산원 공표(인용 보도 포함) 2027년 1월 전국 ㎡당 관리비가 3,443원 이상이면 적중",
    basis=[f"{Q}-M-010", f"{Q}-M-011", f"{Q}-M-016"])
add(id=f"{Q}-F-005", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 연료비 실질 지출(2020년 가격)은 2025년 대비 ±3% 안에 머물 것이다.",
    due="2027-03-31", condition="전기·가스 요금의 큰 폭 조정이 없음",
    method="2026년 연간 가계동향 연료비 명목값 ÷ 2026년 D05 물가지수 연평균 × 100이 74,812~79,440원이면 적중",
    basis=[f"{Q}-M-008", f"{Q}-M-015"])
add(id=f"{Q}-F-006", type="전망", importance=2, forecast_status="진행 중", result=None,
    statement="2026년 3분기 가계동향에서 가정용품·가사서비스 명목 지출은 1년 전보다 늘 것이다.",
    due="2026-12-31", condition="없음",
    method="국가데이터처 2026년 3분기 가계동향조사 발표(2026년 11월 예정)에서 가정용품·가사서비스 전년 동기 대비 증감률이 0% 초과면 적중",
    basis=[f"{Q}-E-001", f"{Q}-M-003", f"{Q}-M-002"])

# ---------- 메인 질문 시나리오 ----------
add(id=f"{Q}-F-101", type="전망", importance=3, forecast_status="진행 중", scenario="낙관", result=None,
    statement="2027년 말까지 가전을 시작으로 가정용 내구재 실질 지출이 회복 쪽으로 돌아선다. 가구 감소도 멈추고, 고정 주거비 상승은 일반 물가 수준으로 내려온다.",
    milestones=[{"by": "2026-11", "text": "2026년 3분기 가정용품·가사서비스 지출 증가 지속"},
                {"by": "2027-02", "text": "2026년 연간 가전 실질 지출이 2025년보다 많음"},
                {"by": "2027-11", "text": "2027년 1~3분기 가전·가구 소매판매액지수(불변) 누계가 1년 전보다 높음"}],
    due="2027-12-31", condition="가계 실질소득 증가가 이어짐",
    method="세 가지 중 두 가지 이상 충족 시 적중: (1) 2026년 가전 실질 지출 > 2025년 (2) 2026년 가구 실질 지출 ≥ 2025년 (3) 2027년 1~3분기 가전·가구 소매판매액지수(불변) 합계가 2026년 같은 기간보다 높음",
    basis=[f"{Q}-M-001", f"{Q}-M-002", f"{Q}-M-003", f"{Q}-M-004", f"{Q}-E-001"],
    signposts=[{"id": f"{Q}-F-001", "on_hit": "낙관", "on_miss": "비관"},
               {"id": f"{Q}-F-003", "on_hit": "비관", "on_miss": "낙관"},
               {"id": f"{Q}-F-006", "on_hit": "낙관", "on_miss": "비관"}])
add(id=f"{Q}-F-102", type="전망", importance=3, forecast_status="진행 중", scenario="비관", result=None,
    statement="2027년 말까지 2026년 가전 반등은 일시적 판촉 효과로 끝나고 가정용 내구재·가사서비스 실질 지출은 다시 줄어든다. 관리비·연료비 같은 고정 주거비의 실질 부담만 커진다.",
    milestones=[{"by": "2027-02", "text": "2026년 가구·가사서비스 실질 지출이 2025년보다 적음"},
                {"by": "2027-03", "text": "2027년 1월 ㎡당 관리비가 1년 전보다 3% 이상 상승"},
                {"by": "2027-11", "text": "2027년 1~3분기 가전 소매판매액지수(불변)가 1년 전보다 낮음"}],
    due="2027-12-31", condition="없음",
    method="낙관 조건 중 하나 이하 충족 시 적중",
    basis=[f"{Q}-M-004", f"{Q}-M-007", f"{Q}-M-010", f"{Q}-M-012"],
    signposts=[{"id": f"{Q}-F-002", "on_hit": "비관"}, {"id": f"{Q}-F-004", "on_hit": "비관"},
               {"id": f"{Q}-F-005", "on_miss": "비관"}])

# ---------- 공통 마무리 ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from validate import finish
finish(records, Path(__file__).parent)
