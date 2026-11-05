"""closeout_R2462 - append this window's evidence to src/os/state.json.

Same atomic-replace + read-back shape as the R2461 template. The log is kept
deliberately tight because the live log sits close to the 78500B waterline.
"""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2462 BUSINESS window on the sandbox entry face the R2461 "
    "export named as the next milestone (CEO standing order "
    "OB-20261105-003656-879: real output only). FINDING: the sandbox had four "
    "openable faces - city on --city-http-port, lobby on --web-port, the 19.9 "
    "checkout demo on its own process - and no door tying them together, so a "
    "reader needed three commands and three URLs. Anchor check at HEAD before "
    "any code: AC-HUB1, os-sandbox-hub, sandbox_hub and hub.html hit nothing "
    "at all.",

    "2026-11-05 R2462 SHIPPED src/sandbox/lobby/hub.html (5393B "
    "self-contained, zero external references, carrying the AI generated "
    "label, the non-advice note, the mock/no-real-charge statement and the "
    "read-only statement) plus src/sandbox/lobby/hub_page.py (GET /hub, "
    "GET /hub/ serve the page byte-identical from disk; GET /hub/api/faces "
    "publishes the ports THIS process really bound; unknown 404, non-GET 405) "
    "plus --hub-port and --checkout-port on server.py, which starts it beside "
    "the ws/city/web faces and names it in the banner. Bring-up: python "
    "src/sandbox/lobby/server.py --city-http-port 8092 --web-port 8094 "
    "--hub-port 8095 then open http://127.0.0.1:8095/hub/.",

    "2026-11-05 R2462 EVIDENCE: AC-HUB1..AC-HUB6 were pinned in "
    "src/os/backlog.md BEFORE the module, page and suite existed, and "
    "src/sandbox/lobby/test_hub_page.py reads SUITE PASS 6/6 twice with an "
    "identical criterion digest through the shipped capture callable "
    "(EVIDENCE CAPTURE round=R2462 legs=2 identical=True adjacent=1 fails=0, "
    "qa/sandbox-hub-R2462.log 1240B); every criterion is read off a REAL "
    "server on OS-assigned ports, and AC-HUB4 compares each published URL "
    "against the port THIS leg configured rather than a literal. Registry "
    "moved exactly one row to 559 suites / 4330 criteria; three adjacent "
    "suites stayed green (lobby page 6/6, city view 6/6, checkout demo 6/6 "
    "with its digest unchanged at 46654133EC75D89438D1B6C4547C79CE); "
    "docs/sandbox-suite-matrix.md regenerated stamp-aligned to 53959B with "
    "--check byte-identical and its green line honestly reads 558/559 because "
    "no battery log carries the new suite yet.",

    "2026-11-05 R2462 debt register: reconcile-battery-R2463 opened first=no "
    "through debt_append at 120110B -> 120598B (readback=ok) because product "
    "src bytes changed and the registry moved, so the R2168 mixed-tree rule "
    "owes the battery next at the pre-registered 559 suites / 4330 criteria. "
    "The gate reads CLAIM-FIRST product-face-R2456 carried=7 stale, still the "
    "internal audit row and still claimable.",

    "2026-11-05 R2462 honest disclosures: (a) the checkout URL is a "
    "PUBLISHED PORT, not a liveness claim - the payload carries a note naming "
    "checkout_demo.py and the port to start it on, because the demo is its own "
    "process and pretending otherwise would be disprovable in one click; (b) "
    "Docker is still absent on this host, so the compose bring-up stays "
    "unproved and is not claimed; (c) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (d) the criteria were pre-registered in the backlog BEFORE "
    "the code this window, correcting the R2460 ordering lapse; (e) the window "
    "ran past its 25-minute budget on three suite legs plus the capture and the "
    "matrix regeneration; (f) tasks.md was not touched, it is the P-47 "
    "canonical board.",

    "R2462 tokens: local=~11k api=0 api_reason=business window - one entry "
    "page, one read-only serving face that publishes the real bound ports, two "
    "server flags, one six-criteria suite proved twice with an identical digest "
    "plus three adjacent suites re-run green, one registry row, one "
    "stamp-aligned matrix regeneration with a byte-identical check, one battery "
    "debt row appended, and the state/export/backlog/heartbeat closeout; zero "
    "cloud calls and zero external API touches",
]


def main():
    with open(STATE, "rb") as handle:
        raw = handle.read()
    crlf = b"\r\n" in raw
    obj = json.loads(raw.decode("utf-8"))
    before = len(obj.get("log") or [])
    obj["tick"] = int(obj.get("tick", 0)) + 1
    obj.setdefault("log", []).extend(LINES)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if crlf:
        text = text.replace("\n", "\r\n")
    data = text.encode("utf-8")
    fd, path = tempfile.mkstemp(dir=BASE, prefix=".state-", suffix=".tmp")
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    os.replace(path, STATE)
    with open(STATE, "rb") as handle:
        back = handle.read()
    check = json.loads(back.decode("utf-8"))
    print("STATE CLOSEOUT tick=%d log=%d->%d crlf=%s bytes=%d readback=%s"
          % (check["tick"], before, len(check["log"]), crlf, len(back),
             "ok" if len(check["log"]) == before + len(LINES) else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())