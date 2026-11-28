"""Battery suite: the chain page publishes the record-chain QUALIFICATION (R3620).

AC-FYCQ1..AC-FYCQ5 were pinned in src/os/backlog.md BEFORE this file existed.
The defect they hold: preview/first-yuan-chain.html printed the money chain as
counts (entries, transactions, balanced, unbalanced) and nothing else, so a
reader had to take `unbalanced=0` on luck rather than on a stated judgement -
the same disease the command-line station (R3618) and the CEO export (R3619)
have already had repaired.

What is measured here: the page's record-chain block comes from the export's
own producer (`status_export_fresh.chain_face`), no second ledger parser is
kept in the tool, an unaskable face publishes UNADJUDICATED with nulls rather
than OK/0, the landed json and html agree with the live block, and `--check`
stays read-only.

Isolation: the live ledger and the landed pair are read, never written; the
blind-face arm patches one module attribute and restores it. Stdlib only,
ASCII source, no network.
"""

import ast
import inspect
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
TOOLS = os.path.join(ROOT, "tools")
for _path in (TOOLS, BASE):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import first_yuan_chain as FY  # noqa: E402
import status_export_fresh as sx  # noqa: E402

CRITERIA = ("AC-FYCQ1", "AC-FYCQ2", "AC-FYCQ3", "AC-FYCQ4", "AC-FYCQ5")
FAILS = []
CHECKS = [0]

HTML_PATH = os.path.join(ROOT, "preview", "first-yuan-chain.html")
JSON_PATH = os.path.join(ROOT, "preview", "first-yuan-chain.json")


def check(ac, ok, evidence):
    CHECKS[0] += 1
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)
    if not ok:
        FAILS.append(ac)


def body_dump(fn):
    """The function's CODE, docstring stripped: prose explains a law, a
    duplicated call restates it, and only the latter is a defect."""
    tree = ast.parse(inspect.getsource(fn))
    body = tree.body[0].body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return "\n".join(ast.dump(part) for part in body)


def blind_call(call):
    """Run `call` with the export producer made unaskable."""
    saved = sx.chain_face
    sx.chain_face = lambda root: (_ for _ in ()).throw(RuntimeError("blind"))
    try:
        return call()
    finally:
        sx.chain_face = saved


def shared_definition_arm():
    helper = body_dump(FY.record_chain_face)
    # One call site: the AST carries the call as an attribute access named
    # chain_face, so counting that attr is counting the calls and nothing else
    # (the first draft counted "chain_face(", which the dump never contains).
    once = helper.count("attr='chain_face'") == 1
    no_second_parse = all(token not in helper
                          for token in ("ledger_report", "qa_replacements",
                                        "old_sha16", "new_sha16"))
    blind = blind_call(FY.record_chain_face)
    landed = json.loads(json.dumps(blind, sort_keys=True))
    proves_asked = (landed["adjudication"] == "UNADJUDICATED"
                    and landed["partial"] is None
                    and landed["rows"] is None
                    and landed["broken"] is None)
    restored = FY.record_chain_face()

    check("AC-FYCQ1", once and no_second_parse and proves_asked
          and restored["rows"] is not None,
          "one chain_face() call=%s, no second parse=%s, blind reads %s, "
          "restored rows=%r" % (once, no_second_parse,
                                landed["adjudication"], restored["rows"]))


def landed_arm():
    block = FY.record_chain_face()
    owner = sx.chain_face(ROOT)
    same = all(block[key] == owner.get(key) for key in FY.CHAIN_KEYS)
    doc = json.loads(io.open(JSON_PATH, encoding="utf-8").read())
    json_same = doc.get("record_chain") == block
    page = io.open(HTML_PATH, encoding="utf-8").read()
    printed = ("The record chain behind this page" in page
               and ("adjudication=%s" % FY.shown(block["adjudication"])) in page
               and ("rows=%s" % FY.shown(block["rows"])) in page
               and ("broken=%s" % FY.shown(block["broken"])) in page
               and ("unexplained=%s" % FY.shown(block["unexplained"])) in page)
    check("AC-FYCQ2", same and json_same and printed,
          "live block=%s equal_to_export=%s landed_json_equal=%s page_printed=%s"
          % (json.dumps(block, sort_keys=True), same, json_same, printed))


def blind_arm():
    stand_in = dict((key, None) for key in FY.CHAIN_KEYS)
    stand_in["adjudication"] = "UNADJUDICATED"
    dashes = all(FY.shown(stand_in[key]) == "-"
                 for key in ("present", "rows", "broken", "partial",
                             "declared", "unexplained", "excused"))
    round_trip = json.loads(json.dumps(stand_in, sort_keys=True))
    nulls_kept = (round_trip["broken"] is None
                  and round_trip["partial"] is None
                  and round_trip["declared"] is None)
    check("AC-FYCQ3", dashes and nulls_kept,
          "unmeasured values render as dashes=%s, JSON round-trip keeps null=%s"
          % (dashes, nulls_kept))


def read_only_arm():
    before = (os.path.getsize(HTML_PATH), os.stat(HTML_PATH).st_mtime_ns,
              os.path.getsize(JSON_PATH), os.stat(JSON_PATH).st_mtime_ns)
    twin = (json.dumps(FY.record_chain_face(), sort_keys=True)
            == json.dumps(FY.record_chain_face(), sort_keys=True))
    rc = FY.do_check()
    after = (os.path.getsize(HTML_PATH), os.stat(HTML_PATH).st_mtime_ns,
             os.path.getsize(JSON_PATH), os.stat(JSON_PATH).st_mtime_ns)
    check("AC-FYCQ4", rc == 0 and before == after and twin,
          "--check rc=%d, pair (size,mtime_ns) unchanged=%s, twin reads "
          "identical=%s" % (rc, before == after, twin))


def hygiene_arm():
    source = io.open(os.path.join(TOOLS, "first_yuan_chain.py"), "rb").read()
    try:
        source.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    text = source.decode("ascii", "replace")
    no_network = all(token not in text
                     for token in ("import socket", "import urllib",
                                   "import http", "import requests"))
    registry = io.open(os.path.join(ROOT, "src", "sandbox", "reconcile_all.py"),
                       encoding="utf-8").read()
    wired = '("os-first-yuan-record-chain",' in registry
    check("AC-FYCQ5", ascii_ok and no_network and wired,
          "ASCII=%s, no network=%s, wired in reconcile_all=%s"
          % (ascii_ok, no_network, wired))


def main():
    shared_definition_arm()
    landed_arm()
    blind_arm()
    read_only_arm()
    hygiene_arm()
    verdict = "PASS" if not FAILS else "FAIL:" + ",".join(FAILS)
    print("SUITE %s %d/%d" % (verdict, CHECKS[0] - len(FAILS), CHECKS[0]),
          flush=True)
    print("SUITE criteria=%d failed=%s"
          % (len(CRITERIA), ",".join(FAILS) or "(none)"), flush=True)
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
