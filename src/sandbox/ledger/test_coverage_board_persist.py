"""Cross-restart persistence suite for the dataset-subscription
coverage board (BigDomain R1984; FIFO-head claim of the R1982
reseed row - the strict file-order topmost open non-gated claim
after the L13/L21 standing gated rows; the L59 lobby stdout
hardening window is deferred as a heavy window per the R1983
export note; persist-example family R1886 lineage).
Asserts the pre-registered criteria AC-COVP1..AC-COVP7 from the
explore.md claim row (criteria were registered before this code
existed; honesty law). The board is a pure read-time derivation
over the datasub sqlite tables - zero cache counters, zero time
keys in the board envelope, so the restart law is byte identity
of the whole board envelope. Evidence stdout carries no raw
utc/tx values (masked-digest law R1941): the double run is
byte-identical.

Usage: python test_coverage_board_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                    # noqa: E402 (P-47-2b core)
import datasub as S                   # noqa: E402 (R1764 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: dataset subscriptions"
              " deliver city aggregate data, not investment advice")

ROW_KEYS = {"dataset_key", "title", "period", "ai_label",
            "subscribers", "subscriptions", "deliveries"}
ENV_KEYS = {"coverage_board", "disclaimer"}

ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
HEX16_RE = re.compile(r"\b[0-9a-f]{16,}\b")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha16(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]


def io_read(path):
    with open(path, "rb") as handle:
        return handle.read()


def masked_digest(obj):
    text = json.dumps(obj, sort_keys=True)
    text = ISO_RE.sub("<TS>", text)
    text = HEX16_RE.sub("<TX16>", text)
    return sha16(text)


def expect_error(fn, code):
    try:
        fn()
    except S.DataSubError as exc:
        return exc.code == code, exc.code
    return False, "no-error-raised"


def board_dump(face):
    return json.dumps(face.coverage_board(), sort_keys=True)


def ds_counts(ds_path):
    conn = sqlite3.connect(ds_path)
    out = {}
    for name in ("dataset_registry", "dataset_subscriptions",
                 "dataset_deliveries"):
        out[name] = int(conn.execute(
            "SELECT COUNT(*) FROM " + name).fetchone()[0])
    conn.close()
    return out


def ds_rows(ds_path):
    conn = sqlite3.connect(ds_path)
    out = {}
    out["registry"] = [list(r) for r in conn.execute(
        "SELECT dataset_key, title, period, price_cent,"
        " dataset_digest, ai_label, registered_utc"
        " FROM dataset_registry ORDER BY rowid").fetchall()]
    out["subs"] = [list(r) for r in conn.execute(
        "SELECT sub_id, account, dataset_key, period_window,"
        " purchase_ref, price_cent, bound_spend_tx, subscribed_utc"
        " FROM dataset_subscriptions ORDER BY sub_id").fetchall()]
    out["deliv"] = [list(r) for r in conn.execute(
        "SELECT delivery_ref, account, dataset_key, period_window,"
        " delivered_utc FROM dataset_deliveries"
        " ORDER BY rowid").fetchall()]
    conn.close()
    return out


def ledger_counts(db_path):
    conn = sqlite3.connect(db_path)
    total = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    spend = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
        ).fetchone()[0])
    conn.close()
    return {"tx_total": total, "spend": spend}


def manual_board(ds_path):
    """Independent second derivation (direct SQL GROUP BY) for the
    AC-COVP1 cross check - never the product's own code path."""
    conn = sqlite3.connect(ds_path)
    regs = conn.execute(
        "SELECT dataset_key FROM dataset_registry").fetchall()
    subs = {r[0]: (int(r[1]), int(r[2])) for r in conn.execute(
        "SELECT dataset_key, COUNT(*), COUNT(DISTINCT account)"
        " FROM dataset_subscriptions GROUP BY dataset_key").fetchall()}
    dels = {r[0]: int(r[1]) for r in conn.execute(
        "SELECT dataset_key, COUNT(*) FROM dataset_deliveries"
        " GROUP BY dataset_key").fetchall()}
    conn.close()
    out = {}
    for (key,) in regs:
        n_rows, n_hh = subs.get(key, (0, 0))
        out[key] = {"subscribers": n_hh, "subscriptions": n_rows,
                    "deliveries": dels.get(key, 0)}
    return out


