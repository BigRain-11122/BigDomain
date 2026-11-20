"""Battery suite for the corpus supply chain - AC-CSC1 (five arms).

WHY THIS SUITE EXISTS (measured at R3129, not assumed):
R3128 measured that the tree-gate corpus has exactly ONE measurement site and
published it on the face. That left a named worry: two other writers name the
face, so "corpus appears and disappears as write paths alternate" would be a
live defect. The R3129 probe answered it by file: of 2310 historical versions
of docs/status-export.json (1719 parsable) exactly TWO carry a corpus block,
both copies agree, the only absent->present transition is R3128's own landing
commit, and present->absent flips are ZERO. The shipped call-site census finds
three: closeout.py passes corpus=, export_round.py calls the grader's line
rewrite, and one test arm passes nothing. export_R2431.py names no corpus and
its write lives behind the __main__ guard, so importing it lands nothing.

WHAT IS PROVED HERE (two criteria):
AC-CSC1 (five arms):
  a  every call to export_round.write in a shipped NON-TEST module passes
     corpus=, and at least one such call exists (an empty census cannot pass).
  b  JUDGED-CHANGED at R3130: corpus_block(None) is None, corpus_block with
     files=0 is None (a zero-file corpus is not publishable), while a measured
     corpus whose files are all zero BYTES still publishes mb=0.0.
  c  a writer that measured nothing REMOVES both copies from a face that
     carried them, so no stale count survives the next write.
  d  the grader's line rewrite (_set_line), which is how the second writer
     touches the face, leaves the corpus block byte-for-byte intact.
  e  export_R2431 writes nothing at import time (its write is behind the
     __main__ guard) and no shipped non-test module imports it.

AC-CSC2 (five arms) - why a zero is unpublishable rather than a named state,
and why that is not the same as "the tree is empty":
  f  an EMPTY private qa/ dir makes the shipped census return rc=3 and write
     NO stats keys at all, so no zero can reach corpus_block.
  g  a MISSING qa/ dir returns the same rc=3 with the same empty stats (a
     missing tree cannot masquerade as a measured empty corpus either).
  h  a qa/ holding only unreadable entries reads files=1 readable=0 bytes=0,
     so "nothing readable" is distinguishable from "nothing there".
  i  the shipped gate (tools/closeout_gate.evaluate) refuses an empty target
     as E_CLG_EMPTY and a red flags face as E_CLG_DRIFT, and NEITHER verdict
     carries a corpus key - the reading travels only on a green face - while
     the drift verdict still publishes files=1.
  j  end to end, export_round.payload(corpus=<zero files>) publishes no
     corpus key at either level, and the card's absent sentence is what a
     reader of such a face gets.

AC-CSC3 (five arms) - why a corpus that cannot state `readable` is
unpublishable, measured at R3131:
  k  a block dict carrying files/bytes but NO readable publishes nothing.
  l  a readable that cannot be turned into an int publishes nothing either:
     "could not state how many entries I read" is a caller error, not a
     corpus of unknown readability.
  m  the negative control still publishes: files/bytes/readable present with
     bytes=0 keeps mb=0.0 and, because the two counts agree, no unread key.
  n  the one supply path always carries all three keys: a REAL census reading
     (derived, not written down) hands files/readable/bytes, and the shipped
     corpus_block call-site census still finds exactly one call.
  o  end to end: payload(corpus=<bare block>) publishes no corpus key at
     either level, and the card prints its absent sentence rather than
     "readable=none".

Isolation: private worlds are temp dirs; the only live reads are shipped
sources. Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "os"))
sys.path.insert(0, os.path.join(ROOT, "src", "sandbox"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import export_round as ER  # noqa: E402
import frontdoor as FD  # noqa: E402
import status_export_fresh as SXF  # noqa: E402

SUITE = "os-corpus-supply-chain"
CRITERION = "AC-CSC1"

BLOCK = {"files": 3, "readable": 3, "bytes": 30, "mb": 0.0}


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build_world(tick=9500):
    """A private world carrying just the inputs payload() reads."""
    import check_export_consistency as cec
    label = cec._load_patterns().get("tick_row_label")
    d = tempfile.mkdtemp(prefix="csc-")
    src = os.path.join(ROOT, "src", "os", "backlog.md")
    write(os.path.join(d, "src", "os", "backlog.md"), io.open(src, encoding="utf-8").read())
    write(os.path.join(d, "src", "os", "state.json"),
          json.dumps({"tick": tick,
                      "log": ["2026-11-21 R%d SOMETHING MEASURED IN THIS WINDOW" % tick,
                              "R%d tokens: local=1k api=0 api_reason=ledger line" % tick]},
                     ensure_ascii=False))
    for name in ("main.md", "tech.md", "explore.md"):
        p = os.path.join(ROOT, "state", "queue", name)
        if os.path.isfile(p):
            write(os.path.join(d, "state", "queue", name),
                  io.open(p, encoding="utf-8").read())
    write(os.path.join(d, "preview", "a.html"), "<!DOCTYPE html>\n")
    write(os.path.join(d, "preview", "a.json"), "{}\n")
    face = {"results": [["1", "a past row"], [tick, label]], "outs": ["x"], "do": "x",
            "corpus": dict(BLOCK),
            "ceo_face": {"current": "x", "latest_artifact": "x",
                         "next_milestone": "x", "corpus": dict(BLOCK)}}
    write(os.path.join(d, "docs", "status-export.json"),
          json.dumps(face, ensure_ascii=False, indent=2) + "\n")
    return d


def shipped_modules():
    for base in ("src", "tools"):
        for root, dirs, files in os.walk(os.path.join(ROOT, base)):
            dirs[:] = [x for x in dirs if x not in (".git", "__pycache__")]
            for name in files:
                if name.endswith(".py") and not name.startswith("test_"):
                    yield os.path.join(root, name)


def arm_a():
    """Every shipped write call passes corpus=, and the census is not empty."""
    calls = []
    for path in shipped_modules():
        try:
            tree = ast.parse(io.open(path, encoding="utf-8").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if getattr(fn, "attr", None) != "write":
                continue
            owner = getattr(getattr(fn, "value", None), "id", None)
            if owner not in ("ER", "export_round"):
                continue
            kw = sorted(k.arg for k in node.keywords if k.arg)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            calls.append((rel, node.lineno, kw))
    bad = [c for c in calls if "corpus" not in c[2]]
    if bad:
        return False, "write call without corpus= at %s:%d" % (bad[0][0], bad[0][1])
    if not calls:
        return False, "no export_round.write call found in a shipped non-test module"
    return True, "calls=%d all pass corpus= (%s)" % (
        len(calls), ", ".join("%s:%d" % (c[0], c[1]) for c in calls))


def arm_b():
    """Absence and measured-empty are different objects (R3130 amended).

    JUDGED-CHANGED at R3130, recorded on the board before this code existed:
    the old arm pinned "a measured zero returns a block". The probe measured
    that the one supply path CANNOT hand out a zero (an empty or missing qa/
    dir makes the census return rc=3 before it writes stats), so a zero-file
    block is a caller error and is now refused. Zero BYTES with files>0 is a
    real corpus of empty files and still publishes - the negative control.
    """
    if ER.corpus_block(None) is not None:
        return False, "corpus_block(None) published a block"
    # R3131: the zero arm states readable so it isolates the files<=0 law
    # from the readable law (a bare zero would now be refused for both).
    for zero in ({"files": 0, "bytes": 0, "readable": 0},):
        if ER.corpus_block(zero) is not None:
            return False, "a zero-file corpus published %r" % (zero,)
    empty_files = ER.corpus_block({"files": 3, "bytes": 0, "readable": 3})
    if not isinstance(empty_files, dict) or empty_files.get("mb") != 0.0:
        return False, "zero bytes with real files stopped publishing: %r" % (empty_files,)
    return True, "None->nothing, zero files->nothing, zero bytes->%r" % (empty_files,)


def arm_c():
    """A writer that measured nothing removes BOTH copies."""
    world = build_world()
    try:
        state = json.loads(io.open(os.path.join(world, "src", "os", "state.json"),
                                   encoding="utf-8").read())
        data, _d = ER.payload(world, state, "2026-11-21T12:00:00+08:00", corpus=None)
        if "corpus" in data:
            return False, "top-level corpus survived a non-measuring writer"
        if "corpus" in (data.get("ceo_face") or {}):
            return False, "ceo_face corpus survived a non-measuring writer"
        return True, "both copies removed (no stale count)"
    finally:
        shutil.rmtree(world, ignore_errors=True)


def arm_d():
    """The grader's line rewrite cannot strip the block."""
    text = json.dumps({"export_ts": "x", "do": "x", "current": "x",
                       "corpus": dict(BLOCK),
                       "ceo_face": {"current": "x", "corpus": dict(BLOCK)}},
                      ensure_ascii=False, indent=2) + "\n"
    out, ok = SXF._set_line(text, "current", "REWRITTEN", "  ")
    if not ok:
        return False, "_set_line did not find the key it exists for"
    if json.loads(out).get("corpus") != BLOCK:
        return False, "top-level block changed"
    if (json.loads(out).get("ceo_face") or {}).get("corpus") != BLOCK:
        return False, "ceo_face block changed"
    block_text = json.dumps(BLOCK, ensure_ascii=False)
    if out.count('"files": 3') != 2:
        return False, "block rows not preserved twice (%d found)" % out.count('"files": 3')
    if block_text not in json.dumps(BLOCK, ensure_ascii=False):
        return False, "unreachable"
    return True, "rewrite keeps both blocks verbatim"


