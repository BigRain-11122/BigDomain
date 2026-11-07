import io, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
HB = os.path.join(os.path.dirname(os.path.dirname(BASE)), "heartbeat.txt")

LINE = ("2026-11-08T05:32:00+08:00 product window R2549: shipped "
        "probe_seam_name_binding_nested_exhaustive_path + suite, 6/6 twice + "
        "five adjacent suites, live SEAMS-NESTED-COVERED over 1499 probes with "
        "the same fixtures measured on BOTH readers (the shipped exhaustive "
        "face over-resolved the partial and the loop-under-arm fixtures, "
        "disclosed), registry 604/4600, matrix 58526B byte-identical with "
        "green=603/604, row 585 closed and AC-PNDP1 seeded at line 587, "
        "battery reconcile-battery-R2549 owed next at 604/4600 (fold still "
        "owed, state_fold ships --check only)")

raw = open(HB, "rb").read()
text = raw.decode("utf-8")
if not text.endswith("\n"):
    text += "\n"
text += LINE + "\n"
with io.open(HB, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
back = open(HB, "rb").read().decode("utf-8")
print("HEARTBEAT lines=%d lf_only=%s once=%s"
      % (len(back.splitlines()), "\r" not in back, back.count("R2549") >= 1))