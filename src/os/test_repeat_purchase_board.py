"""Battery suite for tools/repeat_purchase_board.py - criteria AC-RPN1..6.

WHY THIS SUITE EXISTS (measured at R3405, not assumed):
api_repeat_purchase has shipped with eight green criteria of its own
(test_apimarket_repeatpurchase.py, AC-RPT) but git grep -F over tools/ and
preview/ found no reader at all, so the marketplace's most load-bearing health
question - does the same resident come back and buy a second time - could not
be opened by anyone. R3405 renders it onto one page; this suite grades the
page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3405 PIN
BEFORE the driver existed):
  AC-RPN1  the page and its json land, and the json carries exactly the pinned
           payload key set including the sizes and sources blocks, with every
           scope block and category row carrying its pinned key set.
  AC-RPN2  the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped
           api_board() face (never typed ids), reads api_repeat_purchase() for
           the market and once per seller there, and requires the page json to
           equal those readings item for item plus the board disclaimer
           verbatim - no typed fixture, no synthesized retention.
  AC-RPN3  the face's identities hold everywhere: repeat + one-time equals
           buyer count, repeat purchases equal purchases minus buyers, the
           average and the rate re-derive from the counts with None on an
           honest empty, every category row satisfies the same four, and
           category purchases sum to the scope's own count.
  AC-RPN4  the page reads honestly: category rows ascend with the
           uncategorized bucket last, an undefined rate and a null top buyer
           print the no-value mark, the market row is printed first and named,
           and the page carries exactly one scope row per scope plus the
           market and one data row per pinned category row.
  AC-RPN5  the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-RPN6  no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-RPT arms.

Read-only over the repository: the provenance world is built in a temp dir and
every re-render writes into a temp dir, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "repeat_purchase_board.py")
HTML = os.path.join(ROOT, "preview", "repeat-purchase-board.html")
JSONF = os.path.join(ROOT, "preview", "repeat-purchase-board.json")
COPY = os.path.join(ROOT, "preview", "repeat-purchase-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_repeatpurchase.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-repeat-purchase-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope_count", "market", "scopes",
    "disclaimer", "report", "sources", "sizes",
}
SCOPE_KEYS = {"dev_account", "buyer_count", "repeat_buyer_count",
              "one_time_buyer_count", "repeat_rate", "purchase_count",
              "repeat_purchase_count", "avg_purchases_per_buyer",
              "max_purchases", "top_repeat_buyer", "categories", "disclaimer"}
CAT_KEYS = {"category", "buyer_count", "repeat_buyer_count",
            "one_time_buyer_count", "repeat_rate", "purchase_count",
            "repeat_purchase_count", "avg_purchases_per_buyer"}

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


def face_reading():
    """Market scope plus one scope per seller the shipped board enumerates."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="rpn-suite-")
    db = os.path.join(tmp_root, "rpn.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        market = dict(am.api_repeat_purchase())
        sellers = sorted(set(str(row["dev_account"])
                             for row in board["listings"]))
        scopes = [dict(am.api_repeat_purchase(seller)) for seller in sellers]
        return market, scopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def identity_problems(block, name):
    problems = []
    buyers = int(block["buyer_count"])
    repeat = int(block["repeat_buyer_count"])
    onetime = int(block["one_time_buyer_count"])
    bought = int(block["purchase_count"])
    again = int(block["repeat_purchase_count"])
    if repeat + onetime != buyers:
        problems.append("%s repeat+onetime" % name)
    if again != bought - buyers:
        problems.append("%s repeat_purchases" % name)
    want_rate = (float(repeat) / buyers) if buyers else None
    if block["repeat_rate"] != want_rate:
        problems.append("%s rate" % name)
    want_avg = (float(bought) / buyers) if buyers else None
    if block["avg_purchases_per_buyer"] != want_avg:
        problems.append("%s avg" % name)
    return problems


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    scopes = doc.get("scopes") or []

    # ---- AC-RPN1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    scope_keys_ok = bool(market) and set(market.keys()) == SCOPE_KEYS and all(
        set(block.keys()) == SCOPE_KEYS for block in scopes)
    cat_keys_ok = all(
        set(row.keys()) == CAT_KEYS
        for block in [market] + scopes for row in block.get("categories") or [])
    ok("AC-RPN1", landed and keys == PAYLOAD_KEYS and scope_keys_ok
       and cat_keys_ok and int(doc.get("scope_count", -1)) == len(scopes),
       "landed=%s keys=%d missing=%s extra=%s scope_keys=%s cat_keys=%s"
       " scopes=%d"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), scope_keys_ok, cat_keys_ok,
          len(scopes)))

    # ---- AC-RPN2: every printed number is the shipped face's own.
    live_market, live_scopes, disclaimer = face_reading()
    market_same = json.dumps(market, sort_keys=True) == json.dumps(
        live_market, sort_keys=True)
    same_len = len(scopes) == len(live_scopes)
    diffs = []
    if same_len:
        for landed_scope, live_scope in zip(scopes, live_scopes):
            if json.dumps(landed_scope, sort_keys=True) != json.dumps(
                    live_scope, sort_keys=True):
                diffs.append(landed_scope.get("dev_account"))
    disc_same = doc.get("disclaimer") == disclaimer
    ok("AC-RPN2", market_same and same_len and not diffs and disc_same,
       "market_same=%s scopes=%d/%d diffs=%s disclaimer_same=%s"
       % (market_same, len(scopes), len(live_scopes), diffs[:3], disc_same))

    # ---- AC-RPN3: the face's identities hold on every block.
    problems = identity_problems(market, "market") if market else ["no market"]
    for block in scopes:
        problems.extend(identity_problems(block, str(block["dev_account"])))
    for block in [market] + scopes:
        if not block:
            continue
        cats = block.get("categories") or []
        for row in cats:
            problems.extend(identity_problems(
                row, "%s/%r" % (block.get("dev_account"), row["category"])))
        if sum(int(row["purchase_count"]) for row in cats) != int(
                block["purchase_count"]):
            problems.append("%s purchase sum" % (block.get("dev_account"),))
    ok("AC-RPN3", not problems, "problems=%s"
       % (problems[:4] if problems else []))

    # ---- AC-RPN4: honest ordering, no-value marks, addressable rows.
    order_problems = []
    for block in [market] + scopes:
        if not block:
            continue
        keyed = [(row["category"] is None, row["category"] or "")
                 for row in block.get("categories") or []]
        if keyed != sorted(keyed):
            order_problems.append((block.get("dev_account"), keyed))
    undefined = [block for block in [market] + scopes
                 if block and block["repeat_rate"] is None]
    null_top = [block for block in [market] + scopes
                if block and block["top_repeat_buyer"] is None]
    mark = ">%s<" % labels.get("none", "-")
    stand_in_top = any(">None<" in page for _ in [0])
    scope_rows = page.count('<tr class="scope')
    cat_rows = page.count('<tr class="cat">')
    cats = len(market.get("categories") or [])
    market_first = False
    head = page.find('<tr class="scope')
    if head >= 0 and labels.get("market_label"):
        market_first = page.find(labels["market_label"], head) == page.find(
            ">", page.find("<td>", head)) + 1
    ok("AC-RPN4", not order_problems and scope_rows == 1 + len(scopes)
       and cat_rows == cats and (not undefined or mark in page)
       and (not null_top or mark in page) and not stand_in_top
       and market_first,
       "order=%s scope_rows=%d/%d cat_rows=%d/%d mark=%s stand_in_none=%s"
       " market_first=%s"
       % (order_problems[:2], scope_rows, 1 + len(scopes), cat_rows, cats,
          mark in page, stand_in_top, market_first))

    # ---- AC-RPN5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-RPN5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-RPN6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    # The path element carries parentheses and commas of its own, so the count
    # is read from the first closing paren followed by , N ) after the name.
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-RPT" in read(FACE_SUITE)
    ok("AC-RPN6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