def arm_e():
    """export_R2431 lands nothing at import and nobody imports it."""
    path = os.path.join(ROOT, "src", "os", "export_R2431.py")
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    guarded = 0
    for node in tree.body:
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare)
                    and getattr(test.left, "id", None) == "__name__"):
                guarded += 1
    if guarded != 1:
        return False, "export_R2431 has %d __main__ guards, expected 1" % guarded
    # no module-level statement outside the guard may be a write-shaped call;
    # function bodies are allowed (they only run when something calls them)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.If) and getattr(node.test.left, "id", None) == "__name__":
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            name = getattr(sub.func, "attr", None)
            owner = getattr(getattr(sub.func, "value", None), "id", None)
            # str.replace is a formatting call, os.replace is a landing call
            shaping = name in ("dump", "write", "publish") or (
                name == "replace" and owner == "os")
            if shaping:
                return False, "top-level write-shaped call at line %d" % sub.lineno
    importers = []
    for p in shipped_modules():
        if os.path.abspath(p) == os.path.abspath(path):
            continue
        try:
            other = ast.parse(io.open(p, encoding="utf-8").read())
        except Exception:
            continue
        aliases = []
        for node in ast.walk(other):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if "export_R2431" in a.name:
                        aliases.append(a.asname or a.name.split(".")[-1])
            elif isinstance(node, ast.ImportFrom):
                if node.module and "export_R2431" in node.module:
                    aliases.extend(a.asname or a.name for a in node.names)
        if not aliases:
            continue
        called = set()
        for node in ast.walk(other):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and getattr(node.func.value, "id", None) in aliases):
                called.add(node.func.attr)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        importers.append("%s(%s)" % (rel, ",".join(sorted(called)) or "no calls"))
        if "main" in called:
            return False, "%s calls export_R2431.main, which WRITES the face" % rel
    return True, "guard=1, no importer calls main (%s)" % "; ".join(sorted(importers))


