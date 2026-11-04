"""closeout_R2456 - write this round state, backlog and heartbeat rows.

R2456 is the first P-47 BUSINESS window of this station: group decision
D-20261105-09 dispatched the lobby sandbox to @BigDomain for 12:00, so the
round shipped the runnable sandbox face instead of another internal audit
tool. ASCII only; all prose is English per the encoding law.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = 2456

LINES = [
    "2026-11-05 R2456 PRODUCT window on a GROUP DISPATCH, not on the internal queue: the five-silence scan "
    "did not hold because the content-addressed decisions diff read 7 new tokens, and one of them - "
    "D-20261105-09 - dispatches this company. The row confirms the pivot to the P-47 five business faces "
    "with the first delivery due 2026-11-05 12:00: a runnable docker-compose sandbox plus a minimal lobby "
    "WebSocket with two clients interop. This window did that instead of the tech head "
    "state/queue/tech.md:522 prefix AC-PFKC1, because a dispatched business face outranks a self-seeded "
    "internal audit row.",

    "2026-11-05 R2456 DECISION RECEIPTS with full numbers, since an ack without one does not count as "
    "delivery: D-20261105-09 EXECUTED and acked here (owner @BigDomain, due 11-05 12:00, sandbox first, "
    "19.9 and month card as explicit non-chargeable mocks, msgSecCheck as local stub plus contract, no new "
    "documents). D-20261105-06, D-20261105-07, D-20261105-08, D-20261105-10 and D-20261105-11 are NOT this "
    "station's execution face (group git convergence law, orders.md conflict-marker cleanup, BigCompute "
    "GPU-contention and pool/dual-write rows): read in full, acknowledged, zero action, no reply owed.",

    "2026-11-05 R2456 MEASURED, not asserted - what a CEO can actually run: src/sandbox/lobby already "
    "carried the P-47-1b server (server.py, store.py, city.py, sec_gate.py, 206KB test_client.py with "
    "AC-S1..S19) but nothing that starts it as a sandbox. SHIPPED docker-compose.yml + Dockerfile + "
    "requirements.txt + .dockerignore so the service is a one-command bring-up on any host with Docker "
    "(ports 8091 ws / 8092 city read API, city_data mounted :ro, named volume for the event db, healthcheck "
    "on the ws port), and SHIPPED src/sandbox/lobby/pay_mock.py (19.9 entrance order -> pay -> receipt -> "
    "month-card entitlement, every object carrying chargeable=false and mock=true, unknown order refused, "
    "amount pinned to the 1990-cent canon, real debit called through refuse_real_charge) and "
    "src/sandbox/lobby/msgsec_stub.py (WeChat msgSecCheck v2 response shape, wordlist-backed local answer, "
    "fail-closed when unwired, --contract printing the endpoint the real gate must satisfy, --parity "
    "proving the stub answers exactly like the shipped gate over the config lists).",

    "2026-11-05 R2456 LIVE EVIDENCE for the 12:00 acceptance item: src/sandbox/lobby/interop_demo.py starts "
    "the REAL server on a private port and a private db, then proves five cases in order - hello then risk "
    "warning first, a spectator send refused with E_ENTRANCE_REQUIRED and never broadcast, a sandbox-granted "
    "client send broadcast to BOTH connections with one shared evt_id at 0.3ms round trip, the broadcast "
    "carrying the server-authoritative ai_generated=false and actor, and a blocked word refused with "
    "E_CONTENT_REJECTED with a one-second listener proving the spectator received nothing. The run "
    "qa/lobby-interop-R2456.log reads LOBBY INTEROP PASS with all eight assertion lines; msgs ec parity reads "
    "PARITY-OK cases=14 stub_mismatch=0 gate_agree=14; py_compile is clean on all four modules and the "
    "compose file parses as YAML with the declared ports.",

    "2026-11-05 R2456 honest disclosures: (a) Docker is NOT installed on this host, so 'docker compose up' "
    "cannot be executed here and is not claimed - the compose file is shipped and YAML-validated, and the "
    "same server is proved runnable natively through interop_demo.py, which is the honest substitute; the "
    "containerised bring-up stays unproved until a host with Docker exists (physical item). (b) The first "
    "interop run FAILED on my own proof code, not on the product: the no-leak check caught the absence of a "
    "frame as asyncio.TimeoutError and only AssertionError was handled, so the demo reported FAIL after "
    "every product assertion had passed; the handler was widened and the rerun reads PASS - disclosed rather "
    "than quietly re-run. (c) The 19.9 flow is a MOCK and says so on every field; no real money path is "
    "touched and the merchant id remains a CEO physical item. (d) No new document was written, per the CEO "
    "standing order in the same dispatch batch. (e) The P-47 item 'real msgSecCheck wiring' stays blocked on "
    "the mini-program appid/secret; the contract is shipped so the swap is one transport. (f) tasks.md was "
    "not touched; the tech queue head AC-PFKC1 is carried, not dropped, and remains claimable.",

    "R2456 tokens: local=~9k api=0 api_reason=business window - one group dispatch read and acked by number, "
    "one compose definition and image for the existing P-47-1b server, one 19.9 payment mock and one "
    "msgSecCheck stub with its contract and a parity proof, one two-client interop demo run for real with "
    "eight assertions on the live server, and the state/export/backlog/heartbeat closeout; zero cloud calls "
    "and zero external API touches",
]

NEW_TOKENS = [
    "D-20261105-06",
    "D-20261105-07",
    "D-20261105-08",
    "D-20261105-09",
    "D-20261105-10",
    "D-20261105-11",
]

BACKLOG_ITEM = (
    "- [x] [done 2026-11-05 R2456] R2456 BUSINESS window on group dispatch D-20261105-09 (owner @BigDomain, "
    "due 2026-11-05 12:00): P-47 first delivery shipped as a runnable sandbox instead of another internal "
    "audit face. src/sandbox/lobby gains docker-compose.yml + Dockerfile + requirements.txt + .dockerignore "
    "(one-command bring-up, ws 8091 / city 8092, city_data :ro, event db on a named volume, ws healthcheck), "
    "pay_mock.py (19.9 entrance order -> pay -> receipt -> month-card entitlement, every object "
    "chargeable=false/mock=true, amount pinned to 1990 cents, unknown order and real-charge attempts refused) "
    "and msgsec_stub.py (WeChat msgSecCheck v2 shape, wordlist-backed, fail-closed when unwired, --contract "
    "publishes the endpoint the real gate must satisfy, --parity reads PARITY-OK cases=14 stub_mismatch=0 "
    "gate_agree=14). interop_demo.py starts the REAL server on a private port and db and proves hello+risk "
    "first, spectator refusal E_ENTRANCE_REQUIRED with no broadcast, granted send broadcast to two "
    "connections sharing one evt_id at 0.3ms, server-authoritative ai_generated=false, and blocked-word "
    "refusal E_CONTENT_REJECTED with a one-second listener proving zero leak: qa/lobby-interop-R2456.log "
    "reads LOBBY INTEROP PASS. Docker is absent on this host, so compose bring-up is shipped and "
    "YAML-validated but NOT claimed as executed; the native run is the honest substitute. Two product "
    "points, and the first CEO-runnable business surface this station has produced. The tech head "
    "state/queue/tech.md:522 AC-PFKC1 stays claimable.\n"
)


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_atomic(path, text):
    tmp = path + ".tmp-r2456"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)
    with open(path, "r", encoding="utf-8") as fh:
        back = fh.read()
    if back != text:
        raise SystemExit("E_CLOSE_R2456_READBACK " + path)


def main():
    raw = load(STATE)
    data = json.loads(raw)
    data["tick"] = ROUND
    log = data.setdefault("log", [])
    for line in LINES:
        log.append(line)
    tokens = data.get("last_dec_tokens") or []
    known = set(tokens)
    for tok in NEW_TOKENS:
        if tok not in known:
            tokens.append(tok)
            known.add(tok)
    data["last_dec_tokens"] = sorted(tokens)
    data["last_decision_rows"] = 199
    write_atomic(STATE, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    bl = load(BACKLOG)
    if "R2456 BUSINESS window on group dispatch" not in bl:
        write_atomic(BACKLOG, BACKLOG_ITEM + bl)

    hb = load(HEARTBEAT)
    if not hb.endswith("\n"):
        hb += "\n"
    hb += "tick=%d %s\n" % (ROUND, "2026-11-05T06:20:00+08:00 P-47 sandbox shipped: compose + 19.9 mock + msgSecCheck stub + two-client interop PASS")
    write_atomic(HEARTBEAT, hb)

    print("CLOSEOUT R2456 tick=%d log_added=%d tokens=%d bytes=%d"
          % (ROUND, len(LINES), len(data["last_dec_tokens"]), os.path.getsize(STATE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())