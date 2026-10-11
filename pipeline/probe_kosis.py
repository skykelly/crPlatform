"""Credential-safe diagnostic for the KOSIS table-selection API."""

import json
import os
import re
import urllib.parse
import urllib.request

from factbase import API

key = os.environ.get("KOSIS_API_KEY", "")
if not key:
    raise SystemExit("KOSIS_API_KEY missing")

base = dict(method="getList", apiKey=key, orgId="101", tblId="DT_1PL1502",
            objL1="00", itmId="T00", prdSe="Y", startPrdDe="2025",
            endPrdDe="2025", format="json")
variants = {
    "national-only": {},
    "all-geography": {"objL1": "ALL"},
    "second-dimension": {"objL2": "000"},
    "all-second": {"objL2": "ALL"},
    "jsonvd": {"jsonVD": "Y"},
    "recent-period": {"startPrdDe": None, "endPrdDe": None, "newEstPrdCnt": "1"},
    "all-item": {"itmId": "ALL"},
    "all-dimensions": {"objL1": "ALL", "objL2": "ALL", "itmId": "ALL"},
}

for label, changes in variants.items():
    params = {**base, **changes}
    params = {k: v for k, v in params.items() if v is not None}
    request = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "crPlatform-factbase/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
            if isinstance(parsed, list):
                print(f"{label}: rows={len(parsed)} fields={sorted(parsed[0])[:12] if parsed else []}")
            else:
                print(f"{label}: JSON object error={parsed.get('err', 'unknown')}")
        except json.JSONDecodeError:
            code = re.search(r'err["\s]*:["\s]*([0-9A-Za-z_-]+)', body)
            print(f"{label}: non-JSON error={code.group(1) if code else 'unknown'}")
    except Exception as exc:
        print(f"{label}: request error={type(exc).__name__}")