def probe_batch(face, tag):
    """Five fail-closed gate probes; every rejection must fire
    before any write. Returns (codes, all_ok)."""
    codes = []
    all_ok = True
    probes = [
        ("dup-window",
         lambda: face.subscribe("usr:ada", "city-mobility",
                                "2026-01", "fresh-" + tag + "-a"),
         S.E_DSB_DUP),
        ("dup-ref",
         lambda: face.subscribe("usr:carol", "city-mobility",
                                 "2026-11", "dsp-ada-0101"),
         S.E_DSB_DUP),
        ("not-subscribed",
         lambda: face.deliver("usr:ada", "city-mobility",
                              "2026-11", "dlv-" + tag + "-b"),
         S.E_DSB_NOT_SUBSCRIBED),
        ("unknown-dataset",
         lambda: face.subscribe("usr:carol", "city-nope",
                                "2026-11", "fresh-" + tag + "-c"),
         S.E_DSB_UNKNOWN_DATASET),
        ("bad-window",
         lambda: face.subscribe("usr:carol", "city-mobility",
                                "2026-Q1", "fresh-" + tag + "-d"),
         S.E_DSB_BAD_WINDOW),
    ]
    for name, fn, want in probes:
        ok, code = expect_error(fn, want)
        codes.append(name + "=" + (code if ok else "WRONG:" + str(code)))
        all_ok &= ok
    return codes, all_ok


def build_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    face = S.DatasetSubscriptionFace(led, DISCLAIMER)
    return led, face


