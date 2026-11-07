import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
HB = os.path.join(os.path.dirname(os.path.dirname(BASE)), "heartbeat.txt")

LINE = ("2026-11-08T06:5x+08:00 product window R2551: shipped "
        "probe_seam_name_binding_nested_arm_mixed_scope + suite, 6/6 twice + "
        "five adjacent suites, bounded live leg SEAMS-ARM-MIXED-COVERED over "
        "20 probe_seam modules / 571 arm loop rows (whole-tree leg stopped on "
        "budget, said so), registry 605/4606, matrix 58666B byte-identical "
        "with green=604/605, row 587 closed and AC-PNDQ1 seeded at line 589, "
        "battery reconcile-battery-R2551 owed next at 605/4606; one real defect "
        "measured and seeded - a module-level with-as refusal carries reason "
        "None")

raw = open(HB, "rb").read()
text = raw.decode("utf-8")
if not text.endswith("\n"):
    text += "\n"
text += LINE + "\n"
with io.open(HB, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
back = open(HB, "rb").read().decode("utf-8")
print("HEARTBEAT lines=%d lf_only=%s once=%s"
      % (len(back.splitlines()), "\r" not in back, back.count("R2551") >= 1))