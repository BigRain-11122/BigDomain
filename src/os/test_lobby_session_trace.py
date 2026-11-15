"""Battery suite for tools/lobby_session_trace.py - AC-LST1..AC-LST6.

The six criteria belong to the tool and were pinned in src/os/backlog.md at
R2790, BEFORE the tool existed. This suite is what finally puts them under a
battery row; AC-LSTB1..AC-LSTB8 (the guard shape) were pinned at R2792, again
before this file existed.

Scope, stated honestly: this suite does NOT re-drive a socket. run_session()
needs the sandbox venv and would open a local port on every battery run, so the
suite guards the RECORDED face and the derivation that produced it - the landed
preview pair, the config it claims to read, the render function, and the
read-only gate. A tampered private copy proves the gate is load-bearing.

Every check is read-only against the repo: the whole world this suite mutates
lives under the system temp dir and is removed before the run ends.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import importlib.util
import json
import os
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "lobby_session_trace.py")
OUT_HTML = os.path.join(ROOT, "preview", "lobby-session-trace.html")
OUT_JSON = os.path.join(ROOT, "preview", "lobby-session-trace.json")
CONFIG = os.path.join(ROOT, "src", "sandbox", "lobby", "config.json")
SERVER = os.path.join(ROOT, "src", "sandbox", "lobby", "server.py")

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def load_tool():
    spec = importlib.util.spec_from_file_location("lst_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stat_sig(path):
    return (os.path.getsize(path), os.path.getmtime(path))


def links(html_text):
    found = []
    index = 0
    while True:
        at = html_text.find('href="', index)
        if at < 0:
            return found
        start = at + len('href="')
        end = html_text.find('"', start)
        if end < 0:
            return found
        found.append(html_text[start:end])
        index = end + 1


def main():
    before_html = stat_sig(OUT_HTML)
    before_json = stat_sig(OUT_JSON)
    tool = load_tool()

    # AC-LSTB1 - the landed pair exists and reads.
    have = os.path.exists(OUT_HTML) and os.path.exists(OUT_JSON)
    payload = None
    html_bytes = b""
    if have:
        html_bytes = read_bytes(OUT_HTML)
        json_bytes = read_bytes(OUT_JSON)
        try:
            html_text = html_bytes.decode("utf-8")
            payload = json.loads(json_bytes.decode("utf-8"))
            decode_ok = True
        except Exception as exc:  # noqa: BLE001
            html_text = ""
            decode_ok = False
            print("  ! pair unreadable: %s" % exc)
    else:
        html_text = ""
        decode_ok = False
    ok("AC-LSTB1", have and decode_ok and isinstance(payload, dict),
       "html=%dB json=%dB" % (len(html_bytes),
                              os.path.getsize(OUT_JSON) if have else 0))

    steps = (payload or {}).get("steps") or []
    summary = (payload or {}).get("summary") or {}
    derived = (payload or {}).get("derived") or {}
    source = (payload or {}).get("source") or {}

    # AC-LST2 - the six derived facts on the page still equal the live config.
    cfg = json.loads(read_bytes(CONFIG).decode("utf-8"))
    rate = cfg.get("rate_limit") or {}
    gate = cfg.get("gate") or {}
    pairs = [
        (list(derived.get("rooms") or []), list(cfg.get("rooms") or [])),
        (derived.get("max_text_len"), cfg.get("max_text_len")),
        (derived.get("rate_max_messages"), rate.get("max_messages")),
        (derived.get("rate_window_seconds"), rate.get("window_seconds")),
        (derived.get("forbidden_sample"), (gate.get("forbidden_words") or [""])[0]),
        (derived.get("advisory_sample"), (gate.get("advisory_ban_words") or [""])[0]),
    ]
    drift = [i for i, (a, b) in enumerate(pairs) if a != b]
    ok("AC-LST2", have and not drift, "facts=%d drift=%d" % (len(pairs), len(drift)))

    # AC-LST1 - the announced frame count is the number of frame rows present.
    counted = sum(len(row.get("frames") or []) for row in steps)
    ok("AC-LST1", have and counted > 0 and counted == int(summary.get("frames", -1)),
       "rows=%d announced=%s" % (counted, summary.get("frames")))

    # AC-LST4 - refusals carry server codes, all three appear, one accepted
    # broadcast carries the server's own ai_generated flag.
    frames = [f for row in steps for f in (row.get("frames") or [])]
    refusals = [f for f in frames if f.get("type") in ("sec.reject", "err.rate_limit")]
    codes = set(summary.get("codes") or [])
    wanted = {"E_CONTENT_REJECTED", "E_ROOM_UNKNOWN", "E_RATE_LIMIT"}
    uncoded = [f for f in refusals if not f.get("code")]
    flagged = [f for f in frames
               if f.get("type") == "chat.broadcast" and f.get("ai_generated") is False]
    ok("AC-LST4", have and bool(refusals) and not uncoded and wanted.issubset(codes) and bool(flagged),
       "refusals=%d uncoded=%d codes=%d flagged=%d"
       % (len(refusals), len(uncoded), len(codes & wanted), len(flagged)))

    # AC-LST3 - the landed html is a pure function of the landed payload.
    fresh = tool.render_html(payload).decode("utf-8") if have else ""
    again = tool.render_html(payload).decode("utf-8") if have else ""
    ok("AC-LST3", have and fresh == html_text and fresh == again,
       "render=%dB identical=%s" % (len(fresh.encode("utf-8")), fresh == html_text))

    # AC-LST5 - offline, and every relative link target exists on disk.
    literals = [n for n in ("http://", "https://") if n in html_text]
    targets = links(html_text)
    external = [t for t in targets if "://" in t or t.startswith("//")]
    missing = [t for t in targets
               if t not in external and not t.startswith("#")
               and not os.path.exists(os.path.join(ROOT, t.split("#")[0]))]
    ok("AC-LST5", have and not literals and not missing,
       "hrefs=%d external=%d missing=%d" % (len(targets), len(external), len(missing)))

    # AC-LST6 - the recorded source sizes still describe the final tree.
    size_a = source.get("config_bytes") == os.path.getsize(CONFIG)
    size_b = source.get("server_bytes") == os.path.getsize(SERVER)
    ok("AC-LST6", have and size_a and size_b,
       "config=%s server=%s" % (size_a, size_b))

    # AC-LST7 - the read-only gate passes and writing nothing is proven by stat.
    findings, code = tool.check(read_bytes(OUT_JSON), html_bytes) if have else (["no pair"], 2)
    after_html = stat_sig(OUT_HTML)
    after_json = stat_sig(OUT_JSON)
    untouched = before_html == after_html and before_json == after_json
    ok("AC-LST7", have and code == 0 and not findings and untouched,
       "rc=%d findings=%d untouched=%s" % (code, len(findings), untouched))

    # AC-LSTB8 - one tampered byte in a PRIVATE copy must redden the gate.
    world = tempfile.mkdtemp(prefix="lst-")
    try:
        tampered = json.loads(json.dumps(payload)) if have else {}
        if steps:
            tampered["steps"][0]["label"] = tampered["steps"][0].get("label", "") + " x"
        path = os.path.join(world, "tampered.json")
        with open(path, "wb") as handle:
            handle.write(tool.dump_json(tampered) if have else b"{}")
        tfindings, tcode = tool.check(read_bytes(path), html_bytes) if have else (["no payload"], 2)
        stale = any("E_STALE" in f for f in tfindings)
        ok("AC-LSTB8", have and tcode == 2 and stale,
           "rc=%d stale=%s findings=%d" % (tcode, stale, len(tfindings)))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