def main():
    tmp = tempfile.mkdtemp(prefix="covboard-persist-")
    cfg = json.loads(io_read(os.path.join(BASE, "config.json"))
                     .decode("utf-8"))
    cfg_sha_before = sha16(io_read(os.path.join(BASE, "config.json")))
    ds_sha_before = sha16(io_read(os.path.join(BASE, "datasub.py")))
    led_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    db_path = os.path.join(tmp, "ledger.db")

    led, ds = build_stack(db_path, cfg)
    led.mint_to_pool("pool:reserve", 20000, "COVP-MINT-A", "settlement")
    for who in ("ada", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 2000),
                ("usr:ada", "credit", 2000)],
               "manual:covp-fund-ada", "persist window funding ada")
    led.adjust([("pool:reserve", "debit", 3000),
                ("usr:bob", "credit", 3000)],
               "manual:covp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 1000),
                ("usr:carol", "credit", 1000)],
               "manual:covp-fund-carol",
               "persist window funding carol")

    # -- AC-COVP1: anchor world + pre-close board pinning ----------
    ds.register_dataset("city-mobility", "City Mobility Index",
                        "monthly", 99, "digest-mob-1", False)
    ds.register_dataset("city-quarterly", "City Economy Quarterly",
                        "quarterly", 999, "digest-q-1", True)
    ds.register_dataset("city-air", "City Air Quality Readings",
                        "monthly", 49, "digest-air-1", True)
    ds.subscribe("usr:ada", "city-mobility", "2026-01",
                 "dsp-ada-0101")
    ds.subscribe("usr:ada", "city-mobility", "2026-12",
                 "dsp-ada-1212")
    ds.subscribe("usr:carol", "city-mobility", "2026-10",
                 "dsp-carol-1010")
    ds.subscribe("usr:bob", "city-quarterly", "2026-Q1",
                 "dsp-bob-q1")
    ds.deliver("usr:carol", "city-mobility", "2026-10",
               "dsp-dlv-carol-1")
    ds.deliver("usr:carol", "city-mobility", "2026-10",
               "dsp-dlv-carol-2")
    ds.deliver("usr:ada", "city-mobility", "2026-01",
               "dsp-dlv-ada-01")

    snap_board = board_dump(ds)
    pre_counts = ds_counts(ds.db_path)
    pre_led = ledger_counts(db_path)
    codes_pre, gates_pre_ok = probe_batch(ds, "pre")
    post_counts = ds_counts(ds.db_path)
    post_led = ledger_counts(db_path)

    board = json.loads(snap_board)
    rows = board["coverage_board"]
    man = manual_board(ds.db_path)
    view_mob = ds.dataset_view("city-mobility")
    view_q = ds.dataset_view("city-quarterly")
    view_air = ds.dataset_view("city-air")

    ok1 = (
        gates_pre_ok
        and [c.split("=", 1)[1] for c in codes_pre]
        == ["E_DSB_DUP", "E_DSB_DUP", "E_DSB_NOT_SUBSCRIBED",
            "E_DSB_UNKNOWN_DATASET", "E_DSB_BAD_WINDOW"]
        and pre_counts == post_counts
        and pre_led == post_led
        and set(board.keys()) == ENV_KEYS
        and len(rows) == 3
        and all(set(r.keys()) == ROW_KEYS for r in rows)
        and rows[0]["dataset_key"] == "city-mobility"
        and rows[0]["subscribers"] == 2
        and rows[0]["subscriptions"] == 3
        and rows[0]["deliveries"] == 3
        and rows[0]["ai_label"] == 0
        and rows[1]["dataset_key"] == "city-quarterly"
        and rows[1]["subscribers"] == 1
        and rows[1]["subscriptions"] == 1
        and rows[1]["deliveries"] == 0
        and rows[1]["ai_label"] == 1
        and rows[2]["dataset_key"] == "city-air"
        and rows[2]["subscribers"] == 0
        and rows[2]["subscriptions"] == 0
        and rows[2]["deliveries"] == 0
        and rows[2]["ai_label"] == 1
        and all(r["subscribers"] == man[r["dataset_key"]]["subscribers"]
                and r["subscriptions"]
                == man[r["dataset_key"]]["subscriptions"]
                and r["deliveries"]
                == man[r["dataset_key"]]["deliveries"]
                for r in rows)
        and rows[0]["subscriptions"] == view_mob["subscriber_count"]
        and rows[1]["subscriptions"] == view_q["subscriber_count"]
        and rows[2]["subscriptions"] == view_air["subscriber_count"]
        and board["disclaimer"] == DISCLAIMER
    )
    record("AC-COVP1", ok1,
           "anchor world: 3 registry rows (mobility/q/air), board "
           "ranks mobility {2hh,3subs,3dlv} > quarterly {1,1,0} > "
           "air {0,0,0} honest-zero, seven row keys + two envelope "
           "keys exact, manual SQL GROUP BY cross == board, "
           "dataset_view subscriber_count reconcile x3, five gate "
           "probes rejected [" + "; ".join(codes_pre) + "] with "
           "zero side effects (ds counts %s, ledger %s)" %
           (json.dumps(pre_counts, sort_keys=True),
            json.dumps(pre_led, sort_keys=True)))

    pre_rows = ds_rows(ds.db_path)

    # -- AC-COVP2: close -> reopen, board byte identity -------------
    ds.close()
    led.close()
    led2, ds2 = build_stack(db_path, cfg)
    reopen_board = board_dump(ds2)
    reopen_double = board_dump(ds2)
    ok2 = (reopen_board == snap_board and reopen_double == snap_board)
    record("AC-COVP2", ok2,
           "two-piece restart (face.close + ledger.close -> new "
           "Ledger + new face over the same db paths): reopened "
           "coverage_board byte-identical to the pre-close "
           "snapshot (sort_keys dumps, sha16 %s) and the same-param "
           "double read is self-identical - zero in-memory drift "
           "in the derived board face" % sha16(reopen_board))

    # -- AC-COVP3: post-restart live continuation -------------------
    codes2, gates2_ok = probe_batch(ds2, "post")
    cnt2_before = ds_counts(ds2.db_path)
    led2_before = ledger_counts(db_path)
    ds2.subscribe("usr:bob", "city-mobility", "2026-11",
                  "dsp-bob-1111")
    ds2.register_dataset("city-parks", "City Parks Usage Digest",
                         "monthly", 59, "digest-parks-1", False)
    ds2.deliver("usr:ada", "city-mobility", "2026-12",
                "dsp-dlv-ada-12")
    cnt2_after = ds_counts(ds2.db_path)
    led2_after = ledger_counts(db_path)
    board2 = json.loads(board_dump(ds2))
    rows2 = board2["coverage_board"]
    mob2 = [r for r in rows2 if r["dataset_key"] == "city-mobility"][0]
    q2 = [r for r in rows2 if r["dataset_key"] == "city-quarterly"][0]
    air2 = [r for r in rows2 if r["dataset_key"] == "city-air"][0]
    parks2 = [r for r in rows2 if r["dataset_key"] == "city-parks"][0]
    pre_rows_by_key = {r["dataset_key"]: r for r in rows}

    ok3 = (
        gates2_ok
        and board_dump(ds2) != snap_board
        and len(rows2) == 4
        and mob2["subscribers"] == 3
        and mob2["subscriptions"] == 4
        and mob2["deliveries"] == 4
        and cnt2_after["dataset_subscriptions"]
        == cnt2_before["dataset_subscriptions"] + 1
        and cnt2_after["dataset_registry"]
        == cnt2_before["dataset_registry"] + 1
        and cnt2_after["dataset_deliveries"]
        == cnt2_before["dataset_deliveries"] + 1
        and led2_after["spend"] == led2_before["spend"] + 1
        and parks2["subscribers"] == 0
        and parks2["subscriptions"] == 0
        and parks2["deliveries"] == 0
        and rows2[0]["dataset_key"] == "city-mobility"
        and rows2[1]["dataset_key"] == "city-quarterly"
        and rows2[2]["dataset_key"] == "city-air"
        and rows2[3]["dataset_key"] == "city-parks"
        and json.dumps(q2, sort_keys=True)
        == json.dumps(pre_rows_by_key["city-quarterly"],
                      sort_keys=True)
        and json.dumps(air2, sort_keys=True)
        == json.dumps(pre_rows_by_key["city-air"], sort_keys=True)
    )
    record("AC-COVP3", ok3,
           "post-restart live continuation: gates replayed clean, "
           "new bob mobility 2026-11 subscription (real spend, "
           "spend tx %d -> %d), new city-parks registration lands "
           "as an honest zero row at the dictionary tail (air < "
           "parks tie-break live), new ada 2026-12 delivery: "
           "mobility recomputes {3hh,4subs,4dlv} != pre-close "
           "board (zero cache), untouched quarterly/air rows "
           "byte-frozen" %
           (led2_before["spend"], led2_after["spend"]))

    # -- AC-COVP4: gate codes stable across the restart -------------
    ok4 = gates2_ok and codes2 == codes_pre
    cnt2_probe = ds_counts(ds2.db_path)
    led2_probe = ledger_counts(db_path)
    record("AC-COVP4", ok4 and cnt2_probe == cnt2_after
           and led2_probe == led2_after,
           "five-gate probe batch on the reopened instance rejects "
           "with the identical code sequence [" +
           "; ".join(codes2) + "] and zero side effects (ds "
           "counts %s unchanged, ledger %s unchanged)" %
           (json.dumps(cnt2_probe, sort_keys=True),
            json.dumps(led2_probe, sort_keys=True)))

    # -- AC-COVP5: append-only frozen anchors -----------------------
    post_rows = ds_rows(ds2.db_path)
    frozen = (
        post_rows["registry"][:len(pre_rows["registry"])]
        == pre_rows["registry"]
        and post_rows["subs"][:len(pre_rows["subs"])]
        == pre_rows["subs"]
        and post_rows["deliv"][:len(pre_rows["deliv"])]
        == pre_rows["deliv"]
    )
    dconn = sqlite3.connect(ds2.db_path)
    bound = [r[0] for r in dconn.execute(
        "SELECT bound_spend_tx FROM dataset_subscriptions"
        " WHERE purchase_ref = 'dsp-bob-1111'").fetchall()]
    dconn.close()
    conn = sqlite3.connect(db_path)
    tx_hits = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
        " AND tx_id = ?", (bound[0],)).fetchone()[0]) if bound else 0
    conn.close()
    view_mob2 = ds2.dataset_view("city-mobility")
    ok5 = (frozen and tx_hits == 1
           and view_mob2["subscriber_count"] == 4)
    record("AC-COVP5", ok5,
           "append-only frozen anchors: pre-restart registry/subs/"
           "delivery row prefixes byte-frozen across the restart + "
           "continuation double raid (masked digest %s / %s), the "
           "new subscription row's bound_spend_tx resolves to a "
           "real ledger spend tx (SQL cross hit=%d), post-"
           "continuation dataset_view reconcile mobility "
           "subscriber_count=4" %
           (masked_digest(pre_rows), masked_digest(
               {k: v[:len(pre_rows[k])]
                for k, v in post_rows.items()}), tx_hits))

    # -- AC-COVP6: pure-read law ------------------------------------
    read_a = board_dump(ds2)
    read_b = board_dump(ds2)
    cnt_read = ds_counts(ds2.db_path)
    led_read = ledger_counts(db_path)
    ok6 = (read_a == read_b and cnt_read == cnt2_after
           and led_read == led2_after)
    record("AC-COVP6", ok6,
           "pure-read law: coverage_board double read byte-"
           "identical (sha16 %s), read battery leaves every ds "
           "table count and the ledger spend count untouched "
           "(%s / %s)" %
           (sha16(read_a), json.dumps(cnt_read, sort_keys=True),
            json.dumps(led_read, sort_keys=True)))

    # -- AC-COVP7: third instance + hygiene -------------------------
    term_board = board_dump(ds2)
    ds2.close()
    led2.close()
    led3, ds3 = build_stack(db_path, cfg)
    third_board = board_dump(ds3)
    third_double = board_dump(ds3)
    src_text = io_read(os.path.abspath(__file__)).decode("utf-8")
    import_lines = [l.strip() for l in src_text.split("\n")
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_hits = [l for l in import_lines
                if re.search(r"\b(urllib|requests|socket|http)\b", l)]
    ok7 = (
        third_board == term_board
        and third_double == term_board
        and all(ord(ch) < 128 for ch in src_text)
        and not net_hits
        and sha16(io_read(os.path.join(BASE, "config.json")))
        == cfg_sha_before
        and sha16(io_read(os.path.join(BASE, "datasub.py")))
        == ds_sha_before
        and sha16(io_read(os.path.join(BASE, "ledger.py")))
        == led_sha_before
        and len(RESULTS) == 6
        and tmp.startswith(tempfile.gettempdir())
    )
    record("AC-COVP7", ok7,
           "third instance over the same db paths reproduces the "
           "instance-2 terminal board byte-identically; suite-only "
           "round: datasub.py/ledger.py/config.json sha16 unchanged "
           "(%s/%s), suite source pure ASCII, real import lines "
           "carry zero network libs, world in tmp outside the repo" %
           (ds_sha_before, led_sha_before))

    ds3.close()
    led3.close()

    bad = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d%s" % (
        "PASS" if not bad else "FAIL", len(RESULTS) - len(bad),
        len(RESULTS),
        "" if not bad else " failed=" + ",".join(bad)), flush=True)
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
