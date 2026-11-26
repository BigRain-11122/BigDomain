"""preview_writer_census - who writes preview/*.html and who re-derives the face (R3527).

WHY THIS EXISTS: R3524 closed the birth-site gap for one board-page producer,
R3525 for the rest of export_round.BOARD_PAGES, R3526 for one non-board producer
(tools/preview_pair_census.py). Each of those windows measured ONE producer at a
time, so nobody knew how many producers still land a page and then leave
docs/status-export.json naming an older artifact. The board (R3527 item 2) asked
for the whole list once, measured rather than assumed.

The first read-only pass answered the question the hard way: of the 98 non-test
modules that declare a preview/*.html landing path and carry a write call, only
two carried an in-process face re-derivation. The rest are historical board
producers plus a handful of live ones (face_pair_receipt lands a pair every
round). That is the class R3524..R3526 were repairing, and it is wider than the
policy assumed.

MEASUREMENT LAW (source-level, AST, read-only, no child process, no socket):

  reader  the module names a preview .html path but calls no writer
  writer  the module names a preview .html path AND carries a write call
          (write_text, write_atomic, .write, .writelines, or open(..., "w"))
  closed  a writer whose AST carries a real Call to
          board_face_landing.refresh_export_face(...) or to the shipped
          export_round.write(...) - a Call node, so prose in a docstring and a
          commented-out line never count as closure
  gap     a writer with no such call

src/os/export_round.py and src/os/board_face_landing.py are the DEFINITION SITES;
they are excluded by name and counted in `excluded` so the exclusion is audited
rather than silent.

Two halves, one derivation: preview/preview-writer-census.json and .html are
written by the same run, and --check re-derives both in memory and compares them
byte for byte (only `generated_at` is volatile). --check returns before the first
landing write.

Like the other non-board producers this tool lands its pair and then re-derives
docs/status-export.json IN PROCESS through the one shared definition in
src/os/board_face_landing.py (R3526 shape), so landing this page cannot leave the
CEO face aging with no skipped-audit row.
"""

import ast
import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
PREVIEW = os.path.join(REPO, "preview")
LABEL = "preview-writer-census"
JSON_OUT = os.path.join(PREVIEW, LABEL + ".json")
HTML_OUT = os.path.join(PREVIEW, LABEL + ".html")

SCAN_DIRS = ("tools", os.path.join("src", "os"))
EXCLUDED = {
    os.path.join("src", "os", "export_round.py"),
    os.path.join("src", "os", "board_face_landing.py"),
}
WRITE_ATTRS = {"write", "write_text", "write_atomic", "writelines"}
WRITE_NAMES = {"write_text", "write_atomic"}


def round_label(root):
    path = os.path.join(root, "src", "os", "state.json")
    try:
        with io.open(path, encoding="utf-8") as f:
            tick = json.load(f).get("tick")
        return "R%s" % tick if tick else "R?"
    except Exception:
        return "R?"


def _preview_paths(tree):
    """String constants that name or build a preview html landing path."""
    html = []
    has_preview = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        text = node.value
        if "preview" in text and not text.endswith(".html"):
            has_preview = True
        if text.endswith(".html"):
            html.append(text)
            if text.startswith("preview/") or text.startswith("preview\\"):
                has_preview = True
    return has_preview, sorted(set(html))


def _calls(tree):
    writes = 0
    closes = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "refresh_export_face":
            closes += 1
        elif (isinstance(fn, ast.Attribute) and fn.attr == "write"
              and isinstance(fn.value, ast.Name)
              and fn.value.id in ("ER", "export_round")):
            # The shipped face writer doubles as a landing write and a closure.
            writes += 1
            closes += 1
        elif isinstance(fn, ast.Attribute) and fn.attr in WRITE_ATTRS:
            writes += 1
        elif isinstance(fn, ast.Name) and fn.id in WRITE_NAMES:
            writes += 1
        elif isinstance(fn, ast.Name) and fn.id == "open":
            for arg in node.args[1:]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and "w" in arg.value:
                    writes += 1
                    break
    return writes, closes


