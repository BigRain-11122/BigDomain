"""Suite for the one-click sandbox launcher (open_sandbox.py).

Eight criteria. AC-OSB1..AC-OSB3 were pre-registered in src/os/backlog.md at
R3333 BEFORE this module existed (the board head asked for the disposition to be
scriptized instead of hand-copied into qa/, and for a teardown reading that can
say a child really is gone); AC-OSB6 was pre-registered at R3334 (the board head
asked for a pre-launch probe of the previous run's port table); AC-OSB7 was
pre-registered at R3335 and AC-OSB8 at R3339 (the board head asked whether an
answering port can be attributed to US without guessing, and then whether the
OS itself can name the owner instead of the report):

  AC-OSB1  the process-table reader the launcher uses is real: a child started
           by this suite appears in descendants(), and after it exits the same
           collector no longer reports it.
  AC-OSB2  a real `--check --qa-log NAME` run answers rc=0 with
           gone=N/N leftovers=none and writes its own disposition through the
           shipped writer into a directory outside the repo (an in-repo
           non-qa/ destination is refused by that writer, measured at R3333).
  AC-OSB3  the leftover reading BITES: with the test seam --hold-secs a child
           ignores the stop file, the verdict is FAIL rc=2, the survivor is
           named pid:exe, and it is reaped - so "clean" is a measurement, not
           an assumption.
  AC-OSB4  there is ONE evidence writer: the module routes through
           tools/qa_log.py (measured by asking that writer to refuse a bad name
           through the same import the launcher uses) and it contains no second
           open()/write path into qa/. R3349 re-pinned the reading from a count
           of do_write() sites (a shape of the tree) to the LIST of offending
           open() calls, proven on a mutant that adds a bypass writer.
  AC-OSB5  the battery registry carries this suite exactly once and declares the
           same criterion count this file reports. R3349 re-pinned the reading
           from len(rows)==1 to the declaration list, proven on a private copy
           whose duplicate and stale counts must both show up.
  AC-OSB6  the previous run's port table is read before it is deleted: the
           union of ports/face_ports names each number once, a REAL listener on
           a recorded port is seen and cleared when it closes, and the same
           table on disk makes the launcher refuse (rc=2, port named, boundary
           stated, no face started). The two real runs above point --prev-report
           at a private empty table so ambient machine state cannot red them.
  AC-OSB7  an answering port is ATTRIBUTED without guessing, on the readings
           that need no OS table: a port whose face pid is still alive reads
           ours:pid-alive, the same port after that pid is gone reads
           foreign:pid-gone, and a REAL shipped hub answering its own payload
           reads ours:hub-api - with a control that disables the payload reader
           and reads unknown:no-pid, so the identity check is load-bearing
           rather than decorative. R3339 holds this arm to the fallback path on
           purpose (sockets={}): it is the law a host without iphlpapi keeps.
  AC-OSB8  the OS listen table decides ownership when it is readable (R3339
           measured a real launcher run: the six face ports matched their
           recorded pids exactly, while the hub, ws, city and gate ports
           belonged to the lobby child and NOT to the launcher pid the report
           records as registry): a face port whose recorded pid IS the socket
           owner reads ours:sock-pid; the SAME socket recorded against another
           live python child reads foreign:sock-pid-other (this is the shape
           AC-OSB7 used to read as ours:pid-alive - corrected, not relaxed); a
           child that binds its own socket reads ours:sock-pid, so the reading
           follows the OS and not this process; a real shipped hub owned by a
           recorded pid reads ours:sock-pid while the same hub against an
           unrecorded pid reads foreign:sock-pid-unrecorded; and a refused
           table (listen_owners answering {}) falls back instead of inventing an
           owner.
  AC-OSB9  a recorded pid that came back as a DIFFERENT process is not called a
           leftover and never reaped (R3339 measured a survivor named ssh.exe
           in an arm whose only child was python: a number recycled by the OS).
           Five injected readings: same image and same creation time reads
           left; a changed image reads reused(image); the same image with a new
           creation time reads reused(creation-time); an absent pid reads gone;
           a host whose creation time cannot be read keeps the image test and
           says so. The old "pid in table" form is reproduced in the same arm
           as the decoy, so the arm shows what it is protecting against.
  AC-OSB10 an orphan a run never watched start is named by the NEXT run
           (R3342): a live python child recorded by an earlier run makes the
           launcher REFUSE with rc=2 before any face is started and the survivor
           is named pid:exe; a recycled number (same image, moved creation time)
           does NOT refuse and reads reused=1; after that child is gone the same
           record reads orphans=none and is cleared. The record is what a HARD
           killed launcher leaves behind, which is the only witness of the
           11-22 shape (a leftover holding no port, invisible to a teardown that
           only sees its own subtree).

Cost measured at R3333: the two sandbox runs are about 3.6s each (the faces come
up and are torn down for real); the collector arm and the socket arms are under
a second, and the refusal arm returns before any face is spawned. AC-OSB7 adds
one sleeping child and one in-process hub (well under a second). AC-OSB10 adds
three launcher runs - two refuse or clear before any face is started, one runs
the full tree - about 8s on this machine.
"""

