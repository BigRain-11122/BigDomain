"""Acceptance suite for the minor guardian guard face (BigDomain R937).

Asserts AC-MG1..AC-MG7 pre-registered in src/os/backlog.md (R937
claim row, registered before implementation - honesty law). Legal
anchors: Regulations on the Cyber Protection of Minors sec.43-44 /
sec.31 / sec.24(3) (benchmark G slice 2026-10-02, wall W11).

Scenario dates/minutes are caller-supplied (no wall clock), so every
assertion is deterministic. ASCII-only suite per encoding law.

Usage: python test_minors.py
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from minors import GuardError, MinorGuardFace, render_report  # noqa: E402

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s - %s" % ("PASS" if ok else "FAIL", ac, evidence))


def expect_reject(ac, fn, code, evidence):
    try:
        fn()
    except GuardError as ge:
        record(ac, ge.code == code,
               "%s (want %s, got %s)" % (evidence, code, ge.code))
        return ge.code == code
    record(ac, False, "%s - no refusal raised" % evidence)
    return False


def main():
    # -- AC-MG1: registration + guardian binding -------------------
    f = MinorGuardFace()
    f.register_resident("kid1", True, "guardianA")
    f.register_resident("adult1", False)
    expect_reject("AC-MG1", lambda: f.register_resident(
        "kid2", True), "E_MG_GUARDIAN", "minor without guardian refused")
    expect_reject("AC-MG1", lambda: f.register_resident(
        "kid1", True, "guardianB"), "E_MG_DUP", "duplicate refused")
    rec = f.residents_readout()
    ok = (rec["kid1"]["minor"] and rec["kid1"]["guardian"] == "guardianA"
          and rec["adult1"]["minor"] is False)
    record("AC-MG1", ok, "kid1 bound to guardianA; adult1 guardian-free")

    # -- AC-MG2: time-window gate (sec.43) ---------------------------
    f.set_guardian_limits("guardianA", "kid1",
                          allowed_windows=[(1080, 1200)],
                          single_cent=1000, daily_cent=1500)
    got = f.check_time("kid1", 1100, "2026-10-02")
    record("AC-MG2", got["allowed"] and got["window"] == "1080-1200",
           "in-window pass (18:20)")
    expect_reject("AC-MG2", lambda: f.check_time(
        "kid1", 1300, "2026-10-02"), "E_MG_TIME",
        "outside window refused (sec.43)")
    g = MinorGuardFace()
    g.register_resident("kidX", True, "guardX")
    expect_reject("AC-MG2", lambda: g.check_time(
        "kidX", 1100, "2026-10-02"), "E_MG_NO_LIMIT",
        "no guardian limits configured -> fail-closed")

    # -- AC-MG3: spend gate single + daily (sec.44) ------------------
    expect_reject("AC-MG3", lambda: f.check_spend(
        "kid1", 1500, "2026-10-02"), "E_MG_SPEND_SINGLE",
        "single-purchase over limit refused, zero billed")
    f.record_spend("kid1", 800, "2026-10-02", "tx-sub-1")
    expect_reject("AC-MG3", lambda: f.check_spend(
        "kid1", 800, "2026-10-02"), "E_MG_SPEND_DAILY",
        "daily accumulation over limit refused, zero billed")
    expect_reject("AC-MG3", lambda: g.check_spend(
        "kidX", 100, "2026-10-02"), "E_MG_NO_LIMIT",
        "unconfigured limits refuse billing ([needs-CEO] no defaults)")
    day = f.day_readout("kid1", "2026-10-02")
    record("AC-MG3", day["spent_cent"] == 800 and day["events"] ==
           ["tx-sub-1"], "refusals mutated nothing: 800/tx-sub-1 only")

    # -- AC-MG4: live ban (sec.31) + marketing ban (sec.24(3)) -------
    expect_reject("AC-MG4", lambda: f.check_live("kid1"),
                  "E_MG_LIVE_BAN", "minor live opening banned (sec.31)")
    expect_reject("AC-MG4", lambda: f.check_marketing("kid1"),
                  "E_MG_MARKETING_BAN",
                  "automated marketing push to minor banned (sec.24(3))")

    # -- AC-MG5: adults pass through (minor-only scope) --------------
    ok = (f.check_time("adult1", 300, "2026-10-02")["scope"] == "adult"
          and f.check_spend("adult1", 999999, "2026-10-02")["scope"]
          == "adult"
          and f.check_live("adult1")["allowed"]
          and f.check_marketing("adult1")["allowed"])
    record("AC-MG5", ok, "adult pass-through on all four gates")
    expect_reject("AC-MG5", lambda: f.set_guardian_limits(
        "guardianA", "adult1", allowed_windows=[(0, 60)]),
        "E_MG_NOT_MINOR", "guardian limits are minors-only scope")

    # -- AC-MG6: day rollover + determinism --------------------------
    f.record_spend("kid1", 500, "2026-10-03", "tx-sub-2")
    d2 = f.day_readout("kid1", "2026-10-03")
    d1 = f.day_readout("kid1", "2026-10-02")
    ok = (d2["spent_cent"] == 500 and d1["spent_cent"] == 800
          and f.check_spend("kid1", 500, "2026-10-03")["allowed"])
    record("AC-MG6", ok, "daily counter resets on date rollover")
    r1 = render_report(f, ["kid1", "adult1"], "2026-10-03")
    r2 = render_report(f, ["kid1", "adult1"], "2026-10-03")
    record("AC-MG6", r1 == r2, "same inputs -> byte-identical report")

    # -- AC-MG7: compliance header + ASCII source -------------------
    hdr = ("[needs-CEO]" in r1 and "NON-INVESTMENT-ADVISORY" in r1
           and "AI-GENERATED LABEL" in r1 and "sec.43-44" in r1
           and "sec.31" in r1 and "sec.24(3)" in r1)
    record("AC-MG7", hdr, "compliance header: 4-piece + law cites")
    for name in ("minors.py", "test_minors.py"):
        path = os.path.join(BASE, name)
        with open(path, "rb") as fh:
            raw = fh.read()
        record("AC-MG7", all(b < 128 for b in raw),
               "%s pure ASCII (0 non-ASCII bytes)" % name)

    failed = [ac for ac, ok in RESULTS if not ok]
    print("")
    print("SUITE %s - %d/%d green" % (
        "PASS" if not failed else "FAIL", len(RESULTS) - len(failed),
        len(RESULTS)))
    if failed:
        print("failed: %s" % ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
