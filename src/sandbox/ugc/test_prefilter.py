"""Acceptance suite for the local L1 pre-filter wiring (BigDomain R838).

Asserts AC-SW1..AC-SW6 pre-registered in src/os/backlog.md (R838 row,
registered before any external request; honesty law). The wiring
adopts the pooled OSS candidate houbb/sensitive-word data face
(OH-20261002 window 3 slice, R837): wordlist file verbatim +
NOTICE + LICENSE carried in wordlist_data/, self-written trie matcher
in wordlist.py, config-driven via gate.pre_filter, pipeline order =
L1 local trie -> L2 mock gate (msgSecCheck stand-in) -> gray review.

Chinese probes are sourced from config.json and the wordlist data
file (data files per the encoding discipline; this suite stays ASCII).

Usage: python test_prefilter.py
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.normpath(os.path.join(BASE, "..", "lobby")))

import pipeline as P  # noqa: E402
import store as UGC  # noqa: E402
import wordlist as WL  # noqa: E402
from sec_gate import GateOfflineError  # noqa: E402 (lobby gate product)

RESULTS = []
DATA_DIR = os.path.join(BASE, "wordlist_data")
DICT_PATH = os.path.join(DATA_DIR, "sensitive_words_dict.txt")
DICT_BYTES = 1180575  # source git-trees API reported size (integrity)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_gate_offline(fn):
    try:
        fn()
    except GateOfflineError:
        return True
    return False


def main():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    gate = cfg["gate"]
    with open(DICT_PATH, encoding="utf-8") as fh:
        dict_words = list(dict.fromkeys(
            w.strip() for w in fh.read().splitlines() if w.strip()))

    # AC-SW1: wordlist data face landed verbatim + provenance carried
    record("SW1a-dict-verbatim", os.path.getsize(DICT_PATH) == DICT_BYTES,
           "dict file %d bytes == source trees API size" % os.path.getsize(DICT_PATH))
    record("SW1b-notice", os.path.isfile(
        os.path.join(DATA_DIR, "NOTICE-houbb-sensitive-word.md")),
        "NOTICE (Apache-2.0 s4 attribution) in wordlist_data/")
    record("SW1c-license", os.path.isfile(
        os.path.join(DATA_DIR, "LICENSE-Apache-2.0.txt")),
        "source LICENSE.txt verbatim (20966 B) in wordlist_data/")
    record("SW1d-format", len(dict_words) == 65143 - 2,
           "65143 non-blank lines, 2 exact dups -> %d unique words "
           "(plain one-per-line format, 0 blanks)" % len(dict_words))

    # AC-SW4a: absent pre_filter -> None (legacy configs keep working)
    legacy = json.loads(json.dumps(cfg))
    legacy["gate"].pop("pre_filter")
    record("SW4a-legacy-none", WL.PreFilter.from_config(legacy) is None,
           "gate.pre_filter absent -> None (backward compatible)")

    # AC-SW4b/4c: configured but unwired -> GateOfflineError (no door)
    broken = json.loads(json.dumps(cfg))
    broken["gate"]["pre_filter"]["file"] = "wordlist_data/missing.txt"
    record("SW4b-missing-refuse", expect_gate_offline(
        lambda: WL.PreFilter.from_config(broken)),
        "missing wordlist -> GateOfflineError (no gate, no door)")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
        empty_path = tmp.name
    empty = json.loads(json.dumps(cfg))
    empty["gate"]["pre_filter"]["file"] = empty_path
    record("SW4c-empty-refuse", expect_gate_offline(
        lambda: WL.PreFilter.from_config(empty)),
        "empty wordlist -> GateOfflineError")
    os.unlink(empty_path)

    # AC-SW4: real config loads the real dict into the trie
    pf = WL.PreFilter.from_config(cfg)
    record("SW4d-load", pf is not None and pf.word_count == len(dict_words),
           "pre-filter loaded: %d words, source=%s" % (pf.word_count, pf.source))

    # probe = first dict word outside every config word list + allow set
    config_words = set(gate["forbidden_words"]) | set(gate["advisory_ban_words"]) \
        | set(gate["gray_words"]) | set(gate["pre_filter"]["allow_words"])
    probe = next(w for w in dict_words if w not in config_words)
    record("SW4e-trie-hit", pf.check("clean intro about " + probe + " here") == probe,
           "trie catches dict word at inner position (probe len=%d)" % len(probe))
    record("SW4f-clean-pass", pf.check("clean idea about plaza design") is None,
           "clean text -> no hit")
    gray0 = gate["gray_words"][0]
    record("SW4g-allow-gray", pf.check("user discussion on " + gray0) is None,
           "gray word #0 (len=%d) -> allow fall-through (review, not reject)"
           % len(gray0))
    record("SW4h-allow-mask", pf.check(gray0 + " and " + probe) == probe,
           "allowed word never masks a later real hit")

    # AC-SW5: pipeline integration + counter accounting
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "ugc.db")
        pipe = P.UGCPipeline(cfg, db)
        pipe.grant_entrance_sandbox("A-pf")

        def submit(src, actor, text):
            return pipe.submit(src, actor, text)

        r_ok = submit("direct", "A-pf", "plaza idea about gameplay design")
        record("SW5a-clean-flow", r_ok.get("gate") == "pass"
              and pipe.local_hit_count == 0,
              "clean content passes L1+L2, local_hit_count=0")

        try:
            submit("direct", "A-pf", "spam probe " + probe)
            got = "no-error"
        except UGC.PipelineError as exc:
            got = exc.code
        record("SW5b-dict-hit-reject", got == UGC.E_CONTENT_REJECTED
              and pipe.local_hit_count == 1,
              "dict-only word -> E_CONTENT_REJECTED via L1, counter=1 "
              "(one platform call saved)")

        try:
            submit("direct", "A-pf", "promise " + gate["advisory_ban_words"][0])
            got2 = "no-error"
        except UGC.PipelineError as exc:
            got2 = exc.code
        record("SW5c-l2-still-catches", got2 == UGC.E_CONTENT_REJECTED
              and pipe.local_hit_count == 1,
              "advisory word (not in dict) -> L2 mock gate catches, "
              "counter unchanged (layered defense)")

        r_gray = submit("direct", "A-pf", "policy chat on " + gray0)
        record("SW5d-gray-review-intact", r_gray.get("suspended") is True
              and pipe.local_hit_count == 1,
              "gray word falls through L1 -> review suspension, not reject")

        try:
            submit("direct", "A-pf", "forbidden probe " + gate["forbidden_words"][0])
            got3 = "no-error"
        except UGC.PipelineError as exc:
            got3 = exc.code
        record("SW5e-forbidden-local-first", got3 == UGC.E_CONTENT_REJECTED
              and pipe.local_hit_count == 2,
              "mock forbidden word also in dict -> caught at L1 locally "
              "(counter=2), same rejection family")
        pipe.close()

    # AC-SW6: zero regression - the original suite, file untouched
    run = subprocess.run(
        [sys.executable, os.path.join(BASE, "test_ugc.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (run.stdout or "") + (run.stderr or "")
    passed = run.returncode == 0 and "FAIL" not in out
    record("SW6-zero-regression", passed,
           "test_ugc.py exit=%d, 12/12 unchanged file" % run.returncode)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("prefilter suite: %d/%d PASS%s"
          % (len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " FAILED: " + ",".join(fails)), flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
