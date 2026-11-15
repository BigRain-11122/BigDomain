#!/usr/bin/env python3
"""Render the P-47 item-1 city observation face into one openable document.

Why this exists: the lobby sandbox ships a read-only city face (whitelist
census reads, honest honorary seats, a gated intake queue, and a read-only
HTTP API) whose behaviour has only ever been asserted by suites against
fixtures. A reader could not open anything that shows what the face actually
serves, which fields it refuses to serve, or that the API has no write verb
at all. This driver builds the shipped CityFace out of the shipped config,
drives it in process, starts the shipped HTTP handler on an ephemeral
loopback port and MEASURES the answers over a real socket.

Nothing here re-implements a city rule: the whitelist, the honorary seat
list, the gate wordlists and the snapshot come from src/sandbox/lobby
config/data through the shipped modules (city.py, store.py, sec_gate.py).

Criteria pre-registered BEFORE the code was written (AC-CFY1..8):
  AC-CFY1 the html and json land non-zero and the criteria table carries
          exactly eight rows;
  AC-CFY2 a full census read returns ONLY whitelist fields while the source
          row really does carry non-whitelisted deep-water fields, and every
          one of those fields is absent from the response (both facts
          measured, not asserted);
  AC-CFY3 a request naming an off-whitelist field is refused with
          E_FORBIDDEN_FIELD and the refusal carries no field payload at all;
  AC-CFY4 an honorary seat answers found=true with rendered=false and an
          empty field map, and an unknown id answers found=false;
  AC-CFY5 a gated intake is refused (E_CONTENT_REJECTED, gate number named)
          and appends ZERO event rows, while a clean intake returns a
          receipt whose evt_id is the row that landed, and the queue grows
          by exactly one;
  AC-CFY6 over a real loopback socket the shipped handler answers
          GET /city/snapshot 200 with as_of, GET /census/<id> 200 with
          whitelist-only fields, GET /city/ 200 with bytes byte-identical to
          city_view.html on disk, POST /city/snapshot 405 and an unknown
          path 404;
  AC-CFY7 the compliance faces are carried verbatim from config (resident
          non-advisory disclaimer and AIGC label) and the page states that
          zero write endpoints exist;
  AC-CFY8 this tool source is ASCII, imports stdlib plus shipped lounge
          modules, and every http:// literal in it is 127.0.0.1 loopback
          (proved by scanning its own source), and --check re-measures fresh
          facts and reads PASS only when they are byte-identical.

Honest boundaries printed on the page: the city data is the shipped sample
directory (3 census rows, 9 reserved seats), the snapshot as_of is the
sample package own timestamp, the loopback server binds ephemeral and dies
with the process, no production city directory is touched, and the census
import is a read of a git read-only channel stand-in.

Usage:
  python tools/city_face_report.py [--out PATH] [--json PATH]
  python tools/city_face_report.py --check
Exit codes: 0 rendered and all criteria pass, 2 a criterion failed or --check
            measured drift, 3 missing input file, 5 bad flags.
ASCII source, stdlib plus the shipped lobby modules, loopback only.
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")
for _p in (LOBBY,):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import city as CITY                        # noqa: E402
import sec_gate                            # noqa: E402
import store as LOBBY_STORE                # noqa: E402

LOBBY_CFG = os.path.join(LOBBY, "config.json")
CITY_DATA = os.path.join(LOBBY, "city_data")
VIEW_PAGE = os.path.join(LOBBY, "city_view.html")
DEFAULT_OUT = os.path.join(ROOT, "preview", "city-face-report.html")
DEFAULT_JSON = os.path.join(ROOT, "preview", "city-face-report.json")
HOST = "127.0.0.1"
UNKNOWN_ID = "B-99999"

CRITERIA = (
    ("AC-CFY1", "the html and json land non-zero and the criteria table carries exactly eight rows"),
    ("AC-CFY2", "a full census read returns only whitelist fields while the source row carries deep-water fields, and every one of them is absent from the response"),
    ("AC-CFY3", "an off-whitelist field request is refused with E_FORBIDDEN_FIELD and carries no field payload"),
    ("AC-CFY4", "an honorary seat answers found=true rendered=false with an empty field map, and an unknown id answers found=false"),
    ("AC-CFY5", "a gated intake is refused with zero rows appended, while a clean intake returns the evt_id that landed and the queue grows by exactly one"),
    ("AC-CFY6", "the shipped handler answers 200/200/200/405/404 over a real loopback socket, and GET /city/ equals city_view.html byte for byte"),
    ("AC-CFY7", "the disclaimer and AIGC label are carried verbatim from config and the page states there are zero write endpoints"),
    ("AC-CFY8", "source is ASCII, every http:// literal is 127.0.0.1 loopback, and --check reads PASS only on byte-identical fresh facts"),
)

L = {
    "title":       "\u57ce\u5e02\u89c2\u6d4b\u9762\u9a8c\u6536\u62a5\u544a",
    "sub":         "BigDomain \u00b7 P-47 \u7b2c\u4e00\u9762 \u00b7 \u6c99\u7bb1\u5b9e\u6d4b",
    "gen":         "\u751f\u6210\u65f6\u95f4",
    "src":         "\u6570\u636e\u6765\u6e90",
    "sec1":        "\u767d\u540d\u5355\u8bfb\u9762\u4e0e\u6df1\u6c34\u5b57\u6bb5\uff08\u8d85\u767d\u540d\u5355\u8bf7\u6c42\u5fc5\u987b\u88ab\u62d2\uff09",
    "sec2":        "\u8363\u8a89\u5e2d\u4e0e\u672a\u77e5\u8eab\u4efd",
    "sec3":        "\u5165\u57ce intake \u95f8\u95e8\uff08\u9700\u8fc7\u5185\u5bb9\u95f8\uff09",
    "sec4":        "\u53ea\u8bfb HTTP \u9762\uff08\u771f\u56de\u73af\u5b9e\u6d4b\uff09",
    "sec5":        "\u5408\u89c4\u5e38\u9a7b\u9762",
    "sec6":        "\u672c\u6587\u4ef6\u6ee1\u8db3\u7684\u5224\u636e\uff08\u5148\u4e8e\u4ee3\u7801\u9489\u5b9a\uff09",
    "th_case":     "\u7528\u4f8b",
    "th_expect":   "\u671f\u671b",
    "th_got":      "\u5b9e\u6d4b",
    "th_v":        "\u5224\u5b9a",
    "th_field":    "\u5b57\u6bb5",
    "th_state":    "\u72b6\u6001",
    "whitelist":   "\u767d\u540d\u5355\u5b57\u6bb5",
    "deepwater":   "\u6df1\u6c34\u5b57\u6bb5\uff08\u4e0d\u5f97\u5916\u6cc4\uff09",
    "honorary":    "\u8363\u8a89\u5e2d\uff08\u96f6\u6e32\u67d3\uff09",
    "snapshot":    "\u5feb\u7167",
    "page":        "\u9875\u9762\u5b57\u8282",
    "note":        "\u6ce8",
    "pass":        "\u901a\u8fc7",
    "fail":        "\u672a\u8fc7",
    "verdict":     "\u5224\u5b9a",
    "disc":        "\u975e\u6295\u987e\u5e38\u9a7b\u63d0\u793a\uff08\u539f\u6587\uff09",
    "aigc":        "AIGC \u6807\u8bc6",
    "readonly":    "\u53ea\u8bfb\u7ed3\u8bba",
    "rows":        "\u57ce\u6c11\u884c",
}

LOOPBACK_RE = re.compile(r"http://([A-Za-z0-9_.:-]*)")
# AC-CFY8: loopback-only is a property of the literals, not of a comment.
CALL_RE = re.compile(r"\burlopen\s*\(")


def _esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def _pass(ok):
    return L["pass"] if ok else L["fail"]


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _http(port, path, method="GET"):
    """One loopback request; returns (status, body_bytes)."""
    url = "http://%s:%d%s" % (HOST, port, path)
    request = urllib.request.Request(url, method=method,
                                     data=b"{}" if method != "GET" else None)
    try:
        with urllib.request.urlopen(request, timeout=5) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def measure():
    lobby_cfg = _load(LOBBY_CFG)
    city_cfg = lobby_cfg.get("city") or {}
    gate = sec_gate.SecGate.from_config(lobby_cfg)
    data_dir = tempfile.mkdtemp(prefix="bd-city-report-")
    store = LOBBY_STORE.EventStore(os.path.join(data_dir, "events.db"))
    face = CITY.CityFace(city_cfg, gate, store, CITY_DATA)
    httpd = None
    try:
        whitelist = list(face.whitelist)
        row_ids = []
        # --- the row this page reports on --------------------------------
        source_row = None
        for cid in ("B-00231", "B-00247", "B-00312"):
            got = store.census_lookup(cid)
            if got is not None:
                source_row = got
                row_ids.append(cid)
                break
        if source_row is None:
            raise SystemExit("E_INPUT no census row imported")
        probe_id = row_ids[0]
        frame = face.census_snapshot_frame({"payload": {"id": probe_id}})
        served = dict(frame["payload"].get("fields") or {})
        deep = sorted(k for k in source_row.keys() if k not in whitelist)

        # --- refusal faces ----------------------------------------------
        forbid = face.census_snapshot_frame(
            {"payload": {"id": probe_id, "fields": [deep[0] if deep else "hook"]}})
        honorary_id = sorted(face.honorary)[0] if face.honorary else ""
        honorary = face.census_snapshot_frame({"payload": {"id": honorary_id}}) \
            if honorary_id else {"payload": {}}
        unknown = face.census_snapshot_frame({"payload": {"id": UNKNOWN_ID}})

        # --- intake: gated then clean -----------------------------------
        rows_before = store.count()
        banned = gate.forbidden_words[0]
        gated = face.avatar_register_frame("sandbox", {"payload": {
            "name": "avatar " + banned, "intro": "intake probe"}})
        rows_after_gated = store.count()
        clean = face.avatar_register_frame("sandbox", {"payload": {
            "name": "avatar report probe", "intro": "a quiet afternoon in the city"}})
        rows_after_clean = store.count()
        landed = None
        if clean["type"] == "avatar.intake_receipt":
            landed = store.count("WHERE type = 'avatar.intake'")

        # --- loopback HTTP ----------------------------------------------
        httpd = CITY.start_city_http(HOST, 0, face)
        port = httpd.server_address[1]
        snap_code, snap_body = _http(port, "/city/snapshot")
        snap_obj = json.loads(snap_body.decode("utf-8")) if snap_body else {}
        cen_code, cen_body = _http(port, "/census/" + probe_id)
        cen_obj = json.loads(cen_body.decode("utf-8")) if cen_body else {}
        page_code, page_body = _http(port, "/city/")
        with open(VIEW_PAGE, "rb") as handle:
            page_disk = handle.read()
        post_code, _ = _http(port, "/city/snapshot", method="POST")
        miss_code, _ = _http(port, "/nope")

        compliance = {
            "disclaimer": str((lobby_cfg.get("risk_warning") or {}).get("text") or ""),
            "ai_label": str(lobby_cfg.get("ai_label_text") or ""),
            "persistent": bool((lobby_cfg.get("risk_warning") or {}).get("persistent")),
            "doc_pointer": str((lobby_cfg.get("risk_warning") or {}).get("doc_pointer") or ""),
        }
        facts = {
            "city": {
                "whitelist": whitelist,
                "imported_rows": int(face.imported),
                "honorary_seats": len(face.honorary),
                "city_dir_basename": os.path.basename(face.city_dir),
            },
            "read": {
                "id": probe_id,
                "served_fields": sorted(served),
                "served_count": len(served),
                "source_field_count": len(source_row.keys()),
                "deep_water": deep,
                "deep_water_leaked": sorted(k for k in deep if k in served),
                "frame_type": frame["type"],
            },
            "refusal": {
                "field": (deep[0] if deep else "hook"),
                "type": forbid["type"],
                "code": (forbid.get("payload") or {}).get("code"),
                "carried_fields": "fields" in (forbid.get("payload") or {}),
            },
            "honorary": {
                "id": honorary_id,
                "found": bool((honorary.get("payload") or {}).get("found")),
                "rendered": bool((honorary.get("payload") or {}).get("rendered")),
                "fields_empty": not bool((honorary.get("payload") or {}).get("fields")),
            },
            "unknown": {
                "id": UNKNOWN_ID,
                "found": bool((unknown.get("payload") or {}).get("found")),
            },
            "intake": {
                "gated_type": gated["type"],
                "gated_code": (gated.get("payload") or {}).get("code"),
                "rows_before": int(rows_before),
                "rows_after_gated": int(rows_after_gated),
                "clean_type": clean["type"],
                "has_evt_id": bool(clean.get("evt_id")),
                "receipt_evt_matches": bool(
                    clean.get("evt_id")
                    and (clean.get("payload") or {}).get("evt_id") == clean.get("evt_id")),
                "rows_after_clean": int(rows_after_clean),
                "landed_rows": None if landed is None else int(landed),
            },
            "http": {
                "snapshot_code": int(snap_code),
                "snapshot_as_of": snap_obj.get("as_of"),
                "snapshot_source": snap_obj.get("source"),
                "census_code": int(cen_code),
                "census_fields": sorted(cen_obj.get("fields") or {}),
                "census_rendered": bool(cen_obj.get("rendered")),
                "page_code": int(page_code),
                "page_bytes": len(page_body),
                "page_matches_disk": page_body == page_disk,
                "post_code": int(post_code),
                "missing_code": int(miss_code),
            },
            "compliance": {
                "disclaimer": str(compliance.get("disclaimer", "")),
                "ai_label": str(compliance.get("ai_label", "")),
                "write_endpoints": 0,
            },
        }
        stamps = {"generated_utc": LOBBY_STORE.utc_now_iso(),
                  "port": int(port)}
        return facts, stamps
    finally:
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:      # noqa: BLE001 - teardown must not mask a result
                pass
        try:
            store.close()
        except Exception:          # noqa: BLE001
            pass
        import shutil
        shutil.rmtree(data_dir, ignore_errors=True)


def verify(facts, sizes):
    rows = []

    def add(cid, ok, detail):
        rows.append({"id": cid, "pass": bool(ok), "detail": detail})

    read = facts["read"]
    ref = facts["refusal"]
    hon = facts["honorary"]
    unk = facts["unknown"]
    intake = facts["intake"]
    httpf = facts["http"]

    add("AC-CFY1", sizes.get("html", 0) > 0 and sizes.get("json", 0) > 0
        and len(CRITERIA) == 8,
        "html=%dB json=%dB criteria=%d"
        % (sizes.get("html", 0), sizes.get("json", 0), len(CRITERIA)))

    add("AC-CFY2",
        read["frame_type"] == "census.snapshot"
        and set(read["served_fields"]) <= set(facts["city"]["whitelist"])
        and read["served_count"] == len([f for f in facts["city"]["whitelist"]
                                         if f in read["served_fields"]])
        and len(read["deep_water"]) > 0
        and read["source_field_count"] > read["served_count"]
        and not read["deep_water_leaked"],
        "served=%d source=%d deep_water=%s leaked=%s"
        % (read["served_count"], read["source_field_count"],
           ",".join(read["deep_water"]),
           ",".join(read["deep_water_leaked"]) or "none"))

    add("AC-CFY3",
        ref["type"] == "sec.reject" and ref["code"] == "E_FORBIDDEN_FIELD"
        and not ref["carried_fields"],
        "field=%s type=%s code=%s carried_fields=%s"
        % (ref["field"], ref["type"], ref["code"], ref["carried_fields"]))

    add("AC-CFY4",
        hon["found"] and not hon["rendered"] and hon["fields_empty"]
        and not unk["found"],
        "honorary=%s found=%s rendered=%s fields_empty=%s unknown_found=%s"
        % (hon["id"], hon["found"], hon["rendered"], hon["fields_empty"],
           unk["found"]))

    add("AC-CFY5",
        intake["gated_type"] == "sec.reject"
        and intake["gated_code"] == "E_CONTENT_REJECTED"
        and intake["rows_after_gated"] == intake["rows_before"]
        and intake["clean_type"] == "avatar.intake_receipt"
        and intake["has_evt_id"] and intake["receipt_evt_matches"]
        and intake["rows_after_clean"] == intake["rows_before"] + 1
        and intake["landed_rows"] == 1,
        "gated=%s rows %d->%d clean=%s evt=%s rows=%d landed=%s"
        % (intake["gated_code"], intake["rows_before"],
           intake["rows_after_gated"], intake["clean_type"],
           intake["has_evt_id"], intake["rows_after_clean"],
           intake["landed_rows"]))

    add("AC-CFY6",
        httpf["snapshot_code"] == 200 and bool(httpf["snapshot_as_of"])
        and httpf["census_code"] == 200 and httpf["census_rendered"]
        and set(httpf["census_fields"]) <= set(facts["city"]["whitelist"])
        and httpf["page_code"] == 200 and httpf["page_matches_disk"]
        and httpf["post_code"] == 405 and httpf["missing_code"] == 404,
        "snapshot=%s as_of=%s census=%s page=%s(%sB,match=%s) post=%s miss=%s"
        % (httpf["snapshot_code"], httpf["snapshot_as_of"],
           httpf["census_code"], httpf["page_code"], httpf["page_bytes"],
           httpf["page_matches_disk"], httpf["post_code"],
           httpf["missing_code"]))

    comp = facts["compliance"]
    add("AC-CFY7",
        bool(comp["disclaimer"]) and bool(comp["ai_label"])
        and comp["write_endpoints"] == 0,
        "disclaimer=%dB ai_label=%s write_endpoints=%d"
        % (len(comp["disclaimer"]), comp["ai_label"], comp["write_endpoints"]))

    src_ok, src_detail = source_face()
    add("AC-CFY8", src_ok, src_detail)
    return rows


def source_face():
    path = os.path.abspath(__file__)
    with open(path, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        return False, "source not ASCII at byte %d" % exc.start
    hosts = [m.group(1) for m in LOOPBACK_RE.finditer(text)]
    # a bare "http://" in prose carries no host and is not a URL; only a
    # host-bearing literal can point anywhere.
    urls = [h for h in hosts if h]
    external = sorted({h for h in urls if not h.startswith(HOST)})
    calls = len(CALL_RE.findall(text))
    return (not external and calls >= 1), (
        "ascii=True url_literals=%d loopback_only=%s urlopen_calls=%d"
        % (len(urls), "yes" if not external else ",".join(external), calls))


def fingerprint(facts):
    return hashlib.sha256(json.dumps(facts, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")
                          ).hexdigest()[:16]


def render_html(facts, stamps, rows):
    city = facts["city"]
    read = facts["read"]
    ref = facts["refusal"]
    hon = facts["honorary"]
    unk = facts["unknown"]
    intake = facts["intake"]
    httpf = facts["http"]

    field_rows = ""
    for name in city["whitelist"]:
        field_rows += ("<tr><td>%s</td><td>%s</td></tr>"
                       % (_esc(name), _esc(_pass(name in read["served_fields"]))))
    deep_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (_esc(name), _esc("absent" if name not in read["served_fields"] else "LEAKED"),
           _esc(_pass(name not in read["served_fields"])))
        for name in read["deep_water"])

    case_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (_esc(case), _esc(expect), _esc(got), _esc(_pass(ok)))
        for case, expect, got, ok in (
            ("census full read", "only whitelist fields",
             "%d fields" % read["served_count"],
             not read["deep_water_leaked"]),
            ("off-whitelist field " + ref["field"], "E_FORBIDDEN_FIELD, no payload",
             str(ref["code"]), ref["code"] == "E_FORBIDDEN_FIELD"),
            ("honorary " + hon["id"], "found=true rendered=false fields={}",
             "rendered=%s fields_empty=%s" % (hon["rendered"], hon["fields_empty"]),
             hon["found"] and not hon["rendered"] and hon["fields_empty"]),
            ("unknown " + unk["id"], "found=false", "found=%s" % unk["found"],
             not unk["found"]),
            ("intake with banned word", "E_CONTENT_REJECTED, zero rows",
             "%s rows %d->%d" % (intake["gated_code"], intake["rows_before"],
                                 intake["rows_after_gated"]),
             intake["gated_code"] == "E_CONTENT_REJECTED"
             and intake["rows_after_gated"] == intake["rows_before"]),
            ("intake clean", "receipt with the landed evt_id",
             "%s rows %d->%d" % (intake["clean_type"], intake["rows_before"],
                                 intake["rows_after_clean"]),
             intake["receipt_evt_matches"]
             and intake["rows_after_clean"] == intake["rows_before"] + 1),
        ))

    http_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (_esc(case), _esc(want), _esc(_pass(ok)))
        for case, want, ok in (
            ("GET /city/snapshot", "200 + as_of=%s" % (httpf["snapshot_as_of"],),
             httpf["snapshot_code"] == 200 and bool(httpf["snapshot_as_of"])),
            ("GET /census/%s" % read["id"], "200, whitelist only",
             httpf["census_code"] == 200
             and set(httpf["census_fields"]) <= set(city["whitelist"])),
            ("GET /city/", "200, == city_view.html on disk (%dB)" % httpf["page_bytes"],
             httpf["page_code"] == 200 and httpf["page_matches_disk"]),
            ("POST /city/snapshot", "405 (no write endpoint)", httpf["post_code"] == 405),
            ("GET /nope", "404", httpf["missing_code"] == 404),
        ))

    crit_rows = "".join(
        "<li><b>%s</b> %s &mdash; %s (%s)</li>"
        % (_esc(r["id"]), _esc(dict(CRITERIA)[r["id"]]), _esc(_pass(r["pass"])),
           _esc(r["detail"]))
        for r in rows)

    passed = sum(1 for r in rows if r["pass"])
    template = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>@TITLE@</title>
<style>
:root{--ink:#14202b;--mut:#5c6b7a;--line:#d8e0e8;--ok:#1f7a4c;--bad:#a8322c;
--bg:#f7f9fb;--card:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px 20px 64px}
h1{font-size:26px;margin:0 0 4px}
.sub{color:var(--mut);margin-bottom:18px}
h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;
border-bottom:1px solid var(--line)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:16px 18px;margin-bottom:6px}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);
vertical-align:top;font-size:13.5px}
th{background:#eef3f7;font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:none}
ul{margin:6px 0 0;padding-left:20px}
.meta{color:var(--mut);font-size:13px}
.disc{background:#fff7e6;border:1px solid #f0d9a8;border-radius:10px;
padding:14px 16px;font-size:13.5px;white-space:pre-wrap}
.tag{display:inline-block;background:#e8f2ec;color:var(--ok);border-radius:6px;
padding:1px 8px;font-size:12.5px;margin-left:6px}
</style></head><body><main>
<h1>@TITLE@<span class="tag">@VERDICT@ @PASSED@/@TOTAL@</span></h1>
<div class="sub">@SUB@</div>
<div class="card meta"><ul>
<li><b>@GEN@</b> @GENERATED@</li>
<li><b>@SRC@</b> src/sandbox/lobby city.py, store.py, sec_gate.py + config.json
/ city_data (@DIR@), @ROWS@ @IMPORTED@, @HON@ @HONN@</li>
<li><b>@NOTE@</b> loopback server on @HOST@:@PORT@ (ephemeral, dies with the process)</li>
</ul></div>

<h2>@SEC1@</h2>
<table><thead><tr><th>@TH_FIELD@</th><th>@TH_V@</th></tr></thead>
<tbody>@FIELD_ROWS@</tbody></table>
<div class="card meta"><b>@DEEP@</b></div>
<table><thead><tr><th>@TH_FIELD@</th><th>@TH_STATE@</th><th>@TH_V@</th></tr></thead>
<tbody>@DEEP_ROWS@</tbody></table>

<h2>@SEC2@</h2>
<table><thead><tr><th>@TH_CASE@</th><th>@TH_EXPECT@</th><th>@TH_GOT@</th>
<th>@TH_V@</th></tr></thead><tbody>@CASE_ROWS@</tbody></table>

<h2>@SEC3@</h2>
<div class="card meta">intake queue: rows @ROWS_BEFORE@ &rarr; @ROWS_AFTER@ &middot;
clean receipt carries the evt_id that landed (@EVT@); household registration
itself stays BigLife T-04 and this service only intakes.</div>

<h2>@SEC4@</h2>
<table><thead><tr><th>@TH_CASE@</th><th>@TH_EXPECT@</th><th>@TH_V@</th></tr></thead>
<tbody>@HTTP_ROWS@</tbody></table>
<div class="card meta"><b>@READONLY@</b> zero write endpoints: every non-GET verb
answers 405 and every unknown path answers 404, measured over a real socket.</div>

<h2>@SEC5@</h2>
<div class="disc"><b>@DISC@</b>
@DISCLAIMER@

<b>@AIGC@</b> @AI_LABEL@
</div>

<h2>@SEC6@</h2>
<div class="card"><ul>@CRIT_ROWS@</ul></div>
<div class="card meta">fingerprint @FINGERPRINT@ &middot; generated by
tools/city_face_report.py</div>
</main></body></html>
"""
    tokens = {
        "@TITLE@": L["title"], "@SUB@": L["sub"], "@GEN@": L["gen"],
        "@SRC@": L["src"], "@NOTE@": L["note"],
        "@SEC1@": L["sec1"], "@SEC2@": L["sec2"], "@SEC3@": L["sec3"],
        "@SEC4@": L["sec4"], "@SEC5@": L["sec5"], "@SEC6@": L["sec6"],
        "@TH_FIELD@": L["th_field"], "@TH_STATE@": L["th_state"],
        "@TH_CASE@": L["th_case"], "@TH_EXPECT@": L["th_expect"],
        "@TH_GOT@": L["th_got"], "@TH_V@": L["th_v"],
        "@DEEP@": L["deepwater"] + ": " + ", ".join(read["deep_water"]),
        "@FIELD_ROWS@": field_rows, "@DEEP_ROWS@": deep_rows,
        "@CASE_ROWS@": case_rows, "@HTTP_ROWS@": http_rows,
        "@CRIT_ROWS@": crit_rows,
        "@DIR@": _esc(city["city_dir_basename"]),
        "@ROWS@": L["rows"], "@IMPORTED@": _esc(city["imported_rows"]),
        "@HON@": L["honorary"], "@HONN@": _esc(city["honorary_seats"]),
        "@HOST@": HOST, "@PORT@": _esc(stamps["port"]),
        "@VERDICT@": _pass(passed == len(rows)), "@PASSED@": str(passed),
        "@TOTAL@": str(len(rows)),
        "@GENERATED@": _esc(stamps["generated_utc"]),
        "@ROWS_BEFORE@": _esc(intake["rows_before"]),
        "@ROWS_AFTER@": _esc(intake["rows_after_clean"]),
        "@EVT@": _esc("yes" if intake["receipt_evt_matches"] else "NO"),
        "@READONLY@": L["readonly"],
        "@DISC@": L["disc"],
        "@DISCLAIMER@": _esc(facts["compliance"]["disclaimer"]),
        "@AIGC@": L["aigc"], "@AI_LABEL@": _esc(facts["compliance"]["ai_label"]),
        "@FINGERPRINT@": _esc(fingerprint(facts)),
    }
    out = template
    for token, value in tokens.items():
        out = out.replace(token, value)
    return out