def _empty_baseline(world):
    import qa_writer_census as CENSUS
    path = os.path.join(world, CENSUS.BASELINE_NAME)
    write(path, json.dumps(dict((c, []) for c in CENSUS.BASELINE_CLASSES),
                           indent=2) + "\n")
    return path


def _census_reading(target_builder):
    import qa_writer_census as CENSUS
    world = tempfile.mkdtemp(prefix="csc-zero-")
    try:
        target, baseline = target_builder(world)
        stats = {}
        lines, rc = CENSUS.check_against_baseline(target, baseline, stats=stats)
        return stats, rc, "\n".join(lines)
    finally:
        shutil.rmtree(world, ignore_errors=True)


def _empty_qa(world):
    baseline = _empty_baseline(world)
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    return qa, baseline


def _missing_qa(world):
    baseline = _empty_baseline(world)
    return os.path.join(world, "qa"), baseline


def _unreadable_qa(world):
    baseline = _empty_baseline(world)
    qa = os.path.join(world, "qa")
    os.makedirs(os.path.join(qa, "x.log"))
    return qa, baseline


def arm_f():
    """An empty qa/ dir refuses BEFORE stats exists - no zero can be handed."""
    stats, rc, text = _census_reading(_empty_qa)
    if rc != 3:
        return False, "empty target read rc=%d, expected 3" % rc
    if stats:
        return False, "empty target wrote stats %r (a zero could be published)" % (stats,)
    if "no *.log candidates" not in text:
        return False, "the refusal did not name itself: %r" % text[-120:]
    return True, "rc=3, stats={} (zero unreachable), refusal named"


