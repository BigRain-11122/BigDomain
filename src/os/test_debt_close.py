"""debt_close suite (R2274; criteria AC-DEBC1..AC-DEBC6 were pinned in
state/queue/tech.md as the R2251 seed row BEFORE this code existed).

What this proves: debt_append gave the register a writer for open rows, but
closing one is still hand surgery - a window edits "- [ ]" to "- [x]" and
types closed=R<n> by hand, so a wrong stamp, or a closed row that keeps
first=yes, stays invisible until debt_register refuses the whole file. This
suite pins the one callable that closes exactly one row by item and proves
the result through the register's own parser and counter.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import glob
import hashlib
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

import debt_close as DC  # noqa: E402
import debt_register as DR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "debt_close.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-close"
WIRED_EXPECT = '"test_debt_close.py"), 6),'

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


OPEN_FIRST = ("- [ ] opened=R2273 | item=product-face-R2274 | "
              "note=back to the product face | first=yes")
OPEN_PLAIN = ("- [ ] opened=R2231 | item=loop-s4u-reconcile | "
              "note=needs elevation | first=no")
DONE_ROW = "- [x] opened=R2272 | item=product-face-R2273 | closed=R2273"


def make_world(rows, raw=None):
    """Build a temp root carrying state/debt.md."""
    world = tempfile.mkdtemp(prefix="bigdomain-debc-")
    inner = os.path.join(world, "state")
    os.makedirs(inner)
    body = raw if raw is not None else "\n".join(rows) + "\n"
    with io.open(os.path.join(inner, "debt.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return world


def register_path(world):
    return os.path.join(world, "state", "debt.md")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def refusal(world, item, round_label="R2274"):
    """The module's own code, or NONE when the close was not refused."""
    try:
        DC.close_row(world, item, round_label, execute=True)
    except DC.DebtCloseError as exc:
        return exc.code
    return "NONE"


# AC-DEBC1: one open row becomes exactly one done row carrying the close
# stamp, and the read-back moves the register's own counts by one each way.
world = make_world([OPEN_FIRST, OPEN_PLAIN, DONE_ROW])
planned = DC.close_row(world, "product-face-R2274", "R2274")
fresh = make_world([OPEN_FIRST, OPEN_PLAIN, DONE_ROW])
done = DC.close_row(fresh, "product-face-R2274", "R2274", execute=True)
back = read_text(register_path(fresh))
closed_lines = [line for line in back.split("\n")
                if line.startswith("- [x]") and "product-face-R2274" in line]
measured = DR.register(fresh, "R2274")
check(planned["open_before"] == 2 and planned["open_after"] == 1
      and planned["done_before"] == 1 and planned["done_after"] == 2
      and planned["line"] == 1
      and planned["row"].startswith("- [x] ")
      and "closed=R2274" in planned["row"]
      and "first=" not in planned["row"]
      and len(closed_lines) == 1
      and len([line for line in back.split("\n")
               if line.startswith("- [ ]")]) == 1
      and measured["open_count"] == 1 and measured["done_count"] == 2
      and measured["first_count"] == 0
      and done["read_back_ok"] is True,
      "AC-DEBC1 one row closed, counts move by one, no first left behind")

# AC-DEBC2: unknown, already-done and ambiguous items are refused with their
# own codes and the file bytes stay unchanged.
unknown_world = make_world([OPEN_FIRST, DONE_ROW])
before_unknown = digest(register_path(unknown_world))
code_unknown = refusal(unknown_world, "no-such-item")
after_unknown = digest(register_path(unknown_world))
code_done = refusal(unknown_world, "product-face-R2273")
after_done = digest(register_path(unknown_world))
ambiguous = make_world([OPEN_FIRST,
                        "- [ ] opened=R2260 | item=product-face-R2274 | "
                        "note=duplicate | first=no"])
before_ambiguous = digest(register_path(ambiguous))
code_ambiguous = refusal(ambiguous, "product-face-R2274")
after_ambiguous = digest(register_path(ambiguous))
check(code_unknown == "E_DEBC_UNKNOWN"
      and code_done == "E_DEBC_ALREADY_DONE"
      and code_ambiguous == "E_DEBC_AMBIGUOUS"
      and before_unknown == after_unknown == after_done
      and before_ambiguous == after_ambiguous,
      "AC-DEBC2 unknown, already-done and ambiguous refused, bytes unchanged")

# AC-DEBC3: a close round before opened is refused, and closing the row that
# leads the next window removes the first flag instead of keeping it.
early_world = make_world([OPEN_FIRST, OPEN_PLAIN])
before_early = digest(register_path(early_world))
code_early = refusal(early_world, "product-face-R2274", "R2200")
code_not_round = refusal(early_world, "product-face-R2274", "2274")
after_early = digest(register_path(early_world))
head_world = make_world([OPEN_FIRST, OPEN_PLAIN])
head_report = DC.close_row(head_world, "product-face-R2274", "R2274",
                           execute=True)
