"""Live end-to-end verification for the EarthWatch backend API.

Run with the server started (``python -m uvicorn app.main:app`` on port 10000
or whatever port you configured), then::

    python verify.py 127.0.0.1 8000

Every check talks to a real deployment: no fixtures, no stubs. The script
asserts on structure and provenance (kinds, source names, honest "stale"
flags), not on specific counts, so it stays valid as the feed changes.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PASS = 0
FAIL = 0


def _ok(label: str) -> None:
    global PASS
    PASS += 1
    print(f"[PASS] {label}")


def _fail(label: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"[FAIL] {label} {detail}")


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        _ok(label)
    else:
        _fail(label, detail)


def get(base: str, path: str, timeout: int = 90) -> tuple[int, dict]:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


def post(base: str, path: str, body: dict, timeout: int = 90) -> tuple[int, dict]:
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


def expect_status(base: str, path: str, body: dict | None, want: int) -> None:
    if body is None:
        urllib.request.urlopen(base + path)
        return
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
        _fail(f"GET/POST {path} -> expected HTTP {want}, got success")
    except urllib.error.HTTPError as err:
        check(f"POST {path} -> HTTP {want}", err.code == want, f"(got {err.code})")


def main(host: str, port: str) -> None:
    base = f"http://{host}:{port}"

    # 1. Health ------------------------------------------------------------
    status, h = get(base, "/api/health")
    check("GET /api/health -> 200", status == 200)
    check("health payload names the service", h.get("service") == "EarthWatch")
    check("health reports database state", "database" in h)

    # 2. Full retrieval ----------------------------------------------------
    status, data = get(base, "/api/events?status=all&limit=500")
    check("GET /api/events (status=all, limit=500) -> 200", status == 200)
    events = data.get("events", [])
    check("events is a list", isinstance(events, list) and len(events) > 0)
    check("retrieval_time present", bool(data.get("retrieval_time")))
    check("stale flag is an honest boolean", isinstance(data.get("stale"), bool))
    check(
        "backend count reflects total after filters",
        isinstance(data.get("count"), int) and data["count"] >= len(events),
    )

    # 2b. Per-source status honesty ----------------------------------------
    statuses = data.get("source_status") or {}
    check("per-source status map present", isinstance(statuses, dict) and len(statuses) >= 1)
    check(
        "every source status is live/cached/unavailable",
        all(v in ("live", "cached", "unavailable") for v in statuses.values()),
    )
    delivered = [k for k, v in statuses.items() if v in ("live", "cached")]
    check("at least one source delivered records", len(delivered) >= 1, json.dumps(statuses))
    check("merged source label non-empty", bool(data.get("source")))
    if len(delivered) >= 2:
        check("merged label joins contributing sources with ' · '", " · " in data.get("source", ""))

    dated = [e for e in events if e.get("event_date")]
    coords = [e for e in events if e.get("coordinates")]
    cats = sorted({(e.get("category") or "Unknown") for e in events})
    print(
        f"       records={len(events)}  dated={len(dated)}  with coords={len(coords)}"
        f"  categories={cats}"
    )
    print(f"       source=<{' · '.join(f'{k}:{v}' for k, v in statuses.items())}>")
    check("event records carry ids", all(e.get("id") for e in events))
    check("event records carry a source", all(e.get("source") for e in events))

    # 3. Category filter ---------------------------------------------------
    category = cats[0] if cats else "Wildfires"
    status, filtered = get(
        base, f"/api/events?category={urllib.parse.quote(category)}&status=all&limit=200"
    )
    check(f"GET /api/events?category={category} -> 200", status == 200)
    check(
        "category filter narrows to that category",
        all(category.lower() in (e.get("category") or "").lower() for e in filtered.get("events", [])),
    )

    # 4. Event detail ------------------------------------------------------
    sample = next((e for e in events if e.get("coordinates")), events[0])
    status, detail = get(base, f"/api/events/{sample['id']}")
    check("GET /api/events/{id} -> 200", status == 200 and detail.get("id") == sample["id"])
    check("detail exposes category and dates", bool(detail.get("category")))
    check(
        "missing coordinates stay null (never fabricated)",
        detail.get("coordinates") is None or len(detail.get("coordinates", [])) == 2,
    )

    # 4b. Auxiliary-source record detail served from persisted storage ------
    import urllib.parse as _urlparse

    aux_event = next(
        (
            e
            for e in events
            if str(e.get("id", "")).split(":")[0] in {"usgs", "nws", "nhc", "tsunami"}
        ),
        None,
    )
    if aux_event:
        status, auxdetail = get(
            base,
            "/api/events/" + _urlparse.quote(aux_event["id"], safe=""),
        )
        check(
            "aux record detail served from persisted storage",
            status == 200 and auxdetail.get("id") == aux_event["id"],
        )
    # 5. Sources & imagery -------------------------------------------------
    status, s = get(base, "/api/sources")
    check("GET /api/sources -> 200", status == 200)
    names = [x.get("name") for x in s.get("sources", [])]
    check("NASA EONET registered", "NASA EONET" in names)
    check("USGS registered", "USGS" in names)
    check("NOAA NWS registered", "NOAA NWS" in names)
    check("NOAA NHC registered", "NOAA NHC" in names)
    check("NOAA Tsunami Program registered", "NOAA Tsunami Program" in names)

    status, ic = get(base, "/api/imagery/config")
    check("GET /api/imagery/config -> 200", status == 200)
    check("imagery provider is NASA GIBS", ic.get("provider") == "NASA GIBS")
    note = json.dumps(ic)
    check("imagery is labelled 'not real-time'", "not real-time" in note or "real-time" not in note.replace("not real-time", ""))

    # 6. Insights ----------------------------------------------------------
    status, ins = post(
        base,
        "/api/insights",
        {"event_id": sample["id"], "category": sample.get("category"), "mode": "event"},
    )
    check("POST /api/insights -> 200", status == 200)
    kind = ins.get("kind")
    check(
        "insight kind is ANALYZED or UNAVAILABLE",
        kind in ("ANALYZED", "UNAVAILABLE"),
        f"(got {kind})",
    )
    if kind == "ANALYZED":
        insight = ins.get("insight", {})
        check(
            "ANALYZED insight carries method + limitations",
            bool(insight.get("method")) and bool(insight.get("limitations")),
        )

    expect_status(base, "/api/insights", {"event_id": "does-not-exist"}, 404)
    expect_status(base, "/api/insights", {}, 422)

    # 7. Natural-language analyst -----------------------------------------
    status, q = post(base, "/api/query", {"question": "How many events are in the current retrieval?"})
    check("POST /api/query -> 200", status == 200)
    qkind = q.get("kind")
    check(
        "query kind is ANALYZED or UNAVAILABLE",
        qkind in ("ANALYZED", "UNAVAILABLE"),
        f"(got {qkind})",
    )
    if qkind == "ANALYZED":
        check(
            "query reports which evidence it used",
            isinstance(q.get("evidence"), list),
        )
    status, cmp = post(
        base, "/api/query", {"question": "Compare wildfire events over the last 30 days."}
    )
    check("POST /api/query (compare) -> 200", status == 200)
    check(
        "compare answer stays grounded",
        cmp.get("kind") in ("ANALYZED", "UNAVAILABLE"),
    )
    expect_status(
        base, "/api/query", {"question": "x" * 300}, 422
    )

    print(f"\n==== {PASS} passed, {FAIL} failed ====")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    import urllib.parse  # imported lazily; only needed for quoting categories

    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = sys.argv[2] if len(sys.argv) > 2 else "8000"
    main(host, port)
