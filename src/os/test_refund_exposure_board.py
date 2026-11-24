"""Battery suite for tools/refund_exposure_board.py - criteria AC-REX1..6.

WHY THIS SUITE EXISTS (measured at R3412, not assumed):
api_refund_exposure shipped with its own AC-RPX1..8 criteria of its own
(src/sandbox/ledger/test_apimarket_refundexposure.py) but a git grep over
tools/ and preview/ answered rc=1 with zero hits, so the two questions an
operator and a seller both ask - how much of my balance is already spoken
for by refunds I may have to pay back, and which seller would break a
refund today - could not be opened by anyone. R3412 renders the exposure
onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3412 PIN
BEFORE the driver existed):
  AC-REX1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, the
           nested exposure carries the shipped seven-key envelope, every row
           carries the shipped nine-key row set, seller_count equals the row
           count, and the report points at a file that exists.
  AC-REX2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, reads api_refund_exposure() over it, and
           requires the page json's exposure to equal that reading item for
           item plus the disclaimer verbatim - no typed fixture, no
           synthesized row.
  AC-REX3 the face's identities hold: seller_count, total_liability,
           total_shortfall and at_risk_count re-derive from the rows, every
           row is non-negative, shortfall equals max(0, liability - balance),
           covered equals shortfall == 0, and the rows run ascending by
           dev_account.
  AC-REX4 the page reads honestly: one data row per seller, the liability
           sentence is on the page, the zero at-risk world prints an explicit
           sentence instead of an empty section (measured on the landed page),
           a shortfall-bearing envelope handed to the driver's own renderer
           names the seller and its shortfall (in-memory probe only), and no
           bare None reaches the page.
  AC-REX5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-REX6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-RPX arms.

Read-only over the repository: the provenance world is built in a temp dir and
the shortfall probe renders in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "refund_exposure_board.py")
HTML = os.path.join(ROOT, "preview", "refund-exposure.html")
JSONF = os.path.join(ROOT, "preview", "refund-exposure.json")
COPY = os.path.join(ROOT, "preview", "refund-exposure-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_refundexposure.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-refund-exposure-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "seller_count", "exposure",
    "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "seller_count", "total_liability", "total_shortfall",
    "at_risk_count", "disclaimer", "rows",
}
ROW_KEYS = {
    "dev_account", "listing_count", "open_purchases", "refunded_purchases",
    "refundable_liability", "balance", "balance_known", "shortfall",
    "covered",
}

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def stamp(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def run_tool(args, cwd=ROOT):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def live_exposure():
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="rex-suite-")
    db = os.path.join(tmp_root, "rex.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_refund_exposure())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("rex_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_problems(envelope):
    rows = envelope.get("rows") or []
    problems = []
    if int(envelope.get("seller_count", -1)) != len(rows):
        problems.append("seller_count")
    if int(envelope.get("total_liability", -1)) != sum(
            int(row["refundable_liability"]) for row in rows):
        problems.append("total_liability")
    if int(envelope.get("total_shortfall", -1)) != sum(
            int(row["shortfall"]) for row in rows):
        problems.append("total_shortfall")
    if int(envelope.get("at_risk_count", -1)) != sum(
            1 for row in rows if int(row["shortfall"]) > 0):
        problems.append("at_risk_count")
    owners = [str(row["dev_account"]) for row in rows]
    if owners != sorted(owners):
        problems.append("order")
    for row in rows:
        name = str(row["dev_account"])
        for key in ("listing_count", "open_purchases", "refunded_purchases",
                    "refundable_liability", "shortfall"):
            if int(row[key]) < 0:
                problems.append("%s negative %s" % (name, key))
        expected = int(row["refundable_liability"]) - int(row["balance"])
        if expected < 0:
            expected = 0
        if int(row["shortfall"]) != expected:
            problems.append("%s shortfall" % name)
        if bool(row["covered"]) != (int(row["shortfall"]) == 0):
            problems.append("%s covered" % name)
    return problems


def probe_envelope(disclaimer):
    """A shortfall-bearing envelope: never landed, only handed to the renderer."""
    return {
        "dev_account": None, "seller_count": 1, "total_liability": 9,
        "total_shortfall": 5, "at_risk_count": 1, "disclaimer": disclaimer,
        "rows": [{
            "dev_account": "usr:probe-underwater", "listing_count": 1,
            "open_purchases": 1, "refunded_purchases": 0,
            "refundable_liability": 9, "balance": 4, "balance_known": True,
            "shortfall": 5, "covered": False,
        }],
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    exposure = doc.get("exposure") or {}
    rows = exposure.get("rows") or []

    # ---- AC-REX1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelope_ok = set(exposure.keys()) == ENVELOPE_KEYS
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-REX1", landed and keys == PAYLOAD_KEYS and envelope_ok
       and rows_ok and bool(rows)
       and int(doc.get("seller_count", -1)) == len(rows)
       and int(exposure.get("seller_count", -1)) == len(rows) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelope=%s rows=%s "
       "sellers=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelope_ok, rows_ok, len(rows),
          report_ok))

    # ---- AC-REX2: every printed number is the shipped face's own.
    live = live_exposure()
    same = (json.dumps(exposure, sort_keys=True)
            == json.dumps(live, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live.get("disclaimer"))
    ok("AC-REX2", same and disc_same and bool(rows),
       "identical=%s disclaimer_same=%s sellers=%d liability=%s at_risk=%s"
       % (same, disc_same, len(rows), exposure.get("total_liability"),
          exposure.get("at_risk_count")))

    # ---- AC-REX3: the face's identities hold on this envelope.
    problems = identity_problems(exposure) if rows else ["no rows"]
    ok("AC-REX3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-REX4: honest page face, explicit zero-risk sentence.
    page_rows = page.count('<tr class="seller"')
    sections_ok = all(('data-seller="%s"' % row["dev_account"]) in page
                      for row in rows)
    stand_in = ">None<" in page
    liability_law = labels.get("law_liability", "") in page
    at_risk = int(exposure.get("at_risk_count", -1))
    zero_sentence = labels.get("risk_none", "") in page
    zero_ok = zero_sentence if at_risk == 0 else True
    risk_probe_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        probe_html = driver.build_html(probe_envelope(disclaimer), labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        risk_probe_ok = ('class="risk-row"' in probe_html
                         and "usr:probe-underwater" in probe_html
                         and ">5<" in probe_html
                         and labels.get("risk_none", "") not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-REX4", page_rows == len(rows) and sections_ok and not stand_in
       and liability_law and zero_ok and risk_probe_ok,
       "rows=%d/%d sections=%s liability_law=%s zero_sentence=%s "
       "risk_probe=%s stand_in_none=%s"
       % (page_rows, len(rows), sections_ok, liability_law, zero_ok,
          risk_probe_ok, stand_in))

    # ---- AC-REX5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-REX5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-REX6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-RPX" in read(FACE_SUITE)
    ok("AC-REX6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