import ast
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODULE = os.path.join(HERE, "open_sandbox.py")
WRITER = os.path.join(ROOT, "tools", "qa_log.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
TOTAL = 10


class _TableAbsent(Exception):
    """A judged, named skip for an arm that needs the OS listen table."""


def load_module():
    spec = importlib.util.spec_from_file_location("bd_open_sandbox", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def direct_qa_writers(source):
    """Name every open() call in `source` that addresses the qa dir itself.

    A second call through the SAME shipped writer is not a defect, so the law
    cannot be a count of do_write() sites - that is a shape of the tree. What
    is a defect is a second writer: any open() call whose own source names qa.
    """
    offenders = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if getattr(func, "id", None) != "open" and getattr(func, "attr", None) != "open":
            continue
        segment = " ".join((ast.get_source_segment(source, node) or "").split())
        if "qa" in segment:
            offenders.append(segment[:60])
    return offenders


def registry_declarations(text, label):
    """Every declared criteria count for `label`, in file order."""
    pattern = r'\("%s",\s*[^,]+,\s*(\d+)\)' % re.escape(label)
    return [int(count) for count in re.findall(pattern, text)]


def run_launcher(args, timeout=180):
    proc = subprocess.run([sys.executable, MODULE] + args, cwd=ROOT,
                          capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main():
    failed = 0
    module = load_module()

    # ---------------- AC-OSB1 ----------------
    try:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(6)"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        try:
            seen = []
            deadline = time.time() + 5.0
            while time.time() < deadline and child.pid not in seen:
                seen = module.descendants(os.getpid())
                time.sleep(0.05)
            assert child.pid in seen, "a live child was not in descendants()"
        finally:
            child.kill()
            child.wait(timeout=10)
        time.sleep(0.3)
        after = module.process_table()
        assert child.pid not in after, "a dead child still answered the snapshot"
        print("PASS AC-OSB1 live_child_seen=True dead_child_gone=True tree=%d"
              % len(seen))
    except (AssertionError, OSError, subprocess.SubprocessError) as exc:
        failed += 1
        print("FAIL AC-OSB1 :: %s" % exc)

    # ---------------- AC-OSB2 ----------------
    evidence_dir = None
    try:
        evidence_dir = tempfile.mkdtemp(prefix="osb-evidence-")
        prev = os.path.join(tempfile.mkdtemp(prefix="osb-prev-"),
                            "sandbox-start.json")
        with open(prev, "w", encoding="utf-8") as fh:
            json.dump({"host": "127.0.0.1", "ports": {}, "face_ports": {}}, fh)
        name = "sandbox-onclick-R3333.log"
        rc, out = run_launcher(["--check", "--prev-report", prev,
                                "--tree", os.path.join(evidence_dir, "tree.json"),
                                "--qa-log", name, "--qa-dir", evidence_dir])
        assert rc == 0, "real check run exited %d :: %s" % (
            rc, " | ".join(out.strip().splitlines()[-4:]))
        assert "sandbox up: hub=http://127.0.0.1:" in out, "no measured hub url"
        assert "preoccupied=none" in out, "a clean previous table was not read as none"
        match = re.search(r"descendants=(\d+) gone=(\d+)/(\d+) leftovers=(\S+)", out)
        assert match, "no descendant reading in the disposition"
        assert match.group(2) == match.group(3), "gone %s/%s" % (match.group(2), match.group(3))
        assert match.group(4) == "none", "leftovers=%s" % match.group(4)
        assert "clean=True" in out, "verdict did not read clean"
        assert "QA-LOG WROTE name=%s" % name in out, "the writer did not land the log"
        path = os.path.join(evidence_dir, name)
        assert os.path.isfile(path), "evidence file missing: %s" % path
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        assert "sandbox up: hub=http://127.0.0.1:" in body, "log lost the hub line"
        assert "VERDICT PASS" in body, "log lost the verdict line"
        assert "QA-LOG WROTE" not in body, "log quoted its own receipt"
        print("PASS AC-OSB2 rc=0 descendants=%s gone=%s/%s leftovers=none bytes=%d outside_repo=True"
              % (match.group(1), match.group(2), match.group(3), len(body)))
    except (AssertionError, OSError, subprocess.SubprocessError) as exc:
        failed += 1
        print("FAIL AC-OSB2 :: %s" % exc)

    # ---------------- AC-OSB3 ----------------
    try:
        hold_dir = tempfile.mkdtemp(prefix="osb-hold-")
        prev = os.path.join(tempfile.mkdtemp(prefix="osb-prev-"),
                            "sandbox-start.json")
        with open(prev, "w", encoding="utf-8") as fh:
            json.dump({"host": "127.0.0.1", "ports": {}, "face_ports": {}}, fh)
        rc, out = run_launcher(["--check", "--hold-secs", "25",
                                "--prev-report", prev,
                                "--tree", os.path.join(hold_dir, "tree.json"),
                                "--qa-log", "hold.log", "--qa-dir", hold_dir])
        assert rc == 2, "a surviving child still exited %d" % rc
        match = re.search(r"descendants=(\d+) gone=(\d+)/(\d+) leftovers=([^,]+,|none|\d+:\S+)", out)
        assert match, "no descendant reading in the hold run"
        gone, total = int(match.group(2)), int(match.group(3))
        assert gone < total, "the decoy was not counted as a leftover (gone=%d/%d)" % (gone, total)
        named = re.search(r"leftovers=(\d+):(\S+)", out)
        assert named, "the survivor was not named pid:exe"
        assert "clean=False" in out, "verdict claimed clean while a child survived"
        assert "reaped=" in out, "no reap line"
        assert "still=none" in out, "a survivor outlived the reap"
        print("PASS AC-OSB3 rc=2 gone=%d/%d survivor=%s:%s clean=False reaped=True"
              % (gone, total, named.group(1), named.group(2)))
    except (AssertionError, OSError, subprocess.SubprocessError) as exc:
        failed += 1
        print("FAIL AC-OSB3 :: %s" % exc)

    # ---------------- AC-OSB4 ----------------
    try:
        with open(MODULE, encoding="utf-8") as fh:
            source = fh.read()
        assert "load_qa_log().do_write(" in source, "the module does not call the writer"
        assert 'os.path.join(ROOT, "qa")' in source, "the default destination is not named"
        direct = direct_qa_writers(source)
        assert direct == [], "a second write path into qa/ exists: %r" % (direct,)
        mutant = source + (
            "\n\ndef _own_writer(name, data):\n"
            "    with open(os.path.join(ROOT, \"qa\", name), \"wb\") as fh:\n"
            "        fh.write(data)\n")
        bitten = direct_qa_writers(mutant)
        assert bitten, "the qa-writer scan stayed silent on a bypass writer"
        spec = importlib.util.spec_from_file_location("bd_qa_log_probe", WRITER)
        writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(writer)
        refused = None
        try:
            writer.do_write("bad-name.txt", b"x")
        except ValueError as exc:
            refused = str(exc)[:40]
        assert refused, "the writer accepted a name it must refuse"
        print("PASS AC-OSB4 shipped_writer=True direct_qa_writers=0 bypass_bitten=%d refused=%r"
              % (len(bitten), refused))
    except (AssertionError, OSError, AttributeError) as exc:
        failed += 1
        print("FAIL AC-OSB4 :: %s" % exc)

    # ---------------- AC-OSB5 ----------------
    try:
        with open(REGISTRY, encoding="utf-8") as fh:
            registry = fh.read()
        rows = registry_declarations(registry, "os-sandbox-open")
        assert rows == [TOTAL], (
            "registry declares %r for this suite, suite reports %d" % (rows, TOTAL))
        doubled = registry_declarations(
            ('("os-sandbox-open", "test_open_sandbox.py", %d),\n' % TOTAL) * 2
            + ('("os-sandbox-open", "copy.py", %d),\n' % (TOTAL + 1)),
            "os-sandbox-open")
        assert doubled == [TOTAL, TOTAL, TOTAL + 1], (
            "the declaration reader missed a duplicate or a stale count: %r" % (doubled,))
        print("PASS AC-OSB5 declared=%r duplicate_bitten=%d reported=%d"
              % (rows, len(doubled), TOTAL))
    except AssertionError as exc:
        failed += 1
        print("FAIL AC-OSB5 :: %s" % exc)

    # ---------------- AC-OSB6 ----------------
    try:
        # (a) the union of the two maps names each number once, first key wins
        table = module.previous_port_table({
            "ports": {"ws": "7000", "city": 7001, "gate": "junk"},
            "face_ports": {"lobby": 7000, "checkout": 7002}})
        assert table == {7000: "ws", 7001: "city", 7002: "checkout"}, (
            "port table read %r" % (table,))
        assert module.previous_port_table(None) == {}, "a missing report must read empty"

        # (b) a REAL listener on a recorded port is seen; closing it clears the reading
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(5)
        busy = sock.getsockname()[1]
        quiet = free_port()
        report = {"host": "127.0.0.1", "ports": {"ws": busy, "city": quiet}}
        live = module.occupied_ports(report)
        assert [pair[0] for pair in live] == [busy], "occupied_ports read %r" % (live,)
        sock.close()
        assert module.occupied_ports(report) == [], "a closed port still answered"

        # (c) the same table on disk makes the launcher refuse BEFORE any face starts
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(5)
        busy = sock.getsockname()[1]
        try:
            world = tempfile.mkdtemp(prefix="osb-prev-")
            prev = os.path.join(world, "sandbox-start.json")
            with open(prev, "w", encoding="utf-8") as fh:
                json.dump({"host": "127.0.0.1", "ports": {"ws": busy}}, fh)
            evidence = tempfile.mkdtemp(prefix="osb-refuse-")
            rc, out = run_launcher(["--check", "--prev-report", prev,
                                    "--qa-log", "refuse.log", "--qa-dir", evidence])
            assert rc == 2, "a live leftover port still exited %d" % rc
            assert ("preoccupied=%d:ws" % busy) in out, (
                "the occupied port was not named: %r" % out[:300])
            assert "REFUSED" in out, "no refusal line"
            assert "owner not identified" in out, "the boundary was not stated"
            assert "sandbox up:" not in out, "nine faces were started on top of a leftover"
            with open(os.path.join(evidence, "refuse.log"), encoding="utf-8") as fh:
                body = fh.read()
            assert "VERDICT FAIL" in body, "the disposition did not record the refusal"
        finally:
            sock.close()
        print("PASS AC-OSB6 table=%d busy_named=%d:ws quiet_seen=False refused_rc=2"
              " spawned=False" % (len(table), busy))
    except (AssertionError, OSError, subprocess.SubprocessError) as exc:
        failed += 1
        print("FAIL AC-OSB6 :: %s" % exc)

    # ---------------- AC-OSB7 ----------------
    hub = None
    sock = None
    child = None
    try:
        # (a) a live python child that owned the port last run -> ours:pid-alive
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(5)
        busy = sock.getsockname()[1]
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        time.sleep(0.4)
        alive_world = {"host": "127.0.0.1", "ports": {"ws": 1},
                       "face_ports": {"checkout": busy},
                       "pids": {"checkout": child.pid}}
        got = [tuple(row) for row in module.port_owners(alive_world, sockets={})]
        assert got == [(busy, "checkout", "ours", "pid-alive")], (
            "a live owner read %r" % (got,))

        # (b) the same port after that pid is gone -> foreign:pid-gone
        child.kill()
        child.wait(timeout=20)
        time.sleep(0.4)
        got = [tuple(row) for row in module.port_owners(alive_world, sockets={})]
        assert got == [(busy, "checkout", "foreign", "pid-gone")], (
            "a dead owner read %r" % (got,))

        # (c) a REAL shipped hub answering its own payload -> ours:hub-api
        sys.path.insert(0, os.path.join(HERE, "lobby"))
        import hub_page
        faces = hub_page.build_faces("127.0.0.1", 1, web_port=2)
        hub = hub_page.start_hub_http("127.0.0.1", 0, faces)
        hub_port = hub.server_address[1]
        time.sleep(0.4)
        hub_world = {"host": "127.0.0.1", "ports": {"hub": hub_port},
                     "hub_url": "http://127.0.0.1:%d/hub/" % hub_port}
        got = [tuple(row) for row in module.port_owners(hub_world, sockets={})]
        assert [(row[2], row[3]) for row in got] == [("ours", "hub-api")], (
            "a real hub read %r" % (got,))

        # (d) control: without the payload reader the same world is unknown
        real_payload = module.hub_payload
        module.hub_payload = lambda host, port, timeout=0.6: None
        try:
            got = [tuple(row) for row in module.port_owners(hub_world, sockets={})]
        finally:
            module.hub_payload = real_payload
        assert [(row[2], row[3]) for row in got] == [("unknown", "no-pid")], (
            "without its payload the hub port still read %r" % (got,))

        # (e) a closed world clears every reading
        hub.shutdown()
        hub.server_close()
        hub = None
        sock.close()
        sock = None
        time.sleep(0.3)
        assert module.port_owners(alive_world, sockets={}) == [], "a closed world still answered"
        assert module.port_owners(hub_world, sockets={}) == [], "a closed hub still answered"
        print("PASS AC-OSB7 alive=ours:pid-alive dead=foreign:pid-gone"
              " hub=ours:hub-api without_payload=unknown:no-pid closed=none")
    except (AssertionError, OSError, subprocess.SubprocessError, ImportError) as exc:
        failed += 1
        print("FAIL AC-OSB7 :: %s" % exc)
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            try:
                child.wait(timeout=10)
            except subprocess.SubprocessError:
                pass
        if hub is not None:
            try:
                hub.shutdown()
                hub.server_close()
            except OSError:
                pass
        if sock is not None:
            sock.close()

    # ---------------- AC-OSB8 ----------------
    hub = None
    child = None
    pre = module.listen_owners()
    print("AC-OSB8 table=%s" % ("present" if pre else "absent"))
    try:
        # (0) pre-reading: the OS table names this process and NOT a child
        mine = socket.socket()
        mine.bind(("127.0.0.1", 0))
        mine.listen(128)
        my_port = mine.getsockname()[1]
        if not pre:
            # A host without iphlpapi keeps the pre-R3339 law; the skip is named
            # and graded on that law, never a silent pass.
            world = {"host": "127.0.0.1", "ports": {"hub": my_port},
                     "face_ports": {"checkout": my_port},
                     "pids": {"checkout": os.getpid()}}
            got = [(r[2], r[3]) for r in module.port_owners(world)]
            assert got == [("ours", "pid-alive")], (
                "a host without the listen table read %r" % (got,))
            print("PASS AC-OSB8 table=absent law=fallback ours:pid-alive")
            raise _TableAbsent()
        inner = subprocess.Popen(
            [sys.executable, "-c",
             "import socket,time\n"
             "s=socket.socket();s.bind(('127.0.0.1',0));s.listen(5)\n"
             "print(s.getsockname()[1],flush=True);time.sleep(25)"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, creationflags=NO_WINDOW)
        child = inner
        inner_port = int(inner.stdout.readline().strip())
        table = None
        deadline = time.time() + 5.0
        while time.time() < deadline:
            table = module.listen_owners()
            if table.get(my_port) == os.getpid() and table.get(inner_port) == inner.pid:
                break
            time.sleep(0.1)
        assert table.get(my_port) == os.getpid(), (
            "this process own listener read %r" % (table.get(my_port),))
        assert table.get(inner_port) == inner.pid, (
            "a child listener read %r for pid %d"
            % (table.get(inner_port), inner.pid))
        assert module.listen_owners().get(free_port()) is None, (
            "a closed port appeared in the listen table")
        child_world = {"host": "127.0.0.1", "ports": {"hub": inner_port},
                       "face_ports": {"checkout": inner_port},
                       "pids": {"checkout": inner.pid}}
        got = [tuple(row) for row in module.port_owners(child_world)]
        assert got == [(inner_port, "hub", "ours", "sock-pid")], (
            "a child own socket read %r" % (got,))
        inner.kill()
        inner.wait(timeout=20)
        child = None

        # (a) socket owned by THIS process, report says so -> ours:sock-pid
        mine_world = {"host": "127.0.0.1", "ports": {"hub": my_port},
                      "face_ports": {"checkout": my_port},
                      "pids": {"checkout": os.getpid()}}
        got = [tuple(row) for row in module.port_owners(mine_world)]
        assert got == [(my_port, "hub", "ours", "sock-pid")], (
            "a matching owner read %r" % (got,))

        # (b) the SAME socket recorded against another live python child ->
        #     foreign:sock-pid-other (the shape that used to read pid-alive)
        other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        child = other
        time.sleep(0.4)
        other_world = {"host": "127.0.0.1", "ports": {"hub": my_port},
                       "face_ports": {"checkout": my_port},
                       "pids": {"checkout": other.pid}}
        got = [tuple(row) for row in module.port_owners(other_world)]
        assert got == [(my_port, "hub", "foreign", "sock-pid-other")], (
            "a mismatched owner read %r" % (got,))
        other.kill()
        other.wait(timeout=20)
        child = None

        # (c) a REAL shipped hub on a recorded pid -> ours:sock-pid; the same
        #     hub against an unrecorded pid -> foreign:sock-pid-unrecorded
        sys.path.insert(0, os.path.join(HERE, "lobby"))
        import hub_page
        faces = hub_page.build_faces("127.0.0.1", 1, web_port=2)
        hub = hub_page.start_hub_http("127.0.0.1", 0, faces)
        hub_port = hub.server_address[1]
        time.sleep(0.4)
        recorded_hub = {"host": "127.0.0.1", "ports": {"hub": hub_port},
                        "hub_url": "http://127.0.0.1:%d/hub/" % hub_port,
                        "pids": {"checkout": os.getpid()}}
        got = [tuple(row) for row in module.port_owners(recorded_hub)]
        assert [(row[2], row[3]) for row in got] == [("ours", "sock-pid")], (
            "a hub owned by a recorded pid read %r" % (got,))
        foreign_hub = dict(recorded_hub)
        foreign_pid = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(25)"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        child = foreign_pid
        time.sleep(0.4)
        foreign_hub["pids"] = {"checkout": foreign_pid.pid}
        got = [tuple(row) for row in module.port_owners(foreign_hub)]
        assert [(row[2], row[3]) for row in got] == \
            [("foreign", "sock-pid-unrecorded")], (
            "a hub owned by an unrecorded pid read %r" % (got,))
        foreign_pid.kill()
        foreign_pid.wait(timeout=20)
        child = None

        # (d) a refused table falls back to the older bases, never to a guess
        real = module.listen_owners
        module.listen_owners = lambda: {}
        try:
            got = [tuple(row) for row in module.port_owners(mine_world)]
        finally:
            module.listen_owners = real
        assert [(row[2], row[3]) for row in got] == [("ours", "pid-alive")], (
            "a refused table read %r" % (got,))

        mine.close()
        mine = None
        print("PASS AC-OSB8 own=ours:sock-pid child_own=ours:sock-pid"
              " mismatch=foreign:sock-pid-other hub=ours:sock-pid"
              " unrecorded=foreign:sock-pid-unrecorded refused=pid-alive")
    except _TableAbsent:
        pass
    except (AssertionError, OSError, subprocess.SubprocessError, ImportError) as exc:
        failed += 1
        print("FAIL AC-OSB8 :: %s" % exc)
    finally:
        for proc in (child,):
            if proc is not None and proc.poll() is None:
                proc.kill()
                try:
                    proc.wait(timeout=10)
                except subprocess.SubprocessError:
                    pass
        if hub is not None:
            try:
                hub.shutdown()
                hub.server_close()
            except OSError:
                pass
        for name in ("mine",):
            item = locals().get(name)
            if item is not None:
                try:
                    item.close()
                except OSError:
                    pass

    # ---------------- AC-OSB9 ----------------
    try:
        # Five injected readings - no OS permission needed. The question is
        # whether a number that came back as SOMEBODY ELSE is called a leftover
        # (and then killed) or named as reused.
        mine = (4242, "python.exe", 111)

        left, reused, gone = module.leftovers([mine], {4242: (1, "python.exe")},
                                              {4242: 111})
        assert (left, reused, gone) == ([4242], [], []), (
            "the same process read %r" % ((left, reused, gone),))

        left, reused, gone = module.leftovers([mine], {4242: (1, "ssh.exe")},
                                              {4242: 999})
        assert left == [], "a pid whose image changed was called a leftover"
        assert reused and reused[0][3] == "image", (
            "an image change read %r" % (reused,))

        left, reused, gone = module.leftovers([mine], {4242: (1, "python.exe")},
                                              {4242: 999})
        assert left == [], (
            "a recycled pid with a new creation time was called a leftover")
        assert reused and reused[0][3] == "creation-time", (
            "a creation-time change read %r" % (reused,))

        left, reused, gone = module.leftovers([mine], {}, {})
        assert (left, reused, gone) == ([], [], [4242]), (
            "an absent pid read %r" % ((left, reused, gone),))

        # Boundary: a host whose creation time cannot be read keeps the image
        # test and says so, instead of inventing a decision.
        left, reused, gone = module.leftovers([mine], {4242: (1, "python.exe")},
                                              None)
        assert left == [4242] and reused == [], (
            "a host without creation time read %r" % ((left, reused, gone),))

        # Load-bearing: the SHIPPED form of R3339 was "pid in table".
        old = [pid for pid, _e, _b in [mine] if pid in {4242: (1, "ssh.exe")}]
        assert old == [4242], "the decoy does not reproduce the old shape"
        print("PASS AC-OSB9 same=left image=reused birth=reused absent=gone"
              " notime=left old_form_kills=True")
    except (AssertionError, AttributeError) as exc:
        failed += 1
        print("FAIL AC-OSB9 :: %s" % exc)

    # ---------------- AC-OSB10 ----------------
    try:
        # The 11-22 orphan: a face that outlived its launcher and holds no port
        # was invisible to every later run, because the teardown reading only
        # ever saw ITS OWN subtree. Real processes here - a real python child is
        # seeded into a record, so the census must read the OS table, not a
        # number typed into the test.
        orphan_dir = tempfile.mkdtemp(prefix="osb-orphan-")
        prev = os.path.join(tempfile.mkdtemp(prefix="osb-prev-"),
                            "sandbox-start.json")
        with open(prev, "w", encoding="utf-8") as fh:
            json.dump({"host": "127.0.0.1", "ports": {}, "face_ports": {}}, fh)
        tree = os.path.join(orphan_dir, "tree.json")

        child = subprocess.Popen([sys.executable, "-c",
                                  "import time; time.sleep(60)"],
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 creationflags=NO_WINDOW)
        try:
            time.sleep(0.4)
            birth = module.process_start(child.pid)
            assert module.write_tree(tree, [(child.pid, "python.exe", birth),
                                            (999999, "python.exe", 1)]), \
                "the tree record could not be written"

            # (a) a live orphan from an earlier run refuses the run by name,
            #     before nine new processes could bury it.
            rc, out = run_launcher(["--check", "--prev-report", prev,
                                    "--tree", tree])
            assert rc == 2, "a live orphan still started faces (rc=%d)" % rc
            assert "preoccupied=none" in out, \
                "the refusal did not come from the orphan census"
            named = re.search(r"orphans=(\d+):(\S+)", out)
            assert named, "the orphan was not named pid:exe :: %s" % out[-300:]
            assert named.group(1) == str(child.pid), (
                "the wrong pid was named (%s vs %s)" % (named.group(1), child.pid))
            assert "sandbox up:" not in out, "faces were started over an orphan"
            assert os.path.isfile(tree), "the record of an unfinished run was deleted"

            # (b) a RECYCLED number is reused, not an orphan: the same pid with a
            #     moved creation time must not make this run refuse a stranger.
            if birth is not None:
                module.write_tree(tree, [(child.pid, "python.exe", birth + 1)])
                rc, out = run_launcher(["--check", "--prev-report", prev,
                                        "--tree", tree])
                reused = re.search(r"reused=(\d+)", out)
                assert rc == 0, "a recycled pid refused the run (rc=%d)" % rc
                assert "orphans=none" in out, "a recycled pid read as an orphan"
                assert reused and reused.group(1) == "1", \
                    "the recycled pid was not named reused: %r" % (reused,)
        finally:
            try:
                child.kill()
                child.wait(timeout=10)
            except (OSError, subprocess.SubprocessError):
                pass

        # (c) the same record once the process is gone: clean, and the record is
        #     cleared instead of refusing forever.
        module.write_tree(tree, [(child.pid, "python.exe", birth)])
        deadline = time.time() + 10.0
        while time.time() < deadline and child.pid in module.process_table():
            time.sleep(0.25)
        rc, out = run_launcher(["--check", "--prev-report", prev,
                                "--tree", tree])
        assert rc == 0, "a stale record still refused the run (rc=%d)" % rc
        assert "orphans=none" in out, "a dead recorded pid read as an orphan"
        assert "sandbox up:" in out, "the run did not proceed past a stale record"
        assert not os.path.isfile(tree), "a stale record was left on disk"
        print("PASS AC-OSB10 live_refused=%s recycled=reused stale=cleared "
              "faces_over_orphan=0" % child.pid)
    except (AssertionError, OSError, AttributeError,
            subprocess.SubprocessError) as exc:
        failed += 1
        print("FAIL AC-OSB10 :: %s" % exc)

    if failed:
        print("SUITE FAIL %d/%d" % (TOTAL - failed, TOTAL))
        return 1
    print("SUITE PASS %d/%d" % (TOTAL, TOTAL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
