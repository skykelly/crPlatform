"""records.jsonl → article_r1.html + signal_r1.json (<QNO> R1).
내용만 여기서 정하고 렌더링은 lib/article.py가 한다. 문장마다 근거 기록 번호를 단다.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from article import render

Q = "<QNO>"
CFG = dict(
    QNO=Q, CATEGORY="가구와 생애 전환", AREA="Household Composition", ROUND=1, DATE="2026-10-12", QVER="v1.0",
    TITLE="짧은 제목(질문을 명사형으로)",
    QUESTION="고정 질문 문장",
    ONE_LINE="2026년 10월 현재 … (한 줄 답 형식대로, 수치 포함 2~3문장)",
    ONE_LINE_BASIS=[f"{Q}-I-001"],
    ANSWER_ROWS=[("가장 빠른 변화", "…", [f"{Q}-M-001"])],
    NARRATIVE=[("해석 문단. 사실과 기준만.", [f"{Q}-M-001", f"{Q}-I-001"])],
    LENS=[("청년 1인", "…", [f"{Q}-M-001"]), ("신혼·무자녀 부부", "…", []), ("자녀양육 가구", "…", []),
          ("중장년", "…", []), ("고령 가구", "…", [])],
    SIZE_LENS=[("소형 (60㎡ 이하)", "…", []), ("중형 (60~100㎡)", "…", []), ("대형 (100㎡ 초과)", "…", [])],
    EVENTS_LEAD="이번 회차에 기록한 사건의 성격을 한두 문장으로.",
    FORECAST_TITLE="2027년 말까지 무엇이 갈림길인가",
    FORECAST_LEAD="두 시나리오의 갈림길을 한두 문장으로.",
    JUDGE={"scale": "dir", "title": "가구 유형별 방향×속도", "lead": "판정 방법 한두 문장.",
           "chip": "가장 빠른 변화: 1인가구 증가·유지", "gauge": "가구 유형 6종",
           "rows": [{"item": "1인가구", "value": "36.6% (2025)", "direction": "증가", "speed": "유지", "prov": False,
                     "note": "", "basis": [f"{Q}-M-001"]}]},
    METRICS_LEAD="추적 지표 확보 상황과 빈 지표를 다음에 어떻게 채울지.",
)
render(CFG, Path(__file__).parent)