def classify_source(text):
    """Return (kind, html_paths, writes, closes) for one module's source."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ("unparsed", [], 0, 0)
    has_preview, html = _preview_paths(tree)
    writes, closes = _calls(tree)
    if not has_preview and not html:
        return ("quiet", [], writes, closes)
    if writes == 0:
        return ("reader", html, writes, closes)
    return ("closed" if closes else "gap", html, writes, closes)


def census(root):
    rows = []
    excluded = []
    for rel_dir in SCAN_DIRS:
        folder = os.path.join(root, rel_dir)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".py") or name.startswith("test_"):
                continue
            rel = os.path.join(rel_dir, name)
            if rel in EXCLUDED:
                excluded.append(rel.replace("\\", "/"))
                continue
            try:
                with io.open(os.path.join(folder, name), encoding="utf-8",
                             errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            kind, html, writes, closes = classify_source(text)
            if kind in ("quiet", "unparsed"):
                continue
            rows.append({
                "path": rel.replace("\\", "/"),
                "kind": kind,
                "landing_paths": [p for p in html if "%" not in p and "*" not in p][:4],
                "write_calls": writes,
                "face_calls": closes,
            })
    order = {"gap": 0, "closed": 1, "reader": 2}
    rows.sort(key=lambda r: (order.get(r["kind"], 3), r["path"]))
    totals = {
        "modules": len(rows),
        "writers": sum(1 for r in rows if r["kind"] in ("gap", "closed")),
        "closed": sum(1 for r in rows if r["kind"] == "closed"),
        "gap": sum(1 for r in rows if r["kind"] == "gap"),
        "reader": sum(1 for r in rows if r["kind"] == "reader"),
        "excluded": len(excluded),
    }
    return rows, totals, sorted(excluded)


def payload_for(root):
    rows, totals, excluded = census(root)
    return {
        "generated_at": datetime.datetime.now().astimezone().replace(
            microsecond=0).isoformat(),
        "round": round_label(root),
        "totals": totals,
        "excluded": excluded,
        "rows": rows,
    }


def dumps(payload):
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def html_of(payload):
    t = payload["totals"]
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        "<title>Preview writer census</title>",
        "<style>body{font:14px/1.5 system-ui,sans-serif;margin:2rem;max-width:60rem}"
        "table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ddd;"
        "padding:.3rem .5rem;text-align:left}td.k{font-weight:600}.gap{color:#a11}"
        ".closed{color:#162}</style></head><body>",
        "<h1>Preview writer census (%s)</h1>" % payload["round"],
        "<p>generated_at %s &middot; derived from source, read-only</p>"
        % payload["generated_at"],
        "<p><strong>%d</strong> modules land or read a preview page: "
        "<span class=\"closed\">%d closed</span>, <span class=\"gap\">%d gap</span>, "
        "%d reader &middot; %d definition site(s) excluded.</p>"
        % (t["modules"], t["closed"], t["gap"], t["reader"], t["excluded"]),
        "<table><tr><th>module</th><th>kind</th><th>writes</th>"
        "<th>face calls</th><th>landing paths</th></tr>",
    ]
    for row in payload["rows"][:120]:
        lines.append(
            '<tr><td>%s</td><td class="k %s">%s</td><td>%d</td><td>%d</td>'
            "<td>%s</td></tr>"
            % (row["path"], row["kind"], row["kind"], row["write_calls"],
               row["face_calls"], ", ".join(row["landing_paths"]) or "-"))
    if len(payload["rows"]) > 120:
        lines.append("<tr><td colspan=\"5\">... %d more rows are in the json half"
                     "</td></tr>" % (len(payload["rows"]) - 120))
    lines.append("</table></body></html>")
    return "\n".join(lines) + "\n"


VOLATILE = re.compile(r"generated_at[^,\n]*")


def normalized(text):
    text = text.decode("utf-8") if isinstance(text, bytes) else text
    return VOLATILE.sub("generated_at <volatile>", text.replace("\r\n", "\n"))


def check(payload, json_out, html_out):
    problems = []
    for path, fresh in ((json_out, dumps(payload)), (html_out, html_of(payload))):
        if not os.path.exists(path):
            problems.append("missing half " + os.path.basename(path))
            continue
        with io.open(path, encoding="utf-8", errors="replace", newline="") as f:
            landed = f.read()
        if normalized(landed) != normalized(fresh):
            problems.append("landed half is not this derivation: "
                            + os.path.basename(path))
    return problems


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = REPO
    json_out, html_out = JSON_OUT, HTML_OUT
    if "--root" in argv:
        root = os.path.abspath(argv[argv.index("--root") + 1])
        json_out = os.path.join(root, "preview", LABEL + ".json")
        html_out = os.path.join(root, "preview", LABEL + ".html")
    payload = payload_for(root)
    t = payload["totals"]
    if "--check" in argv:
        problems = check(payload, json_out, html_out)
        if problems:
            print("PWC-CHECK VERDICT FAIL read_only=True")
            for p in problems:
                print("  " + p)
            return 2
        print("PWC-CHECK VERDICT PASS read_only=True modules=%d closed=%d gap=%d "
              "reader=%d" % (t["modules"], t["closed"], t["gap"], t["reader"]))
        return 0

    out_dir = os.path.dirname(json_out)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with io.open(json_out, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(payload))
    with io.open(html_out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_of(payload))
    try:
        sys.path.insert(0, os.path.join(root, "src", "os"))
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(root)
        face = "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # a private world may carry no shared writer
        face = "SKIPPED %s" % type(exc).__name__
    print("PWC (%s) modules=%d closed=%d gap=%d reader=%d face export=%s"
          % (payload["round"], t["modules"], t["closed"], t["gap"],
             t["reader"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main())
