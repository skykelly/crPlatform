"""Inspect selected KOSIS table dimensions without storing data or a credential."""

import json
import os
import urllib.parse
import urllib.request

key = os.environ.get("KOSIS_API_KEY", "")
if not key:
    raise SystemExit("KOSIS_API_KEY missing")

tables = {
    "DT_1TS202001": ("2024", "F"),  # time-use: sleep and housework
    "DT_1PE2002": ("2020", "F"),  # tenure
    "DT_1L9U101": ("2025", "Y"),  # household expenditure
}
variants = (
    {"objL1": "00"},
    {"objL1": "ALL"},
    {"objL1": "00", "objL2": "ALL"},
    {"objL1": "ALL", "objL2": "ALL"},
    {"objL1": "ALL", "objL2": "ALL", "objL3": "ALL"},
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
            print(json.dumps({"table": table, "meta": kind,
                              "sample": result[:4] if isinstance(result, list) else result}, ensure_ascii=False))
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
                           ("C1", "C1_NM", "C2", "C2_NM", "C3", "C3_NM", "ITM_ID", "ITM_NM", "DT", "UNIT_NM")}
                          for row in result[:4]]
                print(json.dumps({"table": table, "variant": variant, "count": len(result), "sample": sample}, ensure_ascii=False))
                break
            message = str(result.get("errMsg", "")).replace(key, "[redacted]")
            print(json.dumps({"table": table, "variant": variant, "error": result.get("err"), "message": message}, ensure_ascii=False))
        except Exception as exc:
            print(f"{table} {variant}: {type(exc).__name__}")
