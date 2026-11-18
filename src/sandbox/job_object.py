"""Kill-on-close job objects: children die with the launcher, not after it.

R2937 answers the orphan R2934 actually measured (a lobby server born at
00:09:33 with a GONE parent still holding port 63097 for hours). Python's
``finally`` cannot answer it: a launcher killed hard never runs it. The kernel
can, because a job object created with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
terminates every process still inside it the moment the last handle to that
job closes - and a hard-killed parent closes its handles.

This module is a LEAF on purpose (stdlib ``ctypes`` and ``sys`` only), so a
suite or a hook can import it without dragging the sandbox in. Where job
objects do not exist it reports ``available() is False`` and the caller must
publish that in its own report instead of pretending the guarantee exists.
"""

import ctypes
import sys

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9

PROCESS_TERMINATE = 0x0001
PROCESS_SET_QUOTA = 0x0100
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class JobError(RuntimeError):
    """A job object could not be created, armed, or joined."""


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("ReadOperationCount", "WriteOperationCount",
                 "OtherOperationCount", "ReadTransferCount",
                 "WriteTransferCount", "OtherTransferCount")]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _kernel32():
    """The kernel32 entry points this module needs, or None off Windows."""
    if sys.platform != "win32":
        return None
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except (OSError, AttributeError):
        return None
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.SetInformationJobObject.restype = ctypes.c_int
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.AssignProcessToJobObject.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int,
                                     ctypes.c_uint32]
    kernel32.IsProcessInJob.restype = ctypes.c_int
    kernel32.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.POINTER(ctypes.c_int)]
    kernel32.CloseHandle.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    return kernel32


_K32 = _kernel32()


def available():
    """True only where a kill-on-close job object can really be created."""
    return _K32 is not None


def create(name="bigdomain-sandbox"):
    """A job armed to kill everything inside it when its last handle closes."""
    if _K32 is None:
        raise JobError("E_JOB_UNSUPPORTED")
    handle = _K32.CreateJobObjectW(None, name)
    if not handle:
        raise JobError("E_JOB_CREATE rc=%d" % ctypes.get_last_error())
    info = _ExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not _K32.SetInformationJobObject(
            handle, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(info), ctypes.sizeof(info)):
        code = ctypes.get_last_error()
        _K32.CloseHandle(handle)
        raise JobError("E_JOB_LIMIT rc=%d" % code)
    return handle


def assign(handle, pid):
    """Put one live process inside the job, or raise with its own name."""
    if _K32 is None or not handle:
        raise JobError("E_JOB_UNSUPPORTED")
    access = PROCESS_TERMINATE | PROCESS_SET_QUOTA
    proc = _K32.OpenProcess(access, 0, int(pid))
    if not proc:
        raise JobError("E_JOB_OPEN pid=%d rc=%d"
                       % (int(pid), ctypes.get_last_error()))
    try:
        if not _K32.AssignProcessToJobObject(handle, proc):
            raise JobError("E_JOB_ASSIGN pid=%d rc=%d"
                           % (int(pid), ctypes.get_last_error()))
    finally:
        _K32.CloseHandle(proc)


def close(handle):
    """Drop the handle; every process still in the job is terminated."""
    if _K32 is not None and handle:
        _K32.CloseHandle(handle)


def is_in_job(handle, pid):
    """Ask the KERNEL whether that process is inside this job right now.

    Added in R2947 for the grandchild question: a child of a job member joins
    the same job by inheritance, and that inheritance is a property no report
    of ours can assert from the outside. IsProcessInJob answers it directly,
    which is stronger evidence than "the port went quiet after a kill" - the
    latter correlates, this one names membership. Returns False when the
    question cannot be asked rather than guessing.
    """
    if _K32 is None or not handle:
        return False
    proc = _K32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid))
    if not proc:
        return False
    try:
        inside = ctypes.c_int(0)
        if not _K32.IsProcessInJob(proc, handle, ctypes.byref(inside)):
            return False
        return bool(inside.value)
    finally:
        _K32.CloseHandle(proc)
