"""판정 섹션 공통 부품: 게이지(잠정 표시 포함), 툴팁, '판정 기준 보기' 패널, 공통 판정 규칙."""
import html
E = html.escape

COMMON_RULES = [
    "분모는 '해 본 적 있다'가 아니라 '주로 AI로 한다'는 비율이다.",
    "의향 설문 수치는 한 단계 낮춰 적용하고, 의향만으로는 2단계를 넘지 않는다.",
    "4단계는 과반이면서 기존 방식이 줄어든 것이 수치로 확인돼야 한다.",
    "4단계에 오른 뒤에도 대표 지표는 핵심 지표 표에서 계속 추적한다.",
    "기준을 직접 재는 수치가 없어 간접 근거로 판정한 칸은 '잠정'이며, 게이지의 점선 테두리와 빗금으로 표시한다. 그 지표를 다음 조사에서 먼저 찾는다.",
]

def tipattr(text):
    return f' tabindex="0" data-tip="{E(text)}"' if text else ""

def gauge(levels, level, tip=None, prov=False, label=None, show_label=True):
    """levels: 단계 이름 목록, level: 현재 단계. prov=True면 점선 게이지 + 잠정."""
    i = levels.index(level)
    pips = "".join(f'<span class="pip{" on" if k <= i else ""}"></span>' for k in range(len(levels)))
    lab = f'<span class="lv"{tipattr(tip)}>{E(label or level)}</span>' if show_label else ""
    return f'<span class="pips{" prov" if prov else ""}">{pips}{lab}</span>'

def chip(text, cls, tip=None, prov=False):
    return f'<span class="own {cls}"{tipattr(tip)}>{E(text)}</span>'

