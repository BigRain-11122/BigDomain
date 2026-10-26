"""Double-run identity suite (R2153; criteria AC-RID1..AC-RID8 were
pre-registered in state/queue/tech.md BEFORE this code existed -
honesty law).

What this proves: the question "did the second run agree with the
first?" now has one dialect instead of two, the dialect is verified
against the files instead of trusted, and the whole qa/ evidence
directory is audited so an unverified claim turns red at the next
battery instead of surviving as a sentence in a narrative.

Fixtures are built in temp directories; the live leg reads the real
qa/ directory and the shipped baseline only (read-only).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import run_identity as RI  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "run_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-run-identity"
BASELINE = os.path.join(REPO, "state", "run_identity_baseline.json")

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def raises(func, *args, **kwargs):
    """Return the error code a call raises, or 'NONE'."""
    try:
        func(*args, **kwargs)
    except RI.IdentityError as exc:
        return exc.code
    return "NONE"


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def run_cli(args):
    proc = subprocess.Popen([sys.executable, MODULE] + args,
                            cwd=REPO,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode,
            out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def evidence(*lines):
    """A small evidence file: criteria, then the suite verdict."""
    body = list(lines)
    body.append("SUITE PASS %d/%d criteria" % (len(lines), len(lines)))
    return "\n".join(body) + "\n"


def run():
    # AC-RID1: the three disclosed normalizations, the digest key, the
    # mode gate and the bytes-implies-conclusions implication.
    crlf = "PASS AC-X1 body\r\nSUITE PASS 1/1\r\n"
    lf = "PASS AC-X1 body\nSUITE PASS 1/1\n"
    bom = "\ufeff" + lf
    padded = lf + "\n\n"
    digests_eq = (RI.digest16(crlf) == RI.digest16(lf)
                  == RI.digest16(bom) == RI.digest16(padded))
    stable = RI.digest16(lf) == RI.digest16(lf)
    length_ok = len(RI.digest16(lf)) == 16
    stripped = RI.normalize("a\r\nb\rc")
    implication = False
    pair = RI.compare_runs(lf, lf, RI.MODE_CONCLUSIONS)
    by = RI.compare_runs(lf, lf, RI.MODE_BYTES)
    implication = (by["bytes_identical"] is True
                   and by["conclusions_identical"] is True
                   and pair["ok"] is True)
    check(digests_eq and stable and length_ok and stripped == "a\nb\nc\n"
          and raises(RI.compare_runs, lf, lf, "sha") == "E_BAD_MODE"
          and implication and RI.MODES == ("bytes", "conclusions"),
          "AC-RID1 normalize/digest16/mode gate, bytes implies conclusions")

    # AC-RID2: the criterion-line parse, the single SUITE law, the
    # multi-leg duplicate law and the ignored-line families.
    text = ("suite: demo (R2099 AC-XY1..AC-XY3)\n"
            "PASS AC-XY1 first leg payload=1\n"
            "FAIL AC-XY2 second leg\n"
            "PASS AC-TMP1 anchors leg\n"
            "PASS AC-TMP1 age leg\n"
            "| PASS table row not a criterion |\n"
            "\n"
            "SUITE FAIL 2/3 criteria\n")
    criteria, suite = RI.parse_verdicts(text)
    names = [row["id"] for row in criteria]
    two_suite = raises(RI.parse_verdicts,
                       "SUITE PASS 1/1\nSUITE PASS 1/1\n")
    conflict = raises(RI.parse_verdicts,
                      "PASS AC-XY1 a\nFAIL AC-XY1 b\nSUITE PASS 1/1\n")
    no_suite = RI.parse_verdicts("PASS AC-XY1 only\n")[1] is None
    check(names == ["AC-XY1", "AC-XY2", "AC-TMP1"]
          and [row["verdict"] for row in criteria] == ["PASS", "FAIL", "PASS"]
          and suite == {"verdict": "FAIL", "passed": 2, "total": 3}
          and two_suite == "E_MULTI_SUITE" and conflict == "E_DUP_ID"
          and no_suite,
          "AC-RID2 criterion parse, multi-leg legal, conflict and suite laws")

    # AC-RID3: conclusions identity survives payload drift and names
    # every real difference.
    left = evidence("PASS AC-AA1 at 2026-10-27T05:00:00Z path=%TMP%x",
                    "PASS AC-AA2 count=3")
    right = evidence("PASS AC-AA1 at 2026-10-27T05:07:41Z path=%TMP%y",
                     "PASS AC-AA2 count=3")
    same = RI.compare_runs(left, right, RI.MODE_CONCLUSIONS)
    flip = RI.compare_runs(left, evidence("FAIL AC-AA1 x",
                                          "PASS AC-AA2 count=3"),
                           RI.MODE_CONCLUSIONS)
    added = RI.compare_runs(left, evidence("PASS AC-AA1 x", "PASS AC-AA2 y",
                                           "PASS AC-AA3 z"),
                            RI.MODE_CONCLUSIONS)
    check(same["ok"] is True and same["differing"] == []
          and flip["ok"] is False and flip["differing"] == ["AC-AA1"]
          and added["ok"] is False and added["differing"] == ["AC-AA3"],
          "AC-RID3 payload drift tolerated, verdict/added/removed named")

    # AC-RID4: bytes identity is strict in both directions and never
    # upgraded from conclusions.
    strict = RI.compare_runs(left, right, RI.MODE_BYTES)
    equal = RI.compare_runs(left, left, RI.MODE_BYTES)
    one_char = RI.compare_runs(left, left.replace("count=3", "count=4"),
                               RI.MODE_BYTES)
    check(equal["ok"] is True and equal["bytes_identical"] is True
          and equal["digest_a"] == equal["digest_b"]
          and strict["ok"] is False and strict["bytes_identical"] is False
          and strict["conclusions_identical"] is True
          and strict["digest_a"] != strict["digest_b"]
          and one_char["ok"] is False and one_char["differing"] == []
          and len(strict["digest_a"]) == 16,
          "AC-RID4 bytes strict, conclusions-equal pair stays bytes False")

    # AC-RID5: claim detection (body only), the silence gate, and the
    # two false-claim codes verified against the files.
    claim_body = evidence("PASS AC-AA1 x") + "double-run byte-identical\n"
    claim_concl = evidence("PASS AC-AA1 x") + "criterion lines identical\n"
    product_only = evidence("PASS AC-AA1 three-instance byte-identical=True")
    block = evidence("PASS AC-AA1 x")
    declared = RI.digest16(block)
    run_line = ("%sRUN1 rc=0 sha16=%s RUN2 rc=0 sha16=%s identical=True\n"
                % (block, declared, declared))
    good = RI.verify_pair(run_line, run_line)
    false_byte = RI.verify_pair(run_line, block)
    bad_run = ("%sRUN1 rc=0 sha16=%s RUN2 rc=0 sha16=0000000000000000"
               " identical=True\n" % (block, declared))
    bad_digest = RI.verify_pair(bad_run, bad_run)
    check(RI.claim_mode(claim_body) == RI.MODE_BYTES
          and RI.claim_mode(claim_concl) == RI.MODE_CONCLUSIONS
          and RI.claim_mode(product_only) is None
          and raises(RI.verify_pair, block, block,
                     None, True) == "E_NO_CLAIM"
          and good["problems"] == []
          and good["declared"] == declared
          and RI.payload_digest(run_line) == declared
          and false_byte["problems"] == ["E_FALSE_BYTE_CLAIM"]
          and bad_digest["problems"] == ["E_FALSE_DIGEST"]
          and RI.parse_run_line(run_line)["identical"] is True,
          "AC-RID5 body-only claims, silence gate, false claim and digest")

    # AC-RID6: pairing shapes, ignored files, stable order, and the
    # ambiguous battery "-2" shape deliberately NOT paired.
    tmp = tempfile.mkdtemp(prefix="ridpair-")
    try:
        names = ["alpha-R1-a.log", "alpha-R1-b.log",
                 "beta-R2-verifya.log", "beta-R2-verifyb.log",
                 "gamma-R3.log", "gamma-R3-run2.log",
                 "delta-R4-2.log", "delta-R4.log",
                 "lonely-R5-a.log", "notes.txt"]
        for name in names:
            write(os.path.join(tmp, name), evidence("PASS AC-AA1 x"))
        pairs = RI.find_pairs(tmp)
        bases = [row["base"] for row in pairs]
        report = RI.audit_pairs(tmp, pairs)
        delta_unpaired = "delta-R4" not in bases
        check(bases == sorted(bases) and bases == ["alpha-R1", "beta-R2",
                                                   "gamma-R3"]
              and delta_unpaired
              and report["summary"]["pairs"] == 3
              and report["summary"]["conclusion_drift"] == 0,
              "AC-RID6 pairing shapes, unpaired and -2 ignored, stable order")
    finally:
        for name in os.listdir(tmp):
            os.remove(os.path.join(tmp, name))
        os.rmdir(tmp)

    # AC-RID7: the CLI contract, and proof that it writes nothing.
    tmp = tempfile.mkdtemp(prefix="ridcli-")
    try:
        first = os.path.join(tmp, "one.log")
        second = os.path.join(tmp, "two.log")
        write(first, evidence("PASS AC-AA1 x"))
        write(second, evidence("PASS AC-AA1 y"))
        before = sorted((name, os.path.getmtime(os.path.join(tmp, name)))
                        for name in os.listdir(tmp))
        code_digest, out_digest, _ = run_cli(["--digest", first])
        code_pair, out_pair, _ = run_cli(["--pair", first, second, "--json"])
        code_audit, _, _ = run_cli(["--audit", tmp])
        code_missing, _, _ = run_cli(["--digest", os.path.join(tmp, "no.log")])
        code_bad, _, _ = run_cli(["--pair", first, second, "--mode", "sha"])
        code_args, _, _ = run_cli([])
        after = sorted((name, os.path.getmtime(os.path.join(tmp, name)))
                       for name in os.listdir(tmp))
        payload = json.loads(out_pair) if out_pair.strip() else {}
        check(code_digest == 0 and out_digest.strip() == RI.digest16(
                  evidence("PASS AC-AA1 x"))
              and code_pair == 0
              and set(payload) == {"mode", "ok", "criteria_a", "criteria_b",
                                   "suite_a", "suite_b", "differing",
                                   "digest_a", "digest_b", "bytes_identical",
                                   "conclusions_identical", "claimed",
                                   "implicit", "declared", "problems"}
              and code_audit == 0 and code_missing == 3
              and code_bad == 2 and code_args == 2
              and before == after,
              "AC-RID7 CLI 0/2/3, stable JSON keys, zero writes")
    finally:
        for name in os.listdir(tmp):
            os.remove(os.path.join(tmp, name))
        os.rmdir(tmp)

    # AC-RID8: the live leg over the real evidence directory plus the
    # hygiene and wiring laws.
    qa_dir = os.path.join(REPO, "qa")
    live = RI.audit_pairs(qa_dir)
    known = RI.load_baseline(BASELINE)
    gated = RI.apply_baseline(live, known)
    with io.open(BASELINE, "r", encoding="utf-8") as handle:
        shipped = json.load(handle)
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner_src = handle.read()
    net = RI.network_imports(source)
    ascii_only = all(ord(char) < 128 for char in source)
    known_ok = ((("apimarket-buyermonths-R2100", "E_FALSE_BYTE_CLAIM")
                 in known)
                and shipped["known"][0]["classes"] == ["E_FALSE_BYTE_CLAIM"])
    check(live["summary"]["pairs"] >= 50
          and live["summary"]["conclusion_drift"] == 0
          and live["summary"]["false_digests"] == 0
          and gated["new"] == [] and gated["gated_clean"] is True
          and known_ok and not net and ascii_only
          and "\r" not in source
          and LABEL in runner_src
          and EXPECTED_CRITERIA == 8,
          "AC-RID8 live audit gated clean, baseline parse, hygiene, wiring")


def main():
    print("suite: double-run identity dialect (R2153 AC-RID1..AC-RID8)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())