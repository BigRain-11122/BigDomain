"""Suite for the one-click sandbox launcher (open_sandbox.py).

Seven criteria. AC-OSB1..AC-OSB3 were pre-registered in src/os/backlog.md at
R3333 BEFORE this module existed (the board head asked for the disposition to be
scriptized instead of hand-copied into qa/, and for a teardown reading that can
say a child really is gone); AC-OSB6 was pre-registered at R3334 (the board head
asked for a pre-launch probe of the previous run's port table); AC-OSB7 was
pre-registered at R3335 (the board head asked whether an answering port can be
attributed to US without guessing):

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
           open()/write path into qa/.
  AC-OSB5  the battery registry carries this suite exactly once and declares the
           same criterion count this file reports.
  AC-OSB6  the previous run's port table is read before it is deleted: the
           union of ports/face_ports names each number once, a REAL listener on
           a recorded port is seen and cleared when it closes, and the same
           table on disk makes the launcher refuse (rc=2, port named, boundary
           stated, no face started). The two real runs above point --prev-report
           at a private empty table so ambient machine state cannot red them.
  AC-OSB7  an answering port is ATTRIBUTED without guessing: a port whose face
           pid is still alive reads ours:pid-alive, the same port after that pid
           is gone reads foreign:pid-gone, and a REAL shipped hub answering its
           own payload reads ours:hub-api - with a control that disables the
           payload reader and reads unknown:no-pid, so the identity check is
           load-bearing rather than decorative.

Cost measured at R3333: the two sandbox runs are about 3.6s each (the faces come
up and are torn down for real); the collector arm and the socket arms are under
a second, and the refusal arm returns before any face is spawned. AC-OSB7 adds
one sleeping child and one in-process hub (well under a second).
"""

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
TOTAL = 7


def load_module():
    spec = importlib.util.spec_from_file_location("bd_open_sandbox", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        assert source.count("do_write(") == 1, "more than one write call site"
        assert 'os.path.join(ROOT, "qa")' in source, "the default destination is not named"
        direct = [line for line in source.splitlines()
                  if re.search(r"open\([^)]*qa", line)]
        assert not direct, "a second write path into qa/ exists: %r" % direct
        spec = importlib.util.spec_from_file_location("bd_qa_log_probe", WRITER)
        writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(writer)
        refused = None
        try:
            writer.do_write("bad-name.txt", b"x")
        except ValueError as exc:
            refused = str(exc)[:40]
        assert refused, "the writer accepted a name it must refuse"
        print("PASS AC-OSB4 one_writer=True direct_qa_writes=0 refused=%r" % refused)
    except (AssertionError, OSError, AttributeError) as exc:
        failed += 1
        print("FAIL AC-OSB4 :: %s" % exc)

    # ---------------- AC-OSB5 ----------------
    try:
        with open(REGISTRY, encoding="utf-8") as fh:
            registry = fh.read()
        rows = re.findall(r'\("os-sandbox-open",\s*[^,]+,\s*(\d+)\)', registry)
        assert len(rows) == 1, "registry carries %d rows for this suite" % len(rows)
        assert int(rows[0]) == TOTAL, "registry declares %s criteria, suite reports %d" % (
            rows[0], TOTAL)
        print("PASS AC-OSB5 rows=1 declared=%s reported=%d" % (rows[0], TOTAL))
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
        got = [tuple(row) for row in module.port_owners(alive_world)]
        assert got == [(busy, "checkout", "ours", "pid-alive")], (
            "a live owner read %r" % (got,))

        # (b) the same port after that pid is gone -> foreign:pid-gone
        child.kill()
        child.wait(timeout=20)
        time.sleep(0.4)
        got = [tuple(row) for row in module.port_owners(alive_world)]
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
        got = [tuple(row) for row in module.port_owners(hub_world)]
        assert [(row[2], row[3]) for row in got] == [("ours", "hub-api")], (
            "a real hub read %r" % (got,))

        # (d) control: without the payload reader the same world is unknown
        real_payload = module.hub_payload
        module.hub_payload = lambda host, port, timeout=0.6: None
        try:
            got = [tuple(row) for row in module.port_owners(hub_world)]
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
        assert module.port_owners(alive_world) == [], "a closed world still answered"
        assert module.port_owners(hub_world) == [], "a closed hub still answered"
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

    if failed:
        print("SUITE FAIL %d/%d" % (TOTAL - failed, TOTAL))
        return 1
    print("SUITE PASS %d/%d" % (TOTAL, TOTAL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
