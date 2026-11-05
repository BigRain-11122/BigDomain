import io

P = "src/sandbox/reconcile_all.py"
OLD = ('    ("os-relative-module-existence-face",\n'
       '     os.path.join("..", "os", "test_relative_module_existence_face.py"), 6),\n')
NEW = OLD + (
    "    # R2491: the existence face measures its corpus by walking the root it is\n"
    "    # given, so a join whose module lives OUTSIDE that root (an installed\n"
    "    # package, or a publisher in a subdirectory while the package sits at the\n"
    "    # tree top) read MISSING-MODULE exactly like a broken import. Every absence\n"
    "    # now carries the scope it was judged against - the root as given and the\n"
    "    # corpus size - and caller-declared extra names are merged on top of the\n"
    "    # measured tree instead of replacing it. (AC-RMSC1..AC-RMSC6 pinned in\n"
    "    # state/queue/tech.md:525 as the R2440 seed row BEFORE the code.)\n"
    '    ("os-relative-module-corpus-scope",\n'
    '     os.path.join("..", "os", "test_relative_module_corpus_scope.py"), 6),\n')

text = io.open(P, encoding="utf-8", newline="").read()
assert text.count(OLD) == 1, text.count(OLD)
io.open(P, "w", encoding="utf-8", newline="").write(text.replace(OLD, NEW))
print("wired")