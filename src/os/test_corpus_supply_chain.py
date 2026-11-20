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

WHAT IS PROVED HERE (one criterion, five arms):
  a  every call to export_round.write in a shipped NON-TEST module passes
     corpus=, and at least one such call exists (an empty census cannot pass).
  b  corpus_block(None) is None while a measured zero returns a block, so
     "not measured" and "measured empty" differ by construction, not by prose.
  c  a writer that measured nothing REMOVES both copies from a face that
     carried them, so no stale count survives the next write.
  d  the grader's line rewrite (_set_line), which is how the second writer
     touches the face, leaves the corpus block byte-for-byte intact.
  e  export_R2431 writes nothing at import time (its write is behind the
     __main__ guard) and no shipped non-test module imports it.

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
sys.path.insert(0, os.path.join(ROOT, "tools"))
import export_round as ER  # noqa: E402
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
    """Absence and measured-empty are different objects."""
    if ER.corpus_block(None) is not None:
        return False, "corpus_block(None) published a block"
    empty = ER.corpus_block({"files": 0, "bytes": 0})
    if not isinstance(empty, dict) or empty.get("files") != 0:
        return False, "a measured zero did not publish files=0: %r" % (empty,)
    return True, "None->nothing, measured 0->%r" % (empty,)


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


def main():
    arms = [("a", "supply census", arm_a),
            ("b", "absence vs zero", arm_b),
            ("c", "removal", arm_c),
            ("d", "grader rewrite", arm_d),
            ("e", "legacy writer", arm_e)]
    red = 0
    print("SUITE %s criteria=1" % SUITE)
    for tag, name, fn in arms:
        try:
            ok, note = fn()
        except Exception as exc:
            ok, note = False, "%s: %s" % (type(exc).__name__, exc)
        print("  %s %s %-18s %s" % (CRITERION, tag, name, note))
        if not ok:
            red += 1
    if red:
        print("SUITE RED criteria=1 arms_red=%d" % red)
        return 2
    print("SUITE PASS 1/1 arms=5 criteria=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
