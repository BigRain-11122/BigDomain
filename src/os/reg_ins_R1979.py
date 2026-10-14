# reg_ins_R1979.py - insert yearbook suite into reconcile_all SUITES registry
import io

P = r"src\sandbox\reconcile_all.py"
s = io.open(P, encoding="utf-8").read()
anchor = ('    ("ledger-honorcert",\n'
          '     os.path.join("ledger", "test_honorcert.py"), 7),\n')
assert s.count(anchor) == 1, "anchor not unique: %d" % s.count(anchor)
ins = ('    # R1979 honor yearbook certified-only roster read face:\n'
       '    # single-source derivation from the honor_certs read face\n'
       '    # (zero own board walks, zero own collection reads), keeps\n'
       '    # certified members in board order with the certificate\n'
       '    # provenance echo (item_id) and live board rank; board-scoped\n'
       '    # honest derivation limit (off-board certificate holders\n'
       '    # stay outside the view, the certificate itself is permanent\n'
       '    # in the collectibles domain); zero-certified year returns an\n'
       '    # honest empty roster; pure read (zero writes, zero storage,\n'
       '    # zero token movement, zero RNG) (AC-HY1..HY7 pre-registered\n'
       '    # in the R1979 explore-queue claim row).\n'
       '    ("ledger-honorcert-yearbook",\n'
       '     os.path.join("ledger", "test_honorcert_yearbook.py"), 7),\n')
s = s.replace(anchor, anchor + ins)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("REGISTRY-INSERTED")
