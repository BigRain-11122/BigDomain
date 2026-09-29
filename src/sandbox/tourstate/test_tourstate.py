"""Acceptance suite for the M4 visitor-end 3D three-state selection
prep face (O-2026-0929-007 @BigDomain dispatch, round R602).

Pre-registered criteria AC-TS1..AC-TS7 = src/os/backlog.md R602 row
(written before the module). Run:
    python test_tourstate.py
Prints one PASS/FAIL line per criterion, exits 0 when all pass.
"""

import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tourstate as TS  # noqa: E402 (product module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "tourstate.py")

FAILS = 0


def check(ok, label):
    global FAILS
    if not ok:
        FAILS += 1
    print("%s %s" % ("PASS" if ok else "FAIL", label), flush=True)


def expect_tamper(packet, label):
    try:
        TS.verify_packet(packet)
    except TS.TourStateError as exc:
        return exc.code == TS.E_TS_TAMPER
    return False


def ac1_three_states():
    packet = TS.build_packet(False)
    ids = [st["id"] for st in packet["states"]]
    check(ids == list(TS.STATES), "AC-TS1a states exactly three, "
          "fixed canon order: %s" % ids)
    check(all(set(st["gates"]) == set(TS.GATES)
              for st in packet["states"]), "AC-TS1b every state "
          "carries all five gates")
    check(packet["schema"] == TS.SCHEMA, "AC-TS1c schema stamped")


def ac2_l1_red_line():
    packet = TS.build_packet(False)
    gates = {st["id"]: st["gates"]["license_l1"]["status"]
             for st in packet["states"]}
    check(gates["offline_frames"] == TS.GATE_BLOCKED
          and gates["realtime3d"] == TS.GATE_BLOCKED,
          "AC-TS2a real leg: both pack-derived states G1 BLOCKED")
    check(gates["dataface"] == TS.GATE_PASS,
          "AC-TS2b real leg: dataface G1 PASS (zero pack pixels)")
    reasons = {st["id"]: st["gates"]["license_l1"]["reason"]
               for st in packet["states"]}
    check("needs-CEO purchase gate" in reasons["offline_frames"],
          "AC-TS2c blocked reason names the needs-CEO gate")
    approved = TS.build_packet(True)
    gates2 = {st["id"]: st["gates"]["license_l1"]["status"]
              for st in approved["states"]}
    check(gates2["offline_frames"] == TS.GATE_PASS
          and gates2["realtime3d"] == TS.GATE_PASS,
          "AC-TS2d hypothetical approval leg: both flip to PASS "
          "deterministically")
    check(gates2["dataface"] == TS.GATE_PASS,
          "AC-TS2e dataface G1 stays PASS on both legs")


def ac3_determinism():
    one = TS.build_packet(False)
    two = TS.build_packet(False)
    check(TS.canonical(one) == TS.canonical(two),
          "AC-TS3a double build canonical byte-identical (zero RNG)")
    check(one["packet_id"] == two["packet_id"],
          "AC-TS3b packet id identical, idempotent")
    check(len(one["packet_id"]) == 64, "AC-TS3c sha256 hex id")


def ac4_tamper():
    packet = TS.build_packet(False)
    check(TS.verify_packet(packet) is True,
          "AC-TS4a authentic packet verifies True")
    gate_flip = copy.deepcopy(packet)
    gate_flip["states"][2]["gates"]["license_l1"]["status"] = "PASS"
    check(expect_tamper(gate_flip, "gate"),
          "AC-TS4b gate-status tamper rejected E_TS_TAMPER")
    id_flip = copy.deepcopy(packet)
    id_flip["packet_id"] = "0" * 64
    check(expect_tamper(id_flip, "id"),
          "AC-TS4c packet-id tamper rejected E_TS_TAMPER")
    flag_flip = copy.deepcopy(packet)
    flag_flip["purchase_approved"] = True
    check(expect_tamper(flag_flip, "flag"),
          "AC-TS4d purchase_approved tamper rejected E_TS_TAMPER "
          "(id recomputes over the payload)")
    verdict_flip = copy.deepcopy(packet)
    verdict_flip["states"][0]["verdict"] = "gated"
    check(expect_tamper(verdict_flip, "verdict"),
          "AC-TS4e verdict tamper rejected E_TS_TAMPER")


def ac5_verdict_table():
    for approved in (False, True):
        packet = TS.build_packet(approved)
        for st in packet["states"]:
            statuses = [st["gates"][g]["status"] for g in TS.GATES]
            expected = TS.state_verdict(statuses)
            check(st["verdict"] == expected,
                  "AC-TS5 verdict derives from the gate matrix "
                  "(%s, approved=%s)" % (st["id"], approved))
    packet = TS.build_packet(False)
    verdicts = {st["id"]: st["verdict"] for st in packet["states"]}
    check(verdicts["dataface"] == "ready_now",
          "AC-TS5b dataface ready_now on the real leg")
    check(verdicts["offline_frames"] == "not_ready"
          and verdicts["realtime3d"] == "not_ready",
          "AC-TS5c pack-derived states not_ready on the real leg "
          "(blocked + pending supply gates)")


def ac6_source_red_lines():
    with open(SRC, "rb") as handle:
        raw = handle.read()
    text = raw.decode("ascii")
    check(all(b < 128 for b in raw), "AC-TS6a pure ASCII source")
    banned = re.compile(
        r"\b(sell|refund|exchange|withdraw|transfer|mint)\b")
    hits = banned.findall(text)
    check(not hits, "AC-TS6b zero banned-verb word hits: %s"
          % (hits or "none"))
    check("import random" not in text,
          "AC-TS6c zero random import")
    for net in ("urllib", "requests", "socket", "http"):
        check(("import %s" % net) not in text,
              "AC-TS6d zero network import: %s" % net)
    check("open(" not in text and "json.load" not in text,
          "AC-TS6e zero file-open / zero config read in the product "
          "module")


def ac7_approval_face():
    packet = TS.build_packet(False)
    items = packet["ceo_decisions"]
    ids = [item["id"] for item in items]
    check(ids == ["purchase_gate_l1", "three_state_selection"],
          "AC-TS7a exactly the two open CEO decisions")
    check(all(item["face"] == "needs-CEO" for item in items),
          "AC-TS7b every decision marked needs-CEO (P1 approval-only)")
    check(all(item["cost_anchor"] is None for item in items),
          "AC-TS7c zero invented cost anchors (all None, collection "
          "is a separate research item)")
    check(len(packet["selection_questions"]) == 3,
          "AC-TS7d three pre-registered selection questions")
    dropped = json.loads(TS.canonical(packet))
    check("cost_anchor\":null" in TS.canonical(dropped).replace(" ", ""),
          "AC-TS7e canonical packet carries null cost anchors only")


def main():
    ac1_three_states()
    ac2_l1_red_line()
    ac3_determinism()
    ac4_tamper()
    ac5_verdict_table()
    ac6_source_red_lines()
    ac7_approval_face()
    if FAILS == 0:
        print("SUITE PASS 7/7 (AC-TS1..AC-TS7) exit=0", flush=True)
        return 0
    print("SUITE FAIL (%d failed checks)" % FAILS, flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