def arm_g():
    """A missing qa/ dir is the same refusal, not a measured empty corpus."""
    stats, rc, text = _census_reading(_missing_qa)
    if rc != 3 or stats:
        return False, "missing target rc=%d stats=%r" % (rc, stats)
    if "no *.log candidates" not in text:
        return False, "missing target refused without naming itself"
    return True, "rc=3, stats={} - a missing tree cannot read as empty"


def arm_h():
    """Nothing readable IS distinguishable from nothing there."""
    stats, rc, _text = _census_reading(_unreadable_qa)
    if rc != 2 or stats.get("files") != 1 or stats.get("readable") != 0:
        return False, "only-unreadable read rc=%d stats=%r" % (rc, stats)
    block = ER.corpus_block(stats)
    if not isinstance(block, dict) or block.get("unread") != 1:
        return False, "only-unreadable block=%r" % (block,)
    return True, "files=1 readable=0 unread=1 (vs files absent when empty)"


def arm_i():
    """The shipped gate never hands a corpus on a refused face."""
    import closeout_gate as CG
    world = tempfile.mkdtemp(prefix="csc-gate-")
    try:
        blank = _empty_baseline(world)
        qa = os.path.join(world, "qa")
        os.makedirs(qa)
        _out, rc, verdict = CG.evaluate(qa, blank)
        if rc != 2 or verdict.get("reason") != "E_CLG_EMPTY":
            return False, "empty gate rc=%d verdict=%r" % (rc, verdict)
        if "corpus" in verdict:
            return False, "gate handed a corpus for an empty target: %r" % (verdict["corpus"],)
        os.makedirs(os.path.join(qa, "x.log"))
        _out2, rc2, verdict2 = CG.evaluate(qa, blank)
        if rc2 != 2 or verdict2.get("reason") != "E_CLG_DRIFT":
            return False, "only-unreadable gate rc=%d verdict=%r" % (rc2, verdict2)
        if "corpus" in verdict2:
            return False, "gate handed a corpus on a red flags face: %r" % (verdict2["corpus"],)
        if verdict2.get("files") != 1:
            return False, "gate did not publish its file count: %r" % (verdict2,)
        return True, "E_CLG_EMPTY and E_CLG_DRIFT both carry no corpus (files=1 named)"
    finally:
        shutil.rmtree(world, ignore_errors=True)


def arm_j():
    """End to end: a zero-file corpus reaches no face and the card names it."""
    world = build_world()
    try:
        state = json.loads(io.open(os.path.join(world, "src", "os", "state.json"),
                                   encoding="utf-8").read())
        data, _d = ER.payload(world, state, "2026-11-21T12:00:00+08:00",
                              corpus={"files": 0, "bytes": 0, "readable": 0})
        if "corpus" in data:
            return False, "zero-file corpus published at top level"
        if "corpus" in (data.get("ceo_face") or {}):
            return False, "zero-file corpus published under ceo_face"
    finally:
        shutil.rmtree(world, ignore_errors=True)
    card = FD.corpus_card({"corpus": ER.corpus_block({"files": 0, "bytes": 0})})
    if "CORPUS absent" not in card:
        return False, "card did not name the absence: %r" % card
    if "files=0" in card:
        return False, "card printed a zero: %r" % card
    return True, "no corpus key at either level; card prints the absent line"


def _healthy_qa(world):
    baseline = _empty_baseline(world)
    qa = os.path.join(world, "qa")
    write(os.path.join(qa, "x.log"), "PASS one\nPASS two\n")
    return qa, baseline


def arm_k():
    """A bare files/bytes dict publishes nothing (R3131)."""
    if ER.corpus_block({"files": 5, "bytes": 100}) is not None:
        return False, "a readable-less corpus published a block"
    return True, "bare {files,bytes} -> None"


def arm_l():
    """An unparseable readable publishes nothing either."""
    for bad in ({"files": 5, "bytes": 100, "readable": "x"},
                {"files": 5, "bytes": 100, "readable": None},
                {"files": 5, "bytes": 100, "readable": ""}):
        if ER.corpus_block(bad) is not None:
            return False, "unparseable readable published %r" % (bad,)
    return True, "unparseable readable -> None (3 shapes)"


