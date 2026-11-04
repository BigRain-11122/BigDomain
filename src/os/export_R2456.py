"""export_R2456 - refresh docs/status-export.json for the R2456 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
one outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2456 BUSINESS window on group dispatch D-20261105-09: the P-47 "
           "lobby sandbox is now a runnable thing - one docker-compose "
           "bring-up for the existing WebSocket server, a 19.9 entrance and "
           "month-card MOCK that never claims a real debit, a msgSecCheck "
           "local stub with the production contract, and a two-client interop "
           "demo that starts the real server and proves the acceptance cases")

base.LATEST = ("qa/lobby-interop-R2456.log (LOBBY INTEROP PASS: hello+risk "
               "first, spectator refused E_ENTRANCE_REQUIRED with zero "
               "broadcast, granted send broadcast to two connections sharing "
               "one evt_id at 0.3ms, ai_generated=false server-authoritative, "
               "blocked word refused E_CONTENT_REJECTED with a one-second "
               "listener proving no leak) + "
               "src/sandbox/lobby/docker-compose.yml + Dockerfile + "
               "requirements.txt (one-command sandbox bring-up, ws 8091 / "
               "city 8092, city_data :ro, named event-db volume, healthcheck) "
               "+ src/sandbox/lobby/pay_mock.py (chargeable=false on every "
               "object) + src/sandbox/lobby/msgsec_stub.py (PARITY-OK "
               "cases=14 stub_mismatch=0 gate_agree=14)")

base.NEXT = ("2026-11-05 12:00 acceptance receipt for D-20261105-09 is due in "
             "HQ-FEEDBACK as one line (already written this window); after "
             "that the next business increment on the same face is the real "
             "msgSecCheck transport swap and the lobby room-board read face "
             "over the shipped store, both gated only on CEO physical items "
             "for the real paths - the sandbox paths stay runnable now, and "
             "the internal tech head state/queue/tech.md:522 AC-PFKC1 stays "
             "claimable, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2456 BUSINESS window on the group dispatch D-20261105-09 "
    "(owner @BigDomain, due 2026-11-05 12:00, sandbox first, 19.9 and month "
    "card as non-chargeable mocks, msgSecCheck as local stub plus contract, "
    "no new documents). The five-silence scan did not hold: the "
    "content-addressed decisions diff read seven new tokens and one of them "
    "dispatches this company, so the window took the dispatched business face "
    "instead of the self-seeded internal tech head AC-PFKC1. SHIPPED "
    "src/sandbox/lobby/docker-compose.yml + Dockerfile + requirements.txt + "
    ".dockerignore for the already-existing P-47-1b server (one-command "
    "bring-up, ws 8091 / city read API 8092, city_data mounted read-only, "
    "event db on a named volume, ws healthcheck), src/sandbox/lobby/pay_mock.py "
    "(19.9 order -> pay -> receipt -> month-card entitlement, amount pinned to "
    "1990 cents, chargeable=false and mock=true on every object, unknown order "
    "and any real-charge attempt refused) and src/sandbox/lobby/msgsec_stub.py "
    "(WeChat msgSecCheck v2 response shape answered from the config wordlists, "
    "fail-closed when unwired, --contract publishing the endpoint the real gate "
    "must satisfy, --parity reading PARITY-OK cases=14 stub_mismatch=0 "
    "gate_agree=14 against the shipped gate). PROVED LIVE by "
    "src/sandbox/lobby/interop_demo.py, which starts the REAL server on a "
    "private port and private database and asserts in order: sys.hello then "
    "sys.risk_warning first, spectator send refused E_ENTRANCE_REQUIRED and "
    "never broadcast, sandbox-granted send broadcast to BOTH connections with "
    "one shared evt_id at 0.3ms round trip, server-authoritative "
    "ai_generated=false, blocked word refused E_CONTENT_REJECTED with a "
    "one-second listener proving the spectator received nothing - "
    "qa/lobby-interop-R2456.log reads LOBBY INTEROP PASS with eight assertion "
    "lines. Honest limits: Docker is absent on this host, so 'docker compose "
    "up' is shipped and YAML-validated but NOT claimed as executed, and the "
    "native run is the substitute; the first interop run failed on my own "
    "proof code (asyncio.TimeoutError not caught in the no-leak check) and the "
    "handler was widened, disclosed rather than silently re-run; the 19.9 path "
    "is a mock and the real merchant id, the msgSecCheck appid/secret and the "
    "public opening all remain CEO physical items. Two product points: this is "
    "the first CEO-runnable business surface this station has produced after "
    "nine internal-audit windows."
)

base.OUTS = (
    "src/sandbox/lobby/docker-compose.yml + src/sandbox/lobby/Dockerfile + "
    "src/sandbox/lobby/requirements.txt + src/sandbox/lobby/.dockerignore "
    "(one-command sandbox bring-up) + src/sandbox/lobby/pay_mock.py (19.9 "
    "non-chargeable mock) + src/sandbox/lobby/msgsec_stub.py (msgSecCheck "
    "stub + contract + parity) + src/sandbox/lobby/interop_demo.py (two-client "
    "acceptance proof) + qa/lobby-interop-R2456.log (LOBBY INTEROP PASS) + "
    "docs/status-export.json + src/os/state.json + src/os/backlog.md + "
    "heartbeat.txt + HQ-FEEDBACK.md (12:00 receipt line)"
)

if __name__ == "__main__":
    sys.exit(base.main())