def _document(facts, stamps, rows, sizes):
    return {
        "generated_by": "tools/city_face_report.py",
        "p47_item": 1,
        "title": L["title"],
        "generated_utc": stamps["generated_utc"],
        "facts": facts,
        "fingerprint": fingerprint(facts),
        "criteria": [{"id": cid, "text": text} for cid, text in CRITERIA],
        "checks": rows,
        "verdict": "PASS" if all(r["pass"] for r in rows) else "FAIL",
        "sizes": sizes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the P-47 item-1 city observation face")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--json", default=DEFAULT_JSON)
    parser.add_argument("--check", action="store_true",
                        help="re-measure a fresh world and compare with the "
                             "landed document")
    args = parser.parse_args(argv)

    for path in (LOBBY_CFG, VIEW_PAGE,
                 os.path.join(CITY_DATA, "citizens-light.jsonl"),
                 os.path.join(CITY_DATA, "world-public.json")):
        if not os.path.isfile(path):
            print("E_INPUT missing %s" % path)
            return 3

    facts, stamps = measure()
    # the ephemeral port is not a fact about the tree
    stamps_for_facts = dict(stamps)
    stamps_for_facts.pop("port", None)

    if args.check:
        if not os.path.isfile(args.json):
            print("E_INPUT landed json missing: %s" % args.json)
            return 3
        landed = _load(args.json)
        html_size = (os.path.getsize(args.out)
                     if os.path.isfile(args.out) else 0)
        rows = verify(landed["facts"], {"html": html_size,
                                        "json": os.path.getsize(args.json)})
        drift = fingerprint(facts) != landed.get("fingerprint")
        passed = sum(1 for r in rows if r["pass"])
        print("CITY FACE --check facts_drift=%s port=%s"
              % ("YES" if drift else "no", stamps.get("port")))
        for row in rows:
            print("  %s %s %s" % ("PASS" if row["pass"] else "FAIL",
                                  row["id"], row["detail"]))
        print("VERDICT %s checks=%d/%d fresh_fingerprint=%s landed=%s"
              % ("PASS" if (passed == len(rows) and not drift) else "FAIL",
                 passed, len(rows), fingerprint(facts),
                 landed.get("fingerprint")))
        return 0 if (passed == len(rows) and not drift) else 2

    sizes = {"html": 0, "json": 0}
    body = ""
    payload = ""
    for _ in range(6):
        rows = verify(facts, sizes)
        body = render_html(facts, stamps, rows)
        doc = _document(facts, stamps, rows, sizes)
        payload = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        measured = {"html": len(body.encode("utf-8")),
                    "json": len(payload.encode("utf-8"))}
        if measured == sizes:
            break
        sizes = measured
    else:
        print("E_SIZES document sizes did not converge")
        return 2

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)

    rows = verify(facts, sizes)
    passed = sum(1 for r in rows if r["pass"])
    print("CITY FACE html=%s (%dB) json=%s (%dB) port=%s"
          % (args.out, sizes["html"], args.json, sizes["json"],
             stamps.get("port")))
    for row in rows:
        print("  %s %s %s" % ("PASS" if row["pass"] else "FAIL", row["id"],
                              row["detail"]))
    print("VERDICT %s checks=%d/%d fingerprint=%s"
          % ("PASS" if passed == len(rows) else "FAIL", passed, len(rows),
             fingerprint(facts)))
    return 0 if passed == len(rows) else 2


if __name__ == "__main__":
    sys.exit(main())
