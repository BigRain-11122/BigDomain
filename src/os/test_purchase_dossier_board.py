"""Battery suite for tools/purchase_dossier_board.py - AC-AMPDB1..6.

WHY THIS SUITE EXISTS (measured at R3418, not assumed):
api_purchase_dossier shipped with its own AC-AMPD1..8 criteria
(src/sandbox/ledger/test_apimarket_purchasedossier.py) but a git grep over
tools/ and preview/ answered rc=1 with zero page readers, so the question a
support desk asks - "what actually happened to THIS purchase: the money, the
refund, the rating, the claim" - could not be opened by anyone. R3418 renders
one dossier section per purchase onto one page; this suite grades the page, not
the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3418 PIN
BEFORE the driver existed):
  AC-AMPDB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, every
           purchase block carries the shipped twenty-one-key envelope, the
           refund/rating/claim blocks carry their pinned key sets when they are
           present, purchase_count equals the block count, and the report
           points at a file that exists.
  AC-AMPDB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates purchase ids through the shipped
           board and sales faces, reads api_purchase_dossier() over it, and
           requires the page json's purchases to equal that reading item for
           item plus the disclaimer verbatim - no typed fixture, no synthesized
           row; the seller view is also required to differ from the buyer view
           in viewer_role alone.
  AC-AMPDB3 the face's identities hold: the price splits into its two legs,
           a refund equals the price paid and splits into the same two legs, a
           revision count is never negative, ticket_state is one of the pinned
           six and equals the recomputed precedence, delisted agrees with its
           stamp, purchase ids ascend strictly, and purchased_utc is ISO Z.
  AC-AMPDB4 the page reads honestly: one section and one summary data row per
           purchase, a purchase with no refund / rating / claim prints an
           explicit absence line, an empty world handed to the driver's own
           renderer prints the same line (in-memory probe only), the seven law
           sentences are on the page, and no bare None reaches it.
  AC-AMPDB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-AMPDB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-AMPD arms.

Read-only over the repository: the provenance world is built in a temp dir and
the empty probe renders in memory, never inside preview/.

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
TOOL = os.path.join(ROOT, "tools", "purchase_dossier_board.py")
HTML = os.path.join(ROOT, "preview", "purchase-dossier-board.html")
JSONF = os.path.join(ROOT, "preview", "purchase-dossier-board.json")
COPY = os.path.join(ROOT, "preview", "purchase-dossier-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_purchasedossier.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-purchase-dossier-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "purchase_count",
    "purchases", "disclaimer", "report", "sources", "sizes",
}
PURCHASE_KEYS = {
    "purchase_id", "listing_id", "listing_key", "title", "category",
    "buyer_id", "dev_account", "viewer_role", "price_paid", "dev_share",
    "platform_share", "spend_tx", "purchased_utc", "current_price",
    "delisted", "delisted_utc", "refund", "rating", "claim",
    "ticket_state", "disclaimer",
}
REFUND_KEYS = {
    "refund_id", "amount", "dev_share", "platform_share", "refund_tx",
    "refunded_utc", "reason",
}
RATING_KEYS = {"rating_id", "stars", "revision_count", "revised_utc"}
CLAIM_KEYS = {
    "claim_id", "claim_text", "opened_utc", "status", "refund_id",
    "refunded_utc", "response_id", "response_text", "responded_utc",
    "withdrawn_utc",
}
TICKET_STATES = {"refunded", "withdrawn", "answered", "open", "rated",
                 "settled"}

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


def live_purchases():
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="apdb-suite-")
    db = os.path.join(tmp_root, "apdb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        seen = {}
        for dev in sorted(set(str(row["dev_account"])
                              for row in board["listings"])):
            for row in (dict(am.api_sales(dev)).get("sales") or []):
                pid = row.get("purchase_id")
                buyer = row.get("buyer_id")
                if pid is not None and buyer:
                    seen[int(pid)] = str(buyer)
        blocks = [dict(am.api_purchase_dossier(pid, seen[pid]))
                  for pid in sorted(seen)]
        seller_views = {}
        for pid in sorted(seen):
            doc = dict(am.api_purchase_dossier(pid, seen[pid]))
            seller_views[pid] = dict(
                am.api_purchase_dossier(pid, doc["dev_account"]))
        return blocks, seller_views, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("apdb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_state(block):
    claim = block.get("claim")
    if block.get("refund") is not None:
        return "refunded"
    if claim is not None and claim.get("status") == "withdrawn":
        return "withdrawn"
    if claim is not None and claim.get("status") == "answered":
        return "answered"
    if claim is not None and claim.get("status") == "open":
        return "open"
    if block.get("rating") is not None:
        return "rated"
    return "settled"


def identity_problems(blocks):
    problems = []
    previous = 0
    for block in blocks:
        name = str(block.get("purchase_id"))
        pid = int(block.get("purchase_id", -1))
        if pid <= previous:
            problems.append("%s purchase_id order" % name)
        previous = pid
        paid = int(block.get("price_paid", -1))
        if paid != int(block.get("dev_share", 0)) + int(
                block.get("platform_share", 0)):
            problems.append("%s split" % name)
        refund = block.get("refund")
        if refund is not None:
            if int(refund["amount"]) != paid:
                problems.append("%s refund amount" % name)
            if int(refund["amount"]) != (int(refund["dev_share"])
                                         + int(refund["platform_share"])):
                problems.append("%s refund split" % name)
        rating = block.get("rating")
        if rating is not None and int(rating.get("revision_count", -1)) < 0:
            problems.append("%s revision count" % name)
        claim = block.get("claim")
        if claim is not None and claim.get("status") not in (
                "open", "answered", "withdrawn", "refunded"):
            problems.append("%s claim status" % name)
        state = block.get("ticket_state")
        if state not in TICKET_STATES:
            problems.append("%s ticket_state" % name)
        elif state != expected_state(block):
            problems.append("%s ticket_state mismatch" % name)
        stamped = block.get("delisted_utc") is not None
        if bool(block.get("delisted")) != stamped:
            problems.append("%s delisted stamp" % name)
        purchased = str(block.get("purchased_utc"))
        if (len(purchased) != 20 or purchased[10] != "T"
                or not purchased.endswith("Z")):
            problems.append("%s purchased_utc" % name)
    return problems


def probe_empty(disclaimer):
    """An empty world: never landed, only handed to the renderer."""
    del disclaimer
    return []


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    blocks = doc.get("purchases") or []

    # ---- AC-AMPDB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    blocks_ok = all(set(block.keys()) == PURCHASE_KEYS for block in blocks)
    nested_ok = all(
        (block["refund"] is None or set(block["refund"].keys()) == REFUND_KEYS)
        and (block["rating"] is None
             or set(block["rating"].keys()) == RATING_KEYS)
        and (block["claim"] is None or set(block["claim"].keys()) == CLAIM_KEYS)
        for block in blocks)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    ok("AC-AMPDB1", landed and keys == PAYLOAD_KEYS and blocks_ok and nested_ok
       and bool(blocks) and int(doc.get("purchase_count", -1)) == len(blocks)
       and report_ok,
       "landed=%s keys=%d missing=%s extra=%s blocks=%s nested=%s "
       "purchases=%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), blocks_ok, nested_ok, len(blocks),
          report_ok))

    # ---- AC-AMPDB2: every printed number is the shipped face's own.
    live, seller_views, live_disclaimer = live_purchases()
    same = (json.dumps(blocks, sort_keys=True)
            == json.dumps(live, sort_keys=True))
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    role_only = True
    for block in live:
        seller = dict(seller_views[int(block["purchase_id"])])
        if seller.get("viewer_role") != "seller":
            role_only = False
            break
        buyer = dict(block)
        buyer.pop("viewer_role", None)
        seller.pop("viewer_role", None)
        if json.dumps(buyer, sort_keys=True) != json.dumps(seller,
                                                           sort_keys=True):
            role_only = False
            break
    ok("AC-AMPDB2", same and disc_same and role_only and bool(blocks),
       "identical=%s disclaimer_same=%s role_only_diff=%s purchases=%d"
       % (same, disc_same, role_only, len(blocks)))

    # ---- AC-AMPDB3: the face's identities hold on this envelope.
    problems = identity_problems(blocks) if blocks else ["no purchases"]
    ok("AC-AMPDB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-AMPDB4: honest page face, explicit absences, laws, no None.
    page_rows = page.count('<tr class="purchase"')
    sections_ok = all(('id="purchase-%s"' % block["purchase_id"]) in page
                      for block in blocks)
    stand_in = ">None<" in page
    absence_keys = (("refund", "no_refund"), ("rating", "no_rating"),
                    ("claim", "no_claim"))
    absence_ok = True
    for block in blocks:
        section = page.split('id="purchase-%s"' % block["purchase_id"],
                             1)[-1]
        section = section.split('id="purchase-', 1)[0]
        for name, label_key in absence_keys:
            if block[name] is None:
                if labels.get(label_key, "") not in section:
                    absence_ok = False
            elif labels.get(label_key, "") in section:
                absence_ok = False
    laws = [labels.get(key, "") for key in
            ("law_split", "law_refund", "law_state", "law_party",
             "law_pure", "law_absence", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_probe_ok = False
    try:
        driver = load_driver()
        disclaimer = doc.get("disclaimer") or ""
        probe_html = driver.build_html(probe_empty(disclaimer), labels,
                                       "2026-01-01 00:00:00Z", disclaimer)
        empty_probe_ok = (labels.get("no_purchases", "") in probe_html
                          and '<tr class="purchase' not in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-AMPDB4", page_rows == len(blocks) and sections_ok and not stand_in
       and absence_ok and laws_ok and empty_probe_ok,
       "rows=%d/%d sections=%s absences=%s laws=%s empty_probe=%s "
       "stand_in_none=%s"
       % (page_rows, len(blocks), sections_ok, absence_ok, laws_ok,
          empty_probe_ok, stand_in))

    # ---- AC-AMPDB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-AMPDB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-AMPDB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMPD" in read(FACE_SUITE)
    ok("AC-AMPDB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
