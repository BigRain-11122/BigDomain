# wire_R2253.py - add the os-queue-row suite to the reconcile runner.
import io
import sys

PATH = "src/sandbox/reconcile_all.py"
OLD = '     os.path.join("..", "os", "test_debt_append.py"), 6),\n    ]'
NEW = ('     os.path.join("..", "os", "test_debt_append.py"), 6),\n'
       "    # R2253: a claimable queue row must name its criteria prefix, so\n"
       "    # pre-registration is a gate instead of a habit. The row law is\n"
       "    # imported from queue_floor rather than rewritten, two declaration\n"
       "    # forms are accepted and only those two, gated rows are exempt but\n"
       "    # still reported, and every refusal carries a file and a line.\n"
       "    # (AC-QROW1..AC-QROW6 pre-registered in state/queue/tech.md as the\n"
       "    # R2248 b seed BEFORE the code existed.)\n"
       '    ("os-queue-row",\n'
       '     os.path.join("..", "os", "test_queue_row.py"), 6),\n'
       "    ]")


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read()
    count = text.count(OLD)
    if count != 1:
        print("E_WIRE count=%d" % count)
        return 1
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace(OLD, NEW))
    check = io.open(PATH, encoding="utf-8", newline="").read()
    print("WIRED label=%r suite=%r"
          % ('"os-queue-row"' in check, "test_queue_row.py" in check))
    return 0


if __name__ == "__main__":
    sys.exit(main())