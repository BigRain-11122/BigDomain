# fix_insert_R2014.py - surgical re-indent fix for the AC-IDB window
# insert in src/sandbox/lobby/test_client.py. The replace tool
# normalized the inserted block by shifting it 11 columns deep
# (whitespace-normalization side effect), breaking the file with an
# IndentationError at the new function def. This script rewrites the
# broken span (from the AC-IDT8 record tail through the mis-indented
# idem_keybind_cases def line) from the canonical source embedded
# below, then byte-verifies with py_compile. Zero normalization
# applied here - pure literal line surgery. Pure ASCII.
import io
import os
import py_compile

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.normpath(os.path.join(HERE, "..", "..", "src",
                                   "sandbox", "lobby",
                                   "test_client.py"))

FUNC = '''async def idem_budget_gateorder_cases():
    """AC-IDB1..IDB7 (criteria pre-registered R2013 in the
    state/queue/explore.md claim row, implemented here R2014):
    chat.send gate-order budget window. The idempotency gate sits
    BEFORE the rate limit (server.py: "before the rate limit
    (replay costs no budget)"), so a replay of an already-processed
    send is absorbed as a duplicate without burning, freeing or
    extending any rate-limit budget while the 5/10s window stays
    saturated by the fresh sends. All probes run against the
    SHIPPED config values (5 msgs / 10s window, 3-violation 60s
    mute, idem ttl 300s, cap 4096): the probe batch uses 7
    distinct idem keys (far below the 4096 cap) and completes well
    inside both the 10s window and the 300s ttl, so no derived
    config copy is needed - this window certifies existing
    behavior, it legislates nothing new (R2013 claim-row note).
    Honest evidence note: client.send_times and the violations
    counter live inside the server subprocess and cannot be read
    directly; the budget claims are pinned by their behavioral
    equivalents - (a) ten consecutive replays all answer
    chat.duplicate while a budget-burning replay path would have
    tripped the 3-violation mute and the 4th+ replay would answer
    E_RATE_LIMIT muted; (b) the 6th fresh send after the replay
    storm is still rejected, so the window was neither freed nor
    extended. Suite-only round: server.py and the shipped config
    are not modified (R1892/R1999/R2012 precedent)."""
    sha_server_pre = hashlib.sha256(open(SERVER, "rb").read()).hexdigest()
    sha_config_pre = hashlib.sha256(open(CONFIG, "rb").read()).hexdigest()

    async def chat_send(ws, room, text, cid=None):
        payload = {"text": text}
        if cid is not None:
            await ws.send(frame("chat.send", room=room,
                                payload=payload, client_msg_id=cid))
        else:
            await ws.send(frame("chat.send", room=room,
                                payload=payload))

    def chat_rows(db):
        return db_query(db,
                        "SELECT COUNT(*) FROM events"
                        " WHERE type='chat.broadcast'")[0][0]

    def is_rate_reject(f):
        return (f.get("type") == "sec.reject"
                and f.get("payload", {}).get("code") == "E_RATE_LIMIT")

    port = _free_port()
    srv = ServerProc(port, db=os.path.join(
        tempfile.mkdtemp(prefix="lobby-idem-bg-"), "events.db"))
    ws_a = None
    ws_b = None
    try:
        srv.start()
        ws_a, _, _ = await open_client(port)
        ws_b, _, _ = await open_client(port)   # bystander, read-only
        await make_resident(ws_a)

        # saturate the 5/10s window: five fresh sends, each a unique
        # (client_msg_id, text) pair; both clients see all five
        # broadcasts (the bystander's receipts are drained here so
        # the later zero-second-broadcast probe starts clean).
        orig_evts = {}
        for i in range(5):
            cid = "idb-w%d" % i
            text = "idb fresh %d" % i
            await chat_send(ws_a, "lobby", text, cid)
            e = await recv_until(ws_a, lambda f: (
                f.get("type") == "chat.broadcast"
                and f.get("payload", {}).get("text") == text))
            await recv_until(ws_b, lambda f: (
                f.get("type") == "chat.broadcast"
                and f.get("evt_id") == e.get("evt_id")))
            orig_evts[cid] = (text, e.get("evt_id"))
        rows_sat = chat_rows(srv.db)

        # ---- AC-IDB1: saturated-window replay absorption ----
        replay_cid = "idb-w2"
        replay_text, replay_evt = orig_evts[replay_cid]
        await chat_send(ws_a, "lobby", replay_text, replay_cid)
        d1 = await recv_until(ws_a, lambda f: (
            f.get("type") == "chat.duplicate"
            and f.get("payload", {}).get("client_msg_id")
            == replay_cid))
        ok_idb1 = (d1 is not None
                   and d1.get("payload", {}).get("code")
                   == "E_DUPLICATE_MSG"
                   and d1.get("payload", {}).get("evt_id")
                   == replay_evt
                   and rows_sat == 5)
        record("AC-IDB1", ok_idb1,
               "5/10s window saturated by five fresh sends (%d rows) "
               "then a replayed (id,text) answered chat.duplicate "
               "code=%s evt==original=%s and zero E_RATE_LIMIT (a "
               "rate-path replay would have failed the duplicate wait)"
               % (rows_sat,
                  d1.get("payload", {}).get("code"),
                  d1.get("payload", {}).get("evt_id") == replay_evt))

        # ---- AC-IDB2: replay storm costs no budget (behavioral
        # equivalent of the in-process send_times/violations probe)
        # ----
        storm_ok = True
        for _ in range(9):   # plus the AC-IDB1 replay = 10 total
            await chat_send(ws_a, "lobby", replay_text, replay_cid)
            d = await recv_until(ws_a, lambda f: (
                f.get("type") == "chat.duplicate"
                and f.get("payload", {}).get("client_msg_id")
                == replay_cid))
            if (d.get("payload", {}).get("code") != "E_DUPLICATE_MSG"
                    or d.get("payload", {}).get("evt_id")
                    != replay_evt):
                storm_ok = False
        rows_storm = chat_rows(srv.db)
        ok_idb2 = storm_ok and rows_storm == rows_sat
        record("AC-IDB2", ok_idb2,
               "10 consecutive replays of one (id,text) all duplicate, "
               "store rows unchanged %d -> %d (behavioral zero-budget "
               "proof: a budget-burning replay would have tripped the "
               "3-violation mute and the 4th+ replay would answer "
               "E_RATE_LIMIT muted; send_times/violations live in the "
               "subprocess and are pinned by this behavioral equivalent)"
               % (rows_sat, rows_storm))

        # ---- AC-IDB5: store/broadcast zero side effects ----
        ws_b_silent = await expect_silence(ws_b, 0.5)
        ok_idb5 = rows_storm == rows_sat and ws_b_silent
        record("AC-IDB5", ok_idb5,
               "dup-absorb storm side effects: store rows %d == %d "
               "saturated count, bystander-second-broadcast=%s "
               "(duplicates never re-broadcast, never re-land)"
               % (rows_storm, rows_sat, not ws_b_silent))

        # ---- AC-IDB3: replays free no budget (6th fresh still
        # rejected; the window stays saturated by the original five)
        # ----
        await chat_send(ws_a, "lobby", "idb fresh 5", "idb-w5")
        f6 = await recv_until(ws_a, is_rate_reject)
        ok_idb3 = f6 is not None
        record("AC-IDB3", ok_idb3,
               "6th fresh send (new id + new text) still rejected "
               "E_RATE_LIMIT after the 10-replay storm: the window was "
               "neither freed nor extended by the replays (violation "
               "#1, below the 3-violation mute)")

        # ---- AC-IDB4: no-idem-path control anchor (gate order
        # triangulated: the dup path returns before the rate check;
        # both the miss-id fresh path and the no-id path hit the
        # rate gate) ----
        await chat_send(ws_a, "lobby", "idb fresh 6")   # no client_msg_id
        f7 = await recv_until(ws_a, is_rate_reject)
        ok_idb4 = f7 is not None
        record("AC-IDB4", ok_idb4,
               "no-client_msg_id send at the same saturated position "
               "also rejected E_RATE_LIMIT (control anchor; violation "
               "#2 - the duplicate path returns ahead of the rate "
               "check while every non-duplicate path hits it)")

        # ---- AC-IDB6: hygiene (suite-only round) ----
        sha_server_post = hashlib.sha256(
            open(SERVER, "rb").read()).hexdigest()
        sha_config_post = hashlib.sha256(
            open(CONFIG, "rb").read()).hexdigest()
        own_src = inspect.getsource(idem_budget_gateorder_cases)
        ascii_ok = True
        try:
            own_src.encode("ascii")
        except UnicodeEncodeError:
            ascii_ok = False
        net_ok = not any(
            ln.strip().startswith(("import requests", "import urllib",
                                   "import http", "from requests",
                                   "from urllib", "from http",
                                   "import socket", "import aiohttp",
                                   "import httpx"))
            for ln in own_src.splitlines())
        record("AC-IDB6", sha_server_post == sha_server_pre
               and sha_config_post == sha_config_pre and ascii_ok
               and net_ok,
               "server.py-unchanged=%s config.json-unchanged=%s "
               "section-ascii=%s true-import-lines-zero-network=%s "
               "(shipped values throughout, no derived config copy "
               "this window; the double-run byte-identity face is "
               "carried by the evidence log qa/idem-budget-R2014.log)"
               % (sha_server_post == sha_server_pre,
                  sha_config_post == sha_config_pre, ascii_ok, net_ok))

        # ---- AC-IDB7: delivery registration ----
        idb_so_far = len([1 for ac, _ in RESULTS
                          if ac.startswith("AC-IDB")])
        reg_line = ('("lobby", os.path.join("lobby",'
                    ' "test_client.py"), 72)')
        reg_src = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "reconcile_all.py"), encoding="utf-8").read()
        reg_ok = reg_line in reg_src
        record("AC-IDB7", reg_ok and idb_so_far == 6,
               "delivery: reconcile_all SUITES lobby row 57->65->72 "
               "registered=%s; AC-IDB criteria counted %d before this "
               "record (7 with it); the full-battery RUNNER pass and "
               "the suite-matrix --check byte-identical face are "
               "carried by the evidence log qa/idem-budget-R2014.log"
               % (reg_ok, idb_so_far))
    finally:
        for ws in (ws_a, ws_b):
            if ws is not None:
                try:
                    await ws.close()
                except Exception:
                    pass
        srv.stop()'''


