"""R2692 birth-site repair: the log block has TWO item indents.

The fold layout reader derives the item indent from the FIRST item line and
refuses a file whose items disagree (state_fold.split_layout, added at R2522
exactly because a hard-coded 16 refused a 2-space file). This file's items sit
at 2 spaces except THIRTEEN lines - the seven R2691 closeout lines and the six
this window appended - because state_io.ITEM_INDENT reads 16.

The repair is at the birth site and changes NO content: every item line inside
the log block has its leading indent rewritten to the indent the first item
already uses, and the parse is asserted EQUAL before and after. The constant
is then set to the indent the file really uses, so the next appender cannot
re-break it. Dry run by default; --execute writes.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
CONST = os.path.join(HERE, "state_io.py")


def main(argv):
    execute = "--execute" in argv
    text = state_io.decode(state_io.read_raw(PATH))
    before = state_io.parse(text)
    doc = state_io._lf_lines(text)
    start, end = state_io._log_block(doc)
    first_indent = len(doc[start + 1]) - len(doc[start + 1].lstrip(" "))
    moved = []
    out = list(doc)
    for index in range(start + 1, end):
        row = out[index]
        stripped = row.lstrip(" ")
        indent = len(row) - len(stripped)
        if indent != first_indent:
            moved.append((index + 1, indent))
            out[index] = " " * first_indent + stripped
    payload = state_io.EOL.join(out)
    after = state_io.parse(payload)
    identical = json.dumps(before, sort_keys=True) == json.dumps(after,
                                                                sort_keys=True)
    const_text = io.open(CONST, encoding="utf-8").read()
    has_const = "ITEM_INDENT = 16" in const_text
    print("layout first_indent=%d moved=%d identical=%s const16=%s"
          % (first_indent, len(moved), identical, has_const))
    for line_no, indent in moved:
        print("  line %d indent %d -> %d" % (line_no, indent, first_indent))
    if not identical:
        print("REFUSED the parse moved")
        return 3
    if not execute:
        print("PLANNED (dry run, nothing written)")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2692l_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload.encode("utf-8"):
        print("REFUSED read-back mismatch")
        return 4
    if has_const:
        new_const = const_text.replace("ITEM_INDENT = 16",
                                       "ITEM_INDENT = %d" % first_indent)
        io.open(CONST, "w", encoding="utf-8", newline="\n").write(new_const)
    print("REPAIRED bytes=%d const=%d" % (len(payload.encode("utf-8")),
                                          first_indent))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
