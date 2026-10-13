# -*- coding: utf-8 -*-
"""R1947 in-round erratum step: first run of the suite returned
6/7 - AC-EFP5's frozen-face wording swept the two credits that the
AC-EFP4 continuation consumes BY DESIGN (consumption marking is
the module's single UPDATE surface) into the full-field freeze.
Family precedent R1883 (AC-PN27 expectation typo, same-round fix
with honest note): amend the registered criteria text in the
tech.md claim row before the code fix, so the register and the
suite stay in agreement. Surgical anchor replace; EOL preserved."""
import io

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
P_TECH = ROOT + r"\state\queue\tech.md"

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    raw = fh.read()
eol = "\r\n" if "\r\n" in raw else "\n"

OLD = ("**AC-EFP5**\uff08\u51bb\u7ed3\u884c+\u91cd\u653e"
       "\u95e8\uff09=\u53cc\u8868\u65e2\u6709\u884c\u5168\u5b57"
       "\u6bb5\u51bb\u7ed3 vs \u5173\u524d\u5feb\u7167\u3014"
       "\u542b consumed_utc/used_effect \u7ed1\u5b9a\u3015+")
NEW = ("**AC-EFP5**\uff08\u51bb\u7ed3\u884c+\u91cd\u653e"
       "\u95e8\u3014R1947 \u9996\u8dd1\u52d8\u6b63\u5f53\u7a97"
       "\u5982\u5b9e\u6ce8\uff1a\u521d\u7248\u51bb\u7ed3\u9762"
       "\u628a\u7eed\u5199\u8bbe\u8ba1\u6027\u6d88\u8d39\u884c "
       "credit#3/#4 \u4e5f\u5165\u5168\u5b57\u6bb5\u51bb\u7ed3="
       "\u5224\u636e\u8bbe\u8ba1\u7b14\u8bef\uff08\u6d88\u8d39"
       "\u6807\u8bb0=\u6a21\u5757\u552f\u4e00 UPDATE \u9762=\u7eed"
       "\u5199\u5fc5\u89e6\u00b7R1883 \u540c\u8f6e\u4fee\u5148"
       "\u4f8b\uff09\u3011=\u51bb\u7ed3\u9762\u5206\u4e09\u9053="
       "\u7eed\u5199\u672a\u89e6\u884c\u5168\u5b57\u6bb5\u51bb"
       "\u7ed3 vs \u5173\u524d\u5feb\u7167\u3014\u5173\u524d\u5df2"
       "\u6d88 #1/#2 \u542b consumed_utc/used_effect \u7ed1\u5b9a"
       "+\u672a\u89e6 #5\u3015+\u7eed\u5199\u6d88\u8d39\u884c #3/"
       "#4 \u8eab\u4efd\u5217\u3014\u5217 0..6 \u542b purchased_"
       "utc\u3011\u51bb\u7ed3+\u6d88\u8d39\u8fc1\u79fb\u4e8b\u5b9e"
       "\u65ad\u8a00\u3014#3.used_effect==\u6548\u679c#4\u00b7#4."
       "used_effect==\u6548\u679c#3\u00b7consumed_utc \u4e24\u884c"
       "\u5747\u7f6e\u975e\u7a7a\u3015+\u6548\u679c\u8868\u65e2"
       "\u6709\u884c\u5168\u5b57\u6bb5\u51bb\u7ed3\u3014\u4e0d"
       "\u53ef\u53d8\u884c\u96f6 UPDATE\u3015+")

assert raw.count(OLD) == 1, "AC-EFP5 old wording not unique: %d" % (
    raw.count(OLD),)
raw = raw.replace(OLD, NEW, 1)
assert raw.count(NEW) == 1

with io.open(P_TECH, "w", encoding="utf-8", newline="") as fh:
    fh.write(raw)
print("erratum registered: AC-EFP5 frozen-face wording amended "
      "in the tech.md claim row (three-lane freeze law)")