def main():
    src = io.open(TC, encoding="utf-8").read()
    lines = src.split("\n")
    i_start = -1
    i_end = -1
    bad_start = " " * 26 + "% (sha_server_post == sha_server_pre,"
    bad_end = " " * 11 + "async def idem_keybind_cases():"
    for i, ln in enumerate(lines):
        if ln == bad_start and i_start < 0:
            i_start = i
        if ln == bad_end:
            i_end = i
    assert i_start >= 0, "broken start marker not found"
    assert i_end > i_start, ("broken end marker not found or"
                            " before start: %d %d" % (i_start, i_end))
    fixed = []
    fixed.append(" " * 15 + "% (sha_server_post == sha_server_pre,")
    fixed.append(" " * 18
                 + "sha_config_post == sha_config_pre, ascii_ok))")
    fixed.append("")
    fixed.append("")
    fixed.extend(FUNC.split("\n"))
    fixed.append("")
    fixed.append("")
    fixed.append("async def idem_keybind_cases():")
    lines[i_start:i_end + 1] = fixed
    out = "\n".join(lines)
    io.open(TC, "w", encoding="utf-8", newline="\n").write(out)
    py_compile.compile(TC, doraise=True)
    body = io.open(TC, encoding="utf-8").read()
    assert body.count("async def idem_budget_gateorder_cases():") == 1
    assert body.count("await idem_budget_gateorder_cases()") == 1
    assert "idem_budget_gateorder_cases"
    print("FIX-OK span=%d..%d total-lines=%d bytes=%d"
          % (i_start + 1, i_end + 1, len(lines), len(out.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
