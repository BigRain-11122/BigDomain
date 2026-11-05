"""R2469 closeout state append (one-off): business window receipt."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-05 R2469 BUSINESS window, taken on the CEO standing order OB-20261105-003656-879 (real output only) and SUPERSEDING the carried internal audit row product-face-R2456 by name - that row stays open and claimable at state/queue/tech.md:522 prefix AC-PFKC1 and is CARRIED, never dropped. Five-silence scan at open: git status empty at HEAD 99f38e9f with no .git/index.lock and origin/main equal to it, zero @BigDomain rows in the evolution ledger, the content-addressed decisions diff new=0 against the stored baseline (rows 211, tokens 135), the group orders tail unchanged at 2026-11-05 00:36 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day gate, queue head AC-PFKC1 with the floor MET. FINDING before any code: the P-47-2b token double-entry ledger already ships as ledger.py (AC-L1..AC-L11: accounts, mint, reward, share, spend, adjust, balance, bill) and reconcile.py (eight honesty checks), both green in their own suites, but until today nobody could operate them without a terminal - there was no way to watch a balance move, watch the one-way fiat->token bridge book a share entry, or watch the eight checks stay PASS after a refused overdraw.",

    "2026-11-05 R2469 SHIPPED src/sandbox/ledger/ledger.html (7977B self-contained console: account field, three buttons, balance/bill/reconcile panels, zero external references, the AI label and the non-advice risk note carried verbatim from ledger config.json plus an explicit no-real-charge line) and src/sandbox/ledger/ledger_page.py (pure ASCII; GET /ledger and /ledger/ serve the page byte-identically from disk; GET /ledger/api/state publishes every balance through the SHIPPED Ledger.balance and the reconcile verdict through the SHIPPED reconcile.check_lines asked at call time; GET /ledger/api/bill returns the SHIPPED Ledger.bill; POST /ledger/api/mint, /reward and /spend drive mint_to_pool, grant_reward and spend, so the double-entry balance, the sign law, the daily cap, the content-gate reference and the schema triggers all keep exactly one owner). Bring-up: python src/sandbox/ledger/ledger_page.py --port 8097 then open http://127.0.0.1:8097/ledger/.",

    "2026-11-05 R2469 EVIDENCE, measured rather than asserted: AC-LC1..AC-LC6 were written into src/os/backlog.md BEFORE the page, the module and the suite existed (the ordering law honoured), an anchor check at HEAD put os-ledger-page, test_ledger_page and the bare names at zero executable occupancy, and src/sandbox/ledger/test_ledger_page.py reads SUITE PASS 6/6 TWICE with an identical criterion digest AC9413AB3051B0C32A33F4100507768B (qa/token-ledger-console-R2469.log, 1164B, one utf-8 LF writer, crlf=0 bom=False), each leg on its own temp database and its own OS-assigned port. Every criterion is read off a REAL server: the page is byte-identical on both slash forms, offline and carrying all three notices from config at call time; the accounts block moves when Ledger.balance is patched and the verdict moves to FAIL/failed=3 when reconcile.check_lines is patched, so neither number is canned; a mint of 100 moves pool:reward +100 and equity:auth -100 with the ledger-wide sum at exactly 0 and reconcile PASS, while an unknown pool answers 400 E_BAD_ACCOUNT and a string amount answers 400 E_BAD_AMOUNT booking nothing; a content-gated chat_mining reward is refused 403 E_GATE_REF with the balance untouched, then after record_gate_pass the same action books and the bill carries the AI label on a source_ai=TRUE row although the client sent source_ai=false (AC-L9 server authority preserved through the face, not circumvented by it); an overdraw of 9999 answers 409 E_NEGATIVE_BALANCE with the balance byte-identical and the sum still 0, then a spend of 3 books and reconcile still reads PASS; and the route surface answers 404/405 as designed with the module pure ASCII and one registry row. Registry moved exactly one row to 562 suites / 4348 criteria, and two adjacent suites stayed green (ledger 11/11, ledger-props 7/7).",

    "2026-11-05 R2469 LIVE, not a plan: qa/token-ledger-console-live-R2469.log is the real process started the way a person would start it - banner LEDGER CONSOLE with channel=sandbox-mock chargeable=false and reconcile=PASS, GET /ledger/ answered 200 at 7977 bytes carrying all three notices, GET /ledger/api/state answered 5 accounts with verdict PASS, POST /ledger/api/mint booked tx 60c4daa2d1676b9d, POST /ledger/api/reward booked, POST /ledger/api/spend of 9999 answered 409 E_NEGATIVE_BALANCE, and the state read afterwards still reads verdict PASS with the ledger-wide total at exactly 0; the process was terminated with zero survivors.",

    "2026-11-05 R2469 matrix and debt register: docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the only eligible green evidence face (qa/reconcile-all-R2468.log) through src/sandbox/suite_matrix.py --evidence plus --stamp-from and now reads 54192B, registry suites=562 criteria=4348, with --check byte-identical and its green line honestly reading 561/562 because no battery log carries the new suite yet. reconcile-battery-R2469 was opened first=no through the shipped debt_append at 121385B -> 121819B (readback=ok) because product src bytes changed and the registry moved 561->562 suites / 4342->4348 criteria, so the R2168 mixed-tree rule owes the battery next at the pre-registered 562 suites / 4348 criteria.",

    "2026-11-05 R2469 honest disclosures: (a) two business points for a face a person can click and read, and the first CEO-runnable surface this station has shipped for P-47-2b; (b) the page is served by its own process on --port 8097 and is NOT yet listed in the lobby hub payload - wiring it there would have touched server.py in the same window that already changed src bytes, so it is named here and left to the battery window; (c) the sandbox demo books tokens only: no fiat field exists anywhere, nothing is chargeable, and the real 19.9 debit plus the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (d) Docker is absent on this host, so a containerised bring-up stays unproved and is not claimed; (e) the criteria were pre-registered BEFORE the code this window, correcting nothing and repeating the R2467 ordering discipline; (f) the waterline was FOLD-DUE at open (src/os/state.json 75605B against the 78500B gate, margin 2895B) so this closeout folds the R2458 block at a true round-block boundary; (g) READ-ONLY observation outside this repo: FluxGroup/docs/orders.md still carries its leftover empty conflict markers, already reported in HQ-FEEDBACK.md; (h) tasks.md was not touched, it is the P-47 canonical board; (i) the window ran past its 25-minute budget on three suite legs, one live process and the fold, named rather than hidden.",

    "R2469 tokens: local=~13k api=0 api_reason=business window - one self-contained console page, one pure-ASCII serving module over the shipped ledger and the shipped eight-check reconcile (no second book law, no second check), six same-origin routes, one six-criteria suite proved twice with an identical digest plus two adjacent suites re-run green, one real-process live capture, one registry row, one stamp-aligned matrix regeneration with a byte-identical check, one battery debt row appended through its shipped CLI, one waterline fold, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return
    state["tick"] = 2469
    state["log"].extend(LINES)
    state["last_decision_rows"] = 289
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"]) and back["tick"] == 2469)
    print("APPEND tick=%d log_items=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), os.path.getsize(PATH),
             "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())