"""Subset-axis semantics window for the multi-year combined
honor yearbook read face (BigDomain R2026; canon = the
explore-queue honorcert subset-axis claim row, criteria
AC-HYS1..AC-HYS7 pre-registered in that row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Suite-only round: the shipped yearbooks_combined face is NOT
touched. The window pins the request-family axis semantics the
in-book criteria left open: the strictly descending full-set
request, the single-year and two-year request families, the
all-empty-years request family, and the same-year-set
multi-form hardening (list / tuple / scrambled tuples / set /
frozenset / generator) where every input form must fold to one
byte-identical envelope - the ascending sort absorbs the
per-process set iteration order drift, proving the zero
insertion-order-key law. Already-in-book faces are not
re-registered: scrambled-to-ascending canonicalization
(AC-HYM3/AC-HYCP1), the subset law (AC-HYCP6) and the empty
iterable request (AC-HYM1) stay with their owners.

Usage: python test_honorcert_yearbook_subsetaxis.py
"""

import hashlib
import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import civicpoints as CV              # noqa: E402 (R1752 face)
import collectibles as CL             # noqa: E402 (R619 face)
import honorcert as HC                # noqa: E402 (R1755 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the multi-year honor"
              " yearbook is a platform recognition roster, not"
              " investment advice, and carries no monetary value")

NETWORK_LIBS = ("urllib", "requests", "socket", "http")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ACCOUNTS = ("usr:carol", "usr:aaron", "usr:bob", "usr:dave",
            "usr:erin", "usr:frank")
ITEM26 = "civic-honor-2026"
ITEM27 = "civic-honor-2027"
DESCENDING = ("2028", "2027", "2026", "2025")
ASCENDING = ["2025", "2026", "2027", "2028"]
ENV_KEYS = {"years", "yearbooks", "totals", "disclaimer"}
BLOCK_KEYS = {"year", "yearbook", "certified_count", "board_size"}
TOTALS_KEYS = {"years_count", "certified_count", "board_size",
               "distinct_accounts"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def block_rows(res):
    """Per-year block tuple view for value pinning."""
    out = []
    for block in res["yearbooks"]:
        rows = [(r["board_rank"], r["account_id"], r["points"],
                 r["item_id"]) for r in block["yearbook"]]
        out.append((block["year"], rows, block["certified_count"],
                    block["board_size"]))
    return out


def table_counts(led_path, cv_path):
    out = {}
    conn = sqlite3.connect(led_path)
    out["collectibles"] = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles").fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    out["ledger_entries"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_entries").fetchone()[0])
    conn.close()
    cvconn = sqlite3.connect(cv_path)
    for table in CIVIC_TABLES:
        out[table] = int(cvconn.execute(
            "SELECT COUNT(*) FROM " + table).fetchone()[0])
    cvconn.close()
    return out