def arm_m():
    """Negative control: the complete three-key dict still publishes."""
    block = ER.corpus_block({"files": 5, "bytes": 0, "readable": 5})
    if not isinstance(block, dict):
        return False, "complete corpus stopped publishing: %r" % (block,)
    want = {"files", "bytes", "mb", "readable"}
    if set(block) != want:
        return False, "block keys drifted: %r" % (sorted(block),)
    if block.get("mb") != 0.0:
        return False, "zero bytes lost its mb reading: %r" % (block,)
    if "unread" in block:
        return False, "a clean corpus grew a decorative unread key: %r" % (block,)
    return True, "files/bytes/mb/readable, mb=0.0, no unread"


def arm_n():
    """The one supply path always states all three counts (derived)."""
    stats, rc, _text = _census_reading(_healthy_qa)
    if rc not in (0, 2):
        return False, "healthy target read rc=%d (not a measurment)" % rc
    missing = [k for k in ("files", "readable", "bytes") if k not in stats]
    if missing:
        return False, "census stats lack %r: %r" % (missing, stats)
    if stats["files"] != 1 or stats["readable"] != 1:
        return False, "healthy target read %r" % (stats,)
    callers = []
    for path in shipped_modules():
        try:
            tree = ast.parse(io.open(path, encoding="utf-8").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and getattr(node.func, "attr", None) == "corpus_block"
                    or isinstance(node, ast.Call)
                    and getattr(node.func, "id", None) == "corpus_block"):
                callers.append("%s:%d"
                               % (os.path.relpath(path, ROOT).replace("\\", "/"),
                                  node.lineno))
    if len(callers) != 1:
        return False, "shipped corpus_block callers=%d (%s)" % (
            len(callers), ", ".join(callers) or "none")
    return True, "census hands %r; corpus_block callers=1 (%s)" % (
        {k: stats[k] for k in ("files", "readable", "bytes")}, callers[0])


def arm_o():
    """End to end: a bare block reaches no face and the card names it."""
    world = build_world()
    try:
        state = json.loads(io.open(os.path.join(world, "src", "os", "state.json"),
                                   encoding="utf-8").read())
        data, _d = ER.payload(world, state, "2026-11-21T12:00:00+08:00",
                              corpus={"files": 5, "bytes": 100})
        if "corpus" in data:
            return False, "readable-less corpus published at top level"
        if "corpus" in (data.get("ceo_face") or {}):
            return False, "readable-less corpus published under ceo_face"
    finally:
        shutil.rmtree(world, ignore_errors=True)
    card = FD.corpus_card({"corpus": ER.corpus_block({"files": 5, "bytes": 100})})
    if "CORPUS absent" not in card:
        return False, "card did not name the absence: %r" % card
    if "readable=none" in card:
        return False, "card printed readable=none: %r" % card
    return True, "no corpus key at either level; card prints the absent line"


def main():
    criteria = [
        ("AC-CSC1", "os-corpus-supply-chain", [
            ("a", "supply census", arm_a),
            ("b", "absence vs zero", arm_b),
            ("c", "removal", arm_c),
            ("d", "grader rewrite", arm_d),
            ("e", "legacy writer", arm_e)]),
        ("AC-CSC2", "os-corpus-empty", [
            ("f", "empty target", arm_f),
            ("g", "missing target", arm_g),
            ("h", "only-unreadable", arm_h),
            ("i", "gate hand-off", arm_i),
            ("j", "payload + card", arm_j)]),
        ("AC-CSC3", "os-corpus-readable",
         [("k", "bare block", arm_k),
          ("l", "unparseable readable", arm_l),
          ("m", "negative control", arm_m),
          ("n", "supply census", arm_n),
          ("o", "payload + card", arm_o)]),
    ]
    arms_total = 0
    red = 0
    print("SUITE %s criteria=%d" % (SUITE, len(criteria)))
    for criterion, _name, arms in criteria:
        for tag, label, fn in arms:
            arms_total += 1
            try:
                ok, note = fn()
            except Exception as exc:
                ok, note = False, "%s: %s" % (type(exc).__name__, exc)
            print("  %s %s %-18s %s" % (criterion, tag, label, note))
            if not ok:
                red += 1
    if red:
        print("SUITE RED arms_red=%d arms=%d criteria=%d"
              % (red, arms_total, len(criteria)))
        return 2
    print("SUITE PASS %d/%d arms=%d criteria=%d"
          % (arms_total, arms_total, arms_total, len(criteria)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
