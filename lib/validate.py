"""질문별 build_records.py 공통 마무리: 수동 입력(patches.jsonl) 적용 → 규칙 검증 → records.jsonl 저장.

사용 (질문 폴더의 build_records.py 맨 끝):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
    from validate import finish
    finish(records, Path(__file__).parent)

검증 규칙
- 지표·사건: 원문 링크(url)와 출처 등급(A/B/C) 필수
- 지표: indicators.json에 있는 추적 지표 ID(indicator) 필수
- 해석: basis에 사실 기록(지표·사건) 1개 이상, direction은 강화|약화|중립
- 전망: due·method·basis 필수, basis에 사실 기록 1개 이상, forecast_status 값 확인
- 해석·전망은 원문 미확인(verified=False) 사실을 근거로 쓰지 않는다
- C등급 출처만 가진 사실은 verified=True일 수 없다 (C는 단독 근거 불가)
- ID 형식 <질문>-(M|E|I|F)-NNN, 중복 금지, 유형과 ID 글자 일치
- revisions의 kind는 lib/records.py KIND_ORDER만
"""
import json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from records import apply_patches, KIND_ORDER, GRADES

TYPE_LETTER = {"지표": "M", "사건": "E", "해석": "I", "전망": "F"}
STATUS = {"유효", "미확인", "대체됨", "반박됨"}
FSTATUS = {"진행 중", "적중", "빗나감", "만료"}


def load_indicators(folder):
    p = Path(folder) / "indicators.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def finish(records, folder, exit_on_error=True):
    folder = Path(folder)
    apply_patches(records, folder / "patches.jsonl")
    inds = load_indicators(folder)
    ind_ids = {i["id"] for i in inds}
    ids = [r["id"] for r in records]
    by = {r["id"]: r for r in records}
    facts = {r["id"] for r in records if r["type"] in ("지표", "사건")}
    errs = []
    if len(ids) != len(set(ids)):
        errs.append("중복 ID: " + ", ".join(k for k, v in Counter(ids).items() if v > 1))
    for r in records:
        rid, t = r["id"], r.get("type")
        if t not in TYPE_LETTER:
            errs.append(f"{rid}: 알 수 없는 유형 {t}"); continue
        m = re.fullmatch(r"([A-Z]\d+)-([MEIF])-(\d{3})", rid)
        if not m or m.group(2) != TYPE_LETTER[t] or m.group(1) != r.get("question"):
            errs.append(f"{rid}: ID 형식 또는 유형·질문 불일치")
        if r.get("status", "유효") not in STATUS:
            errs.append(f"{rid}: status 값 오류")
        if r.get("importance") not in (1, 2, 3):
            errs.append(f"{rid}: importance는 1~3")
        if not r.get("statement"):
            errs.append(f"{rid}: statement 없음")
        if t in ("지표", "사건"):
            srcs = r.get("sources") or []
            if not srcs or not all(s.get("url") for s in srcs):
                errs.append(f"{rid}: 원문 링크 없음")
            if any(s.get("grade") not in GRADES for s in srcs):
                errs.append(f"{rid}: 출처 등급 오류")
            if r.get("verified") and srcs and all(s.get("grade") == "C" for s in srcs):
                errs.append(f"{rid}: C등급 출처만으로 verified=True")
        if t == "지표":
            if ind_ids and r.get("indicator") not in ind_ids:
                errs.append(f"{rid}: 추적 지표 ID {r.get('indicator')}가 indicators.json에 없음")
            for f in ("value", "unit", "as_of"):
                if r.get(f) in (None, ""):
                    errs.append(f"{rid}: {f} 없음")
        if t == "사건" and not r.get("date"):
            errs.append(f"{rid}: date 없음")
        if t == "해석":
            if not set(r.get("basis", [])) & facts:
                errs.append(f"{rid}: 사실 기록 연결 없음")
            if r.get("direction") not in ("강화", "약화", "중립"):
                errs.append(f"{rid}: direction 값 오류")
        if t == "전망":
            for f in ("due", "method", "basis"):
                if not r.get(f):
                    errs.append(f"{rid}: {f} 없음")
            if not set(r.get("basis", [])) & facts:
                errs.append(f"{rid}: 해석에만 기대는 전망")
            if r.get("forecast_status", "진행 중") not in FSTATUS:
                errs.append(f"{rid}: forecast_status 값 오류")
            if r.get("scenario") and r["scenario"] not in ("낙관", "비관"):
                errs.append(f"{rid}: 시나리오 값 오류")
            for sp in r.get("signposts", []):
                if by.get(sp["id"], {}).get("type") != "전망":
                    errs.append(f"{rid}: 판정 신호 {sp['id']}가 세부 전망이 아님")
        for b in r.get("basis", []):
            if b not in by:
                errs.append(f"{rid}: 존재하지 않는 근거 {b}")
            elif t in ("해석", "전망") and b in facts and not by[b].get("verified"):
                errs.append(f"{rid}: 원문 미확인 기록 {b}을 근거로 씀")
        for v in r.get("revisions", []):
            if v.get("kind") not in KIND_ORDER:
                errs.append(f"{rid}: 변경 종류 {v.get('kind')} 오류")

    with open(folder / "records.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    filled = sorted({r.get("indicator") for r in records if r["type"] == "지표" and r.get("verified")})
    print("기록 수:", len(records), dict(Counter(r["type"] for r in records)))
    print("원문 미확인 사실:", [r["id"] for r in records if r["type"] in ("지표", "사건") and not r.get("verified")])
    print("확인 필요:", [r["id"] for r in records if r.get("check_flags")])
    print("값 채워진 추적 지표:", filled, f"{len(filled)}/{len(inds) or '?'}")
    print("검증 오류:", errs or "없음")
    if exit_on_error:
        sys.exit(1 if errs else 0)
    return errs
