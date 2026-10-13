"""R1934 tourstate cross-process re-derivation window (persist-
family seat, R1886 lineage; suite-only round - zero product
change). Pre-registered criteria AC-TSP1..TSP7 live in the
state/queue/tech.md claim line and were written before this code
existed (honesty law).

Substrate ruling (claim line): tourstate is a pure stateless prep
face (zero sqlite, zero file substrate), so the restart carrier is
a fresh interpreter subprocess - the honest form of "read faces
replay byte-identical across restart" for a pure module is
cross-process cold re-derivation byte equality (zero hidden
process state).

Worker protocol: self re-entry via the explicit --worker flag;
one JSON job line in on stdin, one JSON result line out on stdout;
zero temp files, zero disk writes. Evidence lines are deterministic
(no ts, no pid, no paths).

Usage: python test_tourstate_persist.py [--worker]
"""

import copy
import hashlib
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import tourstate as TS  # noqa: E402  (product module under test)

SRC = os.path.join(BASE, "tourstate.py")
SELF = os.path.abspath(__file__)
RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run_worker(job):
    """Spawn a fresh interpreter running this suite in worker mode;
    job in on stdin, one JSON result line back on stdout."""
    proc = subprocess.run(
        [sys.executable, SELF, "--worker"],
        input=json.dumps(job), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("worker exit=%d stderr=%s"
                           % (proc.returncode, proc.stderr.strip()))
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise RuntimeError("worker stdout not one line: %r" % lines)
    return json.loads(lines[0])


def derive_job():
    return {"op": "derive"}


def verify_job(packet):
    return {"op": "verify", "packet": packet}


BADINPUT_JOB = {"op": "badinput"}


def worker_main():
    """Fresh-process entry: one JSON job line in, one JSON out."""
    job = json.loads(sys.stdin.read())
    if job["op"] == "derive":
        p_false = TS.build_packet(False)
        p_true = TS.build_packet(True)
        print(json.dumps({
            "false_canon": TS.canonical(p_false),
            "false_id": p_false["packet_id"],
            "true_canon": TS.canonical(p_true),
            "true_id": p_true["packet_id"],
        }), flush=True)
        return 0
    if job["op"] == "verify":
        try:
            TS.verify_packet(job["packet"])
            print(json.dumps({"ok": True}), flush=True)
        except TS.TourStateError as exc:
            print(json.dumps({"ok": False, "code": exc.code}),
                  flush=True)
        return 0
    if job["op"] == "badinput":
        codes = []
        for probe in (
                lambda: TS.build_packet("yes"),
                lambda: TS.evaluate_gate("ghost_state", "license_l1",
                                         False),
                lambda: TS.evaluate_gate("dataface", "ghost_gate",
                                         False)):
            try:
                probe()
                codes.append("no-error-raised")
            except TS.TourStateError as exc:
                codes.append(exc.code)
        print(json.dumps({"codes": codes}), flush=True)
        return 0
    print(json.dumps({"ok": False, "code": "E_TS_BAD_OP"}), flush=True)
    return 2


def ac1_control_anchor(baseline):
    w1 = run_worker(derive_job())
    ok = (w1["false_canon"] == baseline["false_canon"]
          and w1["false_id"] == baseline["false_id"]
          and w1["true_canon"] == baseline["true_canon"]
          and w1["true_id"] == baseline["true_id"])
    record("AC-TSP1", ok, "fresh subprocess #1 cold re-derivation "
          "byte-identical both legs (ids equal)")


def ac2_three_instance_chain(baseline):
    outs = [run_worker(derive_job()) for _ in range(3)]
    ok = all(w == outs[0] for w in outs) and (
        outs[0]["false_canon"] == baseline["false_canon"]
        and outs[0]["true_canon"] == baseline["true_canon"]
        and outs[0]["false_id"] == baseline["false_id"]
        and outs[0]["true_id"] == baseline["true_id"])
    record("AC-TSP2", ok, "three sequential fresh subprocesses "
          "mutually byte-identical == parent baseline "
          "(double-restart stability)")


def ac3_verify_across_boundary(p_false, p_true):
    r_false = run_worker(verify_job(p_false))
    r_true = run_worker(verify_job(p_true))
    ok = r_false.get("ok") is True and r_true.get("ok") is True
    record("AC-TSP3", ok, "verify True x2 across the process "
          "boundary (stdin JSON roundtrip zero semantic loss)")


def ac4_tamper_across_boundary(p_false):
    gate_flip = copy.deepcopy(p_false)
    gate_flip["states"][2]["gates"]["license_l1"]["status"] = "PASS"
    flag_flip = copy.deepcopy(p_false)
    flag_flip["purchase_approved"] = True
    id_flip = copy.deepcopy(p_false)
    id_flip["packet_id"] = "0" * 64
    results = [run_worker(verify_job(v)) for v in
               (gate_flip, flag_flip, id_flip)]
    ok = all(r.get("ok") is False
             and r.get("code") == TS.E_TS_TAMPER for r in results)
    record("AC-TSP4", ok, "three tampered variants all rejected "
          "E_TS_TAMPER by fresh subprocesses (tamper law survives "
          "the process boundary)")


def ac5_badinput_across_boundary():
    out = run_worker(BADINPUT_JOB)
    codes = out.get("codes", [])
    ok = (len(codes) == 3
          and all(code == TS.E_TS_BAD_INPUT for code in codes))
    record("AC-TSP5", ok, "bad-input probes in a fresh subprocess "
          "raise E_TS_BAD_INPUT x3 (codes=%s)" % ",".join(codes))


def ac6_pure_read_zero_module_drift(baseline, p_false, p_true):
    post_false = TS.canonical(TS.build_packet(False))
    post_true = TS.canonical(TS.build_packet(True))
    stable = (post_false == baseline["false_canon"]
              and post_true == baseline["true_canon"])
    intact = (TS.verify_packet(p_false) is True
              and TS.verify_packet(p_true) is True)
    idem = all(TS.verify_packet(TS.build_packet(False)) is True
               for _ in range(3))
    record("AC-TSP6", stable and intact and idem, "post-activity "
          "re-derivation == pre-window capture (zero module-state "
          "drift) + original packets verify True + idempotent "
          "build->verify cycles")


def ac7_hygiene(sha_before):
    with open(SELF, "rb") as handle:
        raw = handle.read()
    ascii_ok = all(b < 128 for b in raw)
    text = raw.decode("ascii")
    import_lines = [ln.strip() for ln in text.splitlines()
                    if ln.strip().startswith("import ")
                    or ln.strip().startswith("from ")]
    net_hits = [ln for ln in import_lines
                if re.search(r"\b(urllib|requests|socket|http)\b",
                             ln)]
    sha_after = sha256_file(SRC)
    product_unchanged = sha_after == sha_before
    zero_diskwrite = not any("tempfile" in ln for ln in import_lines)
    record("AC-TSP7", ascii_ok and not net_hits
          and product_unchanged and zero_diskwrite,
          "suite source pure ASCII + zero network imports "
          "(net=%d) + tourstate.py sha unchanged across the window "
          "+ zero temp-file imports (pipe-only worker protocol)"
          % len(net_hits))


def main():
    sha_before = sha256_file(SRC)
    p_false = TS.build_packet(False)
    p_true = TS.build_packet(True)
    baseline = {
        "false_canon": TS.canonical(p_false),
        "false_id": p_false["packet_id"],
        "true_canon": TS.canonical(p_true),
        "true_id": p_true["packet_id"],
    }
    ac1_control_anchor(baseline)
    ac2_three_instance_chain(baseline)
    ac3_verify_across_boundary(p_false, p_true)
    ac4_tamper_across_boundary(p_false)
    ac5_badinput_across_boundary()
    ac6_pure_read_zero_module_drift(baseline, p_false, p_true)
    ac7_hygiene(sha_before)
    failed = [ac for ac, ok in RESULTS if not ok]
    if not failed:
        print("SUITE PASS 7/7 (AC-TSP1..AC-TSP7) exit=0", flush=True)
        return 0
    print("SUITE FAIL (%s)" % ",".join(failed), flush=True)
    return 1


if __name__ == "__main__":
    if "--worker" in sys.argv[1:]:
        sys.exit(worker_main())
    sys.exit(main())
