"""Inspect selected KOSIS table dimensions without storing data or a credential."""

import json
import os
import urllib.parse
import urllib.request

key = os.environ.get("KOSIS_API_KEY", "")
if not key:
    raise SystemExit("KOSIS_API_KEY missing")

tables = {"DT_1TS202001": ("2024", "F")}
variants = (
    {"objL1": "A0", "objL2": "S0", "objL3": "C1", "objL4": "ALL"},
    {"objL1": "00"},
    {"objL1": "ALL"},
    {"objL1": "00", "objL2": "ALL"},
    {"objL1": "ALL", "objL2": "ALL"},
    {"objL1": "ALL", "objL2": "ALL", "objL3": "ALL"},
    {"objL1": "ALL", "objL2": "ALL", "objL3": "ALL", "objL4": "ALL"},
    {"objL1": "ALL", "objL2": "ALL", "objL3": "ALL", "objL4": "ALL", "objL5": "ALL"},
)

for table, (year, period) in tables.items():
    for kind in ("PRD", "OBJ", "ITM"):
        meta = {"method": "getMeta", "type": kind, "apiKey": key, "orgId": "101",
                "tblId": table, "format": "json", "jsonVD": "Y"}
        request = urllib.request.Request(
            "https://kosis.kr/openapi/statisticsData.do?" + urllib.parse.urlencode(meta),
            headers={"User-Agent": "crPlatform-factbase/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.load(response)
            if kind == "ITM" and isinstance(result, list):
                groups = {}
                for row in result:
                    groups.setdefault(row.get("OBJ_ID", ""), []).append((row.get("ITM_ID"), row.get("ITM_NM")))
                sample = {group: {"count": len(items), "sample": items[:7],
                                  "matched": [item for item in items if any(term in str(item[1]) for term in
                                              ("수면", "가정관리", "음식준비", "청소", "가사노동", "가족돌봄"))][:35]}
                          for group, items in groups.items()}
            else:
                sample = result[:4] if isinstance(result, list) else result
            print(json.dumps({"table": table, "meta": kind, "sample": sample}, ensure_ascii=False))
        except Exception as exc:
            print(f"{table} meta {kind}: {type(exc).__name__}")
    for variant in variants:
        params = {"method": "getList", "apiKey": key, "orgId": "101", "tblId": table,
                  "itmId": "ALL", "prdSe": period, "startPrdDe": year,
                  "endPrdDe": year, "format": "json", "jsonVD": "Y", **variant}
        request = urllib.request.Request(
            "https://kosis.kr/openapi/Param/statisticsParameterData.do?" + urllib.parse.urlencode(params),
            headers={"User-Agent": "crPlatform-factbase/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
            result = json.loads(body)
            if isinstance(result, list):
                sample = [{field: row.get(field) for field in
                           ("C1", "C1_NM", "C2", "C2_NM", "C3", "C3_NM", "C4", "C4_NM", "ITM_ID", "ITM_NM", "DT", "UNIT_NM")}
                          for row in result[:4]]
                matching = [{"code": row.get("C1"), "name": row.get("C1_NM"), "value": row.get("DT")}
                            for row in result if table == "DT_1L9U101" and row.get("ITM_ID") == "T110"
                            and any(term in str(row.get("C1_NM", "")) for term in ("가전", "가구", "수선", "가사서비스", "광열"))]
                print(json.dumps({"table": table, "variant": variant, "count": len(result),
                                  "sample": sample, "matching": matching[:50]}, ensure_ascii=False))
                break
            message = str(result.get("errMsg", "")).replace(key, "[redacted]")
            print(json.dumps({"table": table, "variant": variant, "error": result.get("err"), "message": message}, ensure_ascii=False))
        except Exception as exc:
            print(f"{table} {variant}: {type(exc).__name__}")