def build_world(led_path, cv_path, cfg):
    """Deterministic multi-year anchor world, same shape as the
    R2025 persist suite: six accounts; 2026 board carol 12 /
    aaron 7 / bob 7 (tie, id asc) / dave 3 with erin and frank
    zero-row faces; 2027 side board carol 5 / aaron 2; 2025
    and 2028 carry zero earn rows."""
    led = L.Ledger(led_path, cfg)
    for acct in ACCOUNTS:
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    cv.register_behavior("city-poll", "Community Poll", 5, 20, False)
    cv.register_behavior("street-clean", "Street Cleanup", 2, 20,
                         False)
    cv.register_behavior("harvest", "Harvest Help", 3, 20, False)
    cv.earn_civic("usr:carol", "city-poll", "2026-10-01", "c-poll-1")
    cv.earn_civic("usr:carol", "city-poll", "2026-10-01", "c-poll-2")
    cv.earn_civic("usr:carol", "street-clean", "2026-10-01",
                  "c-sc-1")
    cv.earn_civic("usr:aaron", "city-poll", "2026-10-01", "a-poll-1")
    cv.earn_civic("usr:aaron", "street-clean", "2026-10-01",
                  "a-sc-1")
    cv.earn_civic("usr:bob", "city-poll", "2026-10-01", "b-poll-1")
    cv.earn_civic("usr:bob", "street-clean", "2026-10-01",
                  "b-sc-1")
    cv.earn_civic("usr:dave", "harvest", "2026-10-01", "d-hv-1")
    cv.earn_civic("usr:carol", "city-poll", "2027-03-01", "c27-p-1")
    cv.earn_civic("usr:aaron", "street-clean", "2027-03-01",
                  "a27-s-1")
    return led, cv, cl


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-ybsubset-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    mod_sha_before = dict(
        (name, sha16(io_read(os.path.join(BASE, name + ".py"))))
        for name in ("honorcert", "civicpoints", "collectibles"))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    led_path = os.path.join(tmp, "ledger.db")
    cv_path = os.path.join(tmp, "civic.db")

    led, cv, cl = build_world(led_path, cv_path, cfg)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    hc.grant_year_honors("2026", 2, ITEM26)
    hc.grant_year_honors("2027", 2, ITEM27)

    # -- AC-HYS1 strictly descending full-set canonicalization --
    r_desc = hc.yearbooks_combined(DESCENDING)
    r_asc = hc.yearbooks_combined(ASCENDING)
    ok1 = (
        r_desc["years"] == ASCENDING
        and [b["year"] for b in r_desc["yearbooks"]] == ASCENDING
        and block_rows(r_desc) == [
            ("2025", [], 0, 0),
            ("2026", [(1, "usr:carol", 12, ITEM26),
                      (2, "usr:aaron", 7, ITEM26)], 2, 4),
            ("2027", [(1, "usr:carol", 5, ITEM27),
                      (2, "usr:aaron", 2, ITEM27)], 2, 2),
            ("2028", [], 0, 0)]
        and dump(r_desc) == dump(r_asc))
    record("AC-HYS1", ok1, "strictly descending request %s ->"
          " ascending years %s with the block order riding the"
          " year axis and every per-block value pinned (2025/2028"
          " honest empty, 2026 carol 12 / aaron 7, 2027 carol 5 /"
          " aaron 2); the full envelope dumps byte-identical to"
          " the ascending same-set request (sha16=%s) - axis"
          " canonicalization is independent of the request order"
          % (list(DESCENDING), r_desc["years"],
             sha16(dump(r_desc))))

    # -- AC-HYS2 single-year request family ------------------------
    s26 = hc.yearbooks_combined(("2026",))
    s25 = hc.yearbooks_combined(("2025",))
    direct26 = hc.honor_yearbook("2026")
    stripped26 = {k: v for k, v in direct26.items()
                  if k != "disclaimer"}
    blk26 = s26["yearbooks"][0]
    ok2 = (
        s26["years"] == ["2026"]
        and len(s26["yearbooks"]) == 1
        and dump(blk26) == dump(stripped26)
        and set(blk26.keys()) == BLOCK_KEYS
        and s26["totals"] == {"years_count": 1,
                              "certified_count": 2,
                              "board_size": 4,
                              "distinct_accounts": 2}
        and s25["years"] == ["2025"]
        and s25["yearbooks"][0]["yearbook"] == []
        and s25["totals"] == {"years_count": 1,
                              "certified_count": 0,
                              "board_size": 0,
                              "distinct_accounts": 0})
    record("AC-HYS2", ok2, "single-year family: ('2026',) ->"
          " years==['2026'] with exactly one block that equals"
          " honor_yearbook('2026') minus disclaimer byte-for-byte"
          " (single source), totals=%s; the empty single-year"
          " request ('2025',) keeps the honest empty block and"
          " totals=%s"
          % (s26["totals"], s25["totals"]))

    # -- AC-HYS3 two-year request family ---------------------------
    t_desc = hc.yearbooks_combined(("2027", "2026"))
    t_asc = hc.yearbooks_combined(("2026", "2027"))
    t_mix = hc.yearbooks_combined(("2028", "2026"))
    mix_blocks = dict((b["year"], b) for b in t_mix["yearbooks"])
    ok3 = (
        t_desc["years"] == ["2026", "2027"]
        and dump(t_desc) == dump(t_asc)
        and t_mix["years"] == ["2026", "2028"]
        and mix_blocks["2028"]["yearbook"] == []
        and t_mix["totals"] == {"years_count": 2,
                                "certified_count": 2,
                                "board_size": 4,
                                "distinct_accounts": 2}
        and t_desc["totals"] == {"years_count": 2,
                                 "certified_count": 4,
                                 "board_size": 6,
                                 "distinct_accounts": 2})
    record("AC-HYS3", ok3, "two-year family: descending"
          " ('2027','2026') folds to the ascending axis"
          " ['2026','2027'] and dumps byte-identical to the"
          " ascending request (sha16=%s); the mixed empty+content"
          " request ('2028','2026') folds to ['2026','2028'] with"
          " the 2028 honest empty block in place and"
          " distinct_accounts=2 (carol/aaron overlap counted"
          " once); the content pair totals=%s"
          % (sha16(dump(t_desc)), t_desc["totals"]))

    # -- AC-HYS4 all-empty-years request family --------------------
    e_pair = hc.yearbooks_combined(("2025", "2028"))
    e_rows = block_rows(e_pair)
    ok4 = (
        e_pair["years"] == ["2025", "2028"]
        and e_rows == [("2025", [], 0, 0), ("2028", [], 0, 0)]
        and e_pair["totals"] == {"years_count": 2,
                                 "certified_count": 0,
                                 "board_size": 0,
                                 "distinct_accounts": 0}
        and set(e_pair.keys()) == ENV_KEYS
        and all(set(b.keys()) == BLOCK_KEYS
                for b in e_pair["yearbooks"])
        and set(e_pair["totals"].keys()) == TOTALS_KEYS
        and set(s25.keys()) == ENV_KEYS)
    record("AC-HYS4", ok4, "all-empty-years family: ('2025',"
          " '2028') returns both honest empty blocks with totals=%s"
          " and the envelope/block/totals key sets stay identical"
          " to the content-year requests (key-set stability law;"
          " the empty family is structurally the same envelope,"
          " never a hide)"

          % (e_pair["totals"],))

    # -- AC-HYS5 multi-form same-set hardening ----------------------
    forms = [
        ("list-asc", ASCENDING),
        ("tuple-desc", DESCENDING),
        ("tuple-mixa", ("2027", "2025", "2028", "2026")),
        ("tuple-mixb", ("2028", "2025", "2027", "2026")),
        ("set", set(ASCENDING)),
        ("frozenset", frozenset(ASCENDING)),
        ("generator", (y for y in DESCENDING)),
    ]
    form_dumps = []
    for name, form in forms:
        res = hc.yearbooks_combined(form)
        form_dumps.append((name, res["years"], dump(res)))
    shared = form_dumps[0][2]
    all_same = all(fd[2] == shared for fd in form_dumps)
    all_axis = all(fd[1] == ASCENDING for fd in form_dumps)
    sub_a = hc.yearbooks_combined(("2026", "2027"))
    sub_b = hc.yearbooks_combined(("2027", "2026"))
    ok5 = (all_same and all_axis and dump(sub_a) == dump(sub_b))
    record("AC-HYS5", ok5, "same year set through %d input forms"
          " (list ascending, tuple descending, two scrambled"
          " tuples, set, frozenset, generator): every form folds"
          " to the identical ascending envelope (sha16=%s, all %d"
          " byte-equal=%s) - the ascending sort absorbs the"
          " per-process set iteration order drift, and the"
          " one-pass generator clears the front door, pinning"
          " the zero insertion-order-key law; the two-year subset"
          " in both orders also dumps byte-identical"
          % (len(forms), sha16(shared), len(forms), all_same))

    # -- AC-HYS6 single-source cross + pure-read law -----------------
    family = [r_desc, s26, s25, t_desc, t_mix, e_pair, sub_a]
    src_ok = True
    for res in family:
        for block in res["yearbooks"]:
            direct = hc.honor_yearbook(block["year"])
            stripped = {k: v for k, v in direct.items()
                        if k != "disclaimer"}
            if dump(stripped) != dump(block):
                src_ok = False
    before = table_counts(led_path, cv_path)
    replay = []
    for res in family:
        years = list(res["years"])
        replay.append(dump(hc.yearbooks_combined(years)))
    after = table_counts(led_path, cv_path)
    double_ok = all(
        replay[i] == dump(family[i]) for i in range(len(family)))
    ok6 = (src_ok and before == after and before["ledger_tx"] == 0
           and before["ledger_entries"] == 0 and double_ok)
    record("AC-HYS6", ok6, "single-source law across the whole"
          " request family: every block of all %d family envelopes"
          " equals honor_yearbook(year) minus disclaimer"
          " byte-for-byte (%s); the read battery leaves both-db"
          " table counts constant (%d civic + ledger tables"
          " frozen) with ledger_tx=%d and ledger_entries=%d"
          " across the whole window - certificates are platform"
          " awards and the combined face is a zero-token"
          " derivation; every family read replays byte-identical"
          " on the second call=%s"
          % (len(family), "all-equal" if src_ok else "DRIFT",
             len(before), before["ledger_tx"],
             before["ledger_entries"], double_ok))

    # -- AC-HYS7 hygiene + sha proofs + delivery --------------------
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    method_src = inspect.getsource(
        HC.HonorCertFace.yearbooks_combined)
    write_hits = [t for t in ("INSERT", "UPDATE ", "DELETE")
                  if t in method_src]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    prior = len(RESULTS)
    ok7 = (sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok and non_ascii == 0 and not net_imports
           and not write_hits and tmp_outside and prior == 6)
    record("AC-HYS7", ok7, "hygiene: shipped files untouched"
          " (config.json + honorcert/civicpoints/collectibles"
          " sha16 stable=%s); suite source pure ASCII (%d"
          " non-ascii chars), zero network imports (%d hits);"
          " yearbooks_combined method source carries zero write"
          " statements (hits=%s); world tmp outside repo (%s);"
          " criteria registered=%d"
          % (sha_ok, non_ascii, len(net_imports),
             write_hits or "none",
             "yes" if tmp_outside else "NO", prior + 1))

    cl.close()
    cv.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