def table(headers, rows):
    """rows의 각 칸은 이미 HTML로 만든 문자열."""
    head = "".join(f"<th>{E(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table class="crit"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

def criteria_panel(blocks, rules=None, extra_rules=()):
    """blocks: [(소제목, headers, rows)]"""
    rules = list(rules if rules is not None else COMMON_RULES) + list(extra_rules)
    inner = "".join(f"<h4>{E(t)}</h4>{table(h, r)}" for t, h, r in blocks)
    rl = "".join(f"<li>{E(x)}</li>" for x in rules)
    return f'<details class="criteria"><summary>판정 기준 보기</summary><div class="crit-body">{inner}<h4>판정 규칙</h4><ul class="crit-rules">{rl}</ul></div></details>'

# 채택 4단계 (C1~C3 공통)
ADOPTION = ["실험", "얼리어답터", "확산", "주류"]
ADOPTION_DEF = {
    "실험": ("서비스가 나왔고 일부 가구가 시도한다.", "이용 가구 비율 10% 미만, 또는 출시·시범만 있고 이용 데이터 없음", "출시 발표, 시범 운영"),
    "얼리어답터": ("일부 가구가 직접 하거나 사던 방식 대신 이 서비스를 쓴다.", "10~25%", "이용 설문 (의향 설문만 있으면 이 단계까지)"),
    "확산": ("상당수 가구가 서비스와 기존 방식을 함께 쓴다.", "25~50%", "실제 이용 설문 또는 거래·가입 데이터"),
    "주류": ("서비스가 기본 경로이고 기존 방식은 예외다.", "50% 이상, 그리고 기존 방식 감소가 수치로 확인", "행동 데이터 필수 (이용 가구·거래·가입 비중)"),
}
def adoption_tip(lv):
    d, th, ev = ADOPTION_DEF[lv]
    return f"{lv} — {d} 기준: {th}. 근거: {ev}."
def adoption_block(title="판정 단계"):
    return (title, ["판정", "상태", "수치 기준", "인정하는 근거"],
            [[gauge(ADOPTION, k)] + [E(x) for x in v] for k, v in ADOPTION_DEF.items()])

# ---------------------------------------------------------------- Life Signals 판정 척도
# 1) 방향 × 속도 (F1·F2·T1·H1·N1) -------------------------------------------
DIRECTIONS = ["증가", "정체", "감소"]
SPEEDS = ["가속", "유지", "둔화"]
DIRECTION_DEF = {
    "증가": ("최근 3~5년 추세가 늘어나는 쪽이다.", "비율 지표는 연평균 +0.2%p 초과, 수·금액 지표는 연평균 +1% 초과(실질 기준)", "공식 통계 시계열 3개 시점 이상"),
    "정체": ("뚜렷한 방향이 없다.", "비율 지표 연평균 ±0.2%p 이내, 수·금액 지표 연평균 ±1% 이내", "공식 통계 시계열 3개 시점 이상"),
    "감소": ("최근 3~5년 추세가 줄어드는 쪽이다.", "비율 지표 연평균 -0.2%p 미만, 수·금액 지표 연평균 -1% 미만(실질 기준)", "공식 통계 시계열 3개 시점 이상"),
}
SPEED_DEF = {
    "가속": ("최근 변화가 추세보다 빠르다.", "최근 1년(또는 최근 조사 간격) 변화폭이 직전 3~5년 연평균 변화폭의 1.25배 초과", "최신 공표값과 직전 추세"),
    "유지": ("최근 변화가 추세와 비슷하다.", "0.75~1.25배", "최신 공표값과 직전 추세"),
    "둔화": ("최근 변화가 추세보다 느리거나 방향이 꺾이고 있다.", "0.75배 미만, 또는 최근 1년 방향이 추세와 반대", "최신 공표값과 직전 추세"),
}
DIR_RULES = [
    "방향은 최근 3~5년 추세로, 속도는 최근 1년 변화와 그 추세의 비교로 정한다.",
    "금액은 소비자물가로 실질화한 값을 우선한다. 명목만 있으면 '잠정'으로 둔다.",
    "5년 주기 조사(생활시간조사 등)는 직전 조사 대비 변화로 판정하고 속도는 직전 두 조사 간격과 비교한다.",
    "공식 통계가 없어 민간 조사·간접 근거로 판정한 칸은 '잠정'이며 점선으로 표시한다. 그 지표를 다음 조사에서 먼저 찾는다.",
    "판정은 딥리서치 회차에서만 바꾼다. 주간 조사에서 새 값이 나오면 지표 기록만 갱신하고 판정 영향은 '확인 필요'로 남긴다.",
]
def dir_block():
    rows = [[f'<span class="dir {"up" if k=="증가" else "down" if k=="감소" else "flat"}">{E(k)}</span>'] + [E(x) for x in v] for k, v in DIRECTION_DEF.items()]
    rows += [[f'<span class="own neutral">{E(k)}</span>'] + [E(x) for x in v] for k, v in SPEED_DEF.items()]
    return ("방향과 속도", ["판정", "뜻", "수치 기준", "인정하는 근거"], rows)

# 2) 주도 주체 지도 (T2) ------------------------------------------------------
OWNERS = ["가족", "공공", "시장", "기술"]
OWNER_CLS = {"가족": "neutral", "공공": "brand", "시장": "platform", "기술": "agent", "경합": "contest"}
OWNER_DEF = {
    "가족": ("가족 구성원이 시간·비용 대부분을 진다.", "돌봄 시간 또는 비용의 50% 이상이 가족 내부"),
    "공공": ("국가·지자체 제도가 주된 공급자다.", "제도 이용률이 대상 인구의 50% 이상, 또는 공공 재원이 비용의 과반"),
    "시장": ("민간 유료 서비스가 주된 공급자다.", "유료 서비스 이용률 또는 가구 지출이 가장 큰 몫"),
    "기술": ("기기·플랫폼이 돌봄의 일부를 대신한다.", "돌봄 목적 기기·앱 이용률 25% 이상 (그 미만은 '보조'로만 표기)"),
    "경합": ("두 주체의 몫이 비슷하다.", "상위 두 주체의 차이가 10%p 이내"),
}
OWNER_RULES = [
    "돌봄 대상(영유아·학령기 아동·노부모)마다 시간과 비용 기준으로 주도 주체를 정한다.",
    "시간 근거(생활시간조사)와 비용·이용 근거(보육·장기요양 통계, 가계동향)가 엇갈리면 '경합'으로 둔다.",
    "주체의 몫을 직접 재는 수치가 없으면 '잠정'으로 둔다.",
]
def owner_block():
    return ("주도 주체", ["주체", "뜻", "기준"], [[chip(k, OWNER_CLS[k])] + [E(x) for x in v] for k, v in OWNER_DEF.items()])

# 3) 영향 순위 (H2) -----------------------------------------------------------
RANK_RULES = [
    "순위는 영향받는 가구 규모(현재값)와 변화 속도를 함께 본다. 규모가 비슷하면 빠른 쪽이 위다.",
    "요인마다 그 요인이 바꾸는 공간·기능을 근거 기록과 함께 적는다.",
    "규모 또는 속도를 직접 재는 수치가 없으면 '잠정'으로 둔다.",
    "순위 변동은 직전 딥리서치 회차 대비로 표시한다.",
]
def rank_block():
    return ("순위 기준", ["항목", "뜻"], [[E("규모"), E("그 요인에 직접 노출된 가구 수 또는 비중")],
                                         [E("속도"), E("최근 1~3년 변화율(방향×속도 기준과 같음)")],
                                         [E("근거"), E("공식 통계 또는 A·B 출처 2개 이상. C 단독은 순위에 넣지 않는다")]])

# 4) 채택 4단계 (N2) — 위 ADOPTION·ADOPTION_DEF를 쓴다. 분모는 전체 가구.
ADOPTION_RULES = [
    "분모는 전체 가구(또는 해당 서비스가 필요한 가구로 명시한 경우 그 가구)다. '들어 본 적 있다'는 쓰지 않는다.",
    "이용 의향 설문만 있으면 '얼리어답터'를 넘지 않는다.",
    "'주류'는 이용률 50% 이상이면서 대체되는 기존 방식(직접 하기, 구매)이 줄어든 것이 수치로 확인돼야 한다.",
    "시장 규모·계정 수처럼 가구 이용률로 바로 바꿀 수 없는 근거로 판정한 칸은 '잠정'이다.",
]
