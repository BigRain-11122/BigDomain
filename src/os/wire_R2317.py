import io

p = 'src/sandbox/reconcile_all.py'
t = io.open(p, encoding='utf-8', newline='').read()

old = (
    '    ("os-gate-decl-identity-wire",\n'
    '     os.path.join("..", "os", "test_gate_decl_identity_wire.py"), 6),\n'
)
new = old + (
    '    # R2317: the declaration could gain an entry but never lose one, so a\n'
    '    # completed row left its blocker declared forever and only a hand edit\n'
    '    # could retire it; the writer asks machine_gate own live reading and\n'
    '    # refuses an entry that is still blocking. (AC-GDRT1..AC-GDRT6 pinned\n'
    '    # in state/queue/tech.md as the R2312 seed row BEFORE the code.)\n'
    '    ("os-gate-decl-retire",\n'
    '     os.path.join("..", "os", "test_gate_decl_retire.py"), 6),\n'
)

assert t.count(old) == 1, t.count(old)
io.open(p, 'w', encoding='utf-8', newline='').write(t.replace(old, new))
print('wired')