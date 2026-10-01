"""Suite for src/sandbox/citymodel/scenario.py (AC-CCM1..CCM6).

Run: python test_scenario.py  -> SUITE PASS n/n, exit 0.
Pure stdlib; ASCII-only source (encoding law).
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as scm  # noqa: E402

BASE = {
    "track_a": {"buyout_price": 99.0, "dlc_price": 30.0, "attach_rate": 0.4,
                "units_per_month": 1000},
    "track_b": {"tier_prices": (9.9, 19.9, 29.9), "tier_mix": (0.5, 0.3, 0.2),
                "monthly_churn": 0.1, "new_subs_per_month": 500,
                "starting_subs": 1000.0},
    "funnel": {"visitors": 100000, "register_rate": 0.2, "paid_rate": 0.05},
}


def test_fail_closed_gate():
    # negative price, missing track_a price, bad mix sum, missing dict
    bad = ("neg", {"track_a": {"buyout_price": -1, "dlc_price": 1}, "track_b": {}, "funnel": {}})
    for name, p in [bad,
                    ("no_price", {"track_a": {"dlc_price": 1}, "track_b": {}, "funnel": {}}),
                    ("mix", {**BASE, "track_b": {**BASE["track_b"], "tier_mix": (0.5, 0.3, 0.5)}}),
                    ("notdict", [])]:
        try:
            scm.validate(p)
        except scm.ParamError:
            continue
        raise AssertionError("gate should fail closed: %s" % name)
    assert scm.validate(BASE) is True


def test_track_a_math():
    # hand check: gross = 1000*99 + 1000*0.4*30 = 99000 + 12000 = 111000
    out = scm.project_track_a(BASE, 3)
    assert abs(out["rows"][0]["gross"] - 111000.0) < 1e-9
    assert abs(out["rows"][2]["cumulative"] - 333000.0) < 1e-9
    assert out["gross_total"] == out["rows"][-1]["cumulative"]


def test_track_b_math():
    # month1: subs0=1000*(.5,.3,.2)=(500,300,200) decay .9 + 500*share
    # tier0: 450+250=700, tier1: 270+150=420, tier2: 180+100=280
    # mrr = 700*9.9 + 420*19.9 + 280*29.9 = 6930 + 8358 + 8372 = 23660
    out = scm.project_track_b(BASE, 2)
    assert abs(out["rows"][0]["mrr"] - 23660.0) < 1e-6
    assert abs(out["rows"][0]["subs_total"] - 1400.0) < 1e-6
    assert out["tiers"][0]["price"] == 9.9 and out["tiers"][2]["price"] == 29.9


def test_funnel_identity():
    f = scm.funnel(BASE)
    assert f["registered"] == 20000.0 and f["paid"] == 1000.0
    assert f["paid"] <= f["registered"] <= f["visitors"]


def test_breakeven():
    out = scm.project_track_a(BASE, 12)
    assert scm.breakeven_month(out, 111000.0) == 1
    assert scm.breakeven_month(out, 333000.0) == 3
    assert scm.breakeven_month(out, 10 ** 9) is None


def test_determinism_two_runs():
    a = scm.render_report(BASE, 6)
    b = scm.render_report(BASE, 6)
    assert a == b and len(a) > 0


def test_compliance_markers():
    r = scm.render_report(BASE, 3)
    for marker in ("[needs-CEO]", "NON-INVESTMENT-ADVISORY",
                   "AI-GENERATED LABEL", "9.9/19.9/29.9"):
        assert marker in r, marker


def test_sensitivity_monotonic():
    grid = scm.sensitivity_grid(BASE, 6, [50, 99, 149, 199])
    assert [g["buyout_price"] for g in grid] == [50, 99, 149, 199]
    gross = [g["gross_total"] for g in grid]
    assert gross == sorted(gross) and gross[0] < gross[-1]


def test_ascii_sources():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("scenario.py", "test_scenario.py"):
        raw = open(os.path.join(here, name), "rb").read()
        assert all(b < 128 for b in raw), "non-ASCII byte in %s" % name


def test_two_run_subprocess_identical():
    here = os.path.dirname(os.path.abspath(__file__))
    cmd = [sys.executable, "-c",
           "import sys; sys.path.insert(0, %r); import scenario as s; "
           "sys.stdout.write(s.render_report(%r, 4))" % (here, BASE)]
    r1 = subprocess.run(cmd, capture_output=True, text=True)
    r2 = subprocess.run(cmd, capture_output=True, text=True)
    assert r1.returncode == 0 and r2.returncode == 0
    assert r1.stdout == r2.stdout and len(r1.stdout) > 0
    assert "[needs-CEO]" in r1.stdout


def main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS %s" % name)
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print("FAIL %s: %r" % (name, exc))
    print("SUITE PASS %d/%d" % (passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