head_text = read_text(register_path(head_world))
head_rows = DR.parse(head_text)
flag_rows = [row for row in head_rows if row["first"] == "yes"]
check(code_early == "E_DEBC_BAD_ROUND"
      and code_not_round == "E_DEBC_BAD_ROUND"
      and before_early == after_early
      and head_report["read_back_ok"] is True
      and not flag_rows
      and DR.register(head_world)["first_count"] == 0
      and DR.first_item(DR.register(head_world)) is None,
      "AC-DEBC3 predating or malformed round refused, first flag dropped")

# AC-DEBC4: a register that does not parse is refused before any write, and
# the read-back runs through debt_register.register rather than a private
# counter (proved by patching it).
broken_world = make_world(["- [ ] opened=R2266 | item=x | first=maybe"])
before_broken = digest(register_path(broken_world))
code_broken = refusal(broken_world, "x", "R2274")
after_broken = digest(register_path(broken_world))
patch_world = make_world([OPEN_FIRST, DONE_ROW])
real_register = DR.register


def lying_register(root, current_round=None):
    report = real_register(root, current_round)
    report["open_count"] = report["open_count"] + 1
    return report


DR.register = lying_register
patched_code = refusal(patch_world, "product-face-R2274")
DR.register = real_register
check(code_broken == "E_DEBC_BAD_REGISTER"
      and before_broken == after_broken
      and patched_code == "E_DEBC_SHAPE",
      "AC-DEBC4 unparseable register refused; read-back goes through register")

# AC-DEBC5: dry run predicts the exact post bytes and writes nothing; the
# execute leg is one atomic replace proved by read-back with no temp residue.
dry_world = make_world([OPEN_FIRST, OPEN_PLAIN, DONE_ROW])
before_dry = digest(register_path(dry_world))
dry = DC.close_row(dry_world, "product-face-R2274", "R2274")
after_dry = digest(register_path(dry_world))
exec_world = make_world([OPEN_FIRST, OPEN_PLAIN, DONE_ROW])
exec_report = DC.close_row(exec_world, "product-face-R2274", "R2274",
                           execute=True)
on_disk = os.path.getsize(register_path(exec_world))
residue = glob.glob(os.path.join(exec_world, "state", "*.debc-tmp"))
check(before_dry == after_dry
      and dry["wrote"] is False and dry["read_back_ok"] is None
      and dry["predicted_bytes"] > dry["before_bytes"]
      and exec_report["wrote"] is True
      and exec_report["read_back_ok"] is True
      and on_disk == dry["predicted_bytes"]
      and not residue,
      "AC-DEBC5 dry run predicts exactly, atomic write leaves no residue")

# AC-DEBC6: purity, wiring, and a live read-only dry run on the real register.
with io.open(MODULE, "r", encoding="utf-8") as handle:
    source = handle.read()
non_ascii = [ch for ch in source if ord(ch) > 127]
imports = [line.strip() for line in source.splitlines()
           if line.strip().startswith("import ")
           or line.strip().startswith("from ")]
banned = ("socket", "urllib", "requests", "http", "time", "datetime",
          "subprocess")
net_hits = [line for line in imports if any(word in line for word in banned)]
with io.open(RUNNER, "r", encoding="utf-8") as handle:
    runner = handle.read()
live_before = digest(os.path.join(REPO, "state", "debt.md"))
live_register = DR.register(REPO, "R2274")
open_items = [row["item"] for row in live_register["rows"]
              if row["state"] == "open"]
probe = open_items[0] if open_items else None
if probe is not None:
    live = DC.close_row(REPO, probe, "R2274")
    code_cli_zero, out_cli_zero = run_cli(["--item", probe,
                                           "--round", "R2274"])
else:
    live = None
    code_cli_zero, out_cli_zero = run_cli(["--item", "no-such-item",
                                           "--round", "R2274"])
live_after = digest(os.path.join(REPO, "state", "debt.md"))
code_cli_two, out_cli_two = run_cli(["--item", "no-such-item",
                                    "--round", "R2274"])
code_cli_five, _ = run_cli(["--bogus"])
live_ok = (live["open_after"] == live["open_before"] - 1
           and live["wrote"] is False
           and "DEBT CLOSE" in out_cli_zero) if live is not None else True
check(not non_ascii and not net_hits
      and WIRED_EXPECT in runner and LABEL in runner
      and live_before == live_after
      and live_ok
      and code_cli_zero == 0
      and code_cli_two == 2 and "E_DEBC_UNKNOWN" in out_cli_two
      and code_cli_five == 5,
      "AC-DEBC6 pure ASCII, stdlib only, wired, CLI 0/2/5, zero writes")

print("LIVE %s" % (DC.one_line(live) if live is not None
                   else "DEBT CLOSE live register carries no open row"), flush=True)
print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                          PASSES, EXPECTED_CRITERIA), flush=True)
sys.exit(0 if FAILS == 0 else 1)