"""A kernel-named claim on the sandbox launcher - discovery that is not a file.

R2939 taught the machine to refuse a second door, but it did so with a RECORD
FILE, and a file can be deleted: remove
``%LOCALAPPDATA%\\BigDomain\\sandbox-launcher.json`` while a launcher serves and
the next one starts beside it with nothing to refuse.

This module adds the claim the kernel owns. A named mutex exists while some
process holds a handle to it and DISAPPEARS when the last handle closes - and
the kernel closes the handles of a process that dies, however it dies. So:

1. ``acquire()`` creates the object; ``ERROR_ALREADY_EXISTS`` means somebody
   else is serving right now. Nothing can delete it from the filesystem.
2. A dead launcher cannot leave a stale lock behind - the object is gone with
   it, which the suite proves by killing a child holding it.
3. The record file stays useful as the DETAIL face (pid, ports, hub url), but
   it is no longer the gate.

The default name is per user SESSION (``Local\\``): a mutex under ``Global\\``
needs SeCreateGlobalPrivilege, and the record it accompanies is already a
per-user record in LOCALAPPDATA. That limit is named rather than faked.

Stdlib only, no shell, no network, no writes.
"""

import ctypes
import hashlib
import os
import sys

NAME = "Local\\BigDomainSandboxLauncher-v1"
ERROR_ALREADY_EXISTS = 183
SYNCHRONIZE = 0x00100000
REFUSED = "E_LAUNCHER_ALREADY_RUNNING"


def available():
    """Kernel named objects are a Windows construction, not a portable one."""
    return os.name == "nt"


def _kernel32():
    return ctypes.WinDLL("kernel32", use_last_error=True)


def name_for(path):
    """The mutex a given record path belongs to.

    Machine use resolves the default record path, so there is exactly ONE
    machine-wide name; a suite that passes a private ``--registry`` therefore
    gets a private, uncontended name without any test-only branch.
    """
    digest = hashlib.sha1(
        os.path.abspath(str(path)).lower().encode("utf-8")).hexdigest()
    return NAME + "-" + digest[:16]


def acquire(name=None):
    """Take the claim, or report the live holder.

    Returns a dict ``{held, already, handle, name, available, source}``.
    ``held`` False with ``already`` True means another process holds it RIGHT
    NOW; ``handle`` must be kept alive for the lifetime of the process that
    serves, and closed with :func:`release`.
    """
    name = name or NAME
    if not available():
        return {"held": True, "already": False, "handle": None, "name": name,
                "available": False, "source": "unavailable-on-this-platform"}
    kernel32 = _kernel32()
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                      ctypes.c_wchar_p]
    handle = kernel32.CreateMutexW(None, 0, name)
    error = ctypes.get_last_error()
    if not handle:
        return {"held": False, "already": False, "handle": None, "name": name,
                "available": True, "source": "create-failed",
                "error": "E_MUTEX_CREATE_FAILED"}
    if error == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        return {"held": False, "already": True, "handle": None, "name": name,
                "available": True, "source": "held-by-another-process"}
    return {"held": True, "already": False, "handle": handle, "name": name,
            "available": True, "source": "claimed"}


def release(handle):
    """Drop our handle. The object survives only while somebody else holds it."""
    if not handle or not available():
        return False
    kernel32 = _kernel32()
    kernel32.CloseHandle.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    return bool(kernel32.CloseHandle(ctypes.c_void_p(handle)))


def exists(name=None):
    """Is somebody holding that claim right now?"""
    name = name or NAME
    if not available():
        return False
    kernel32 = _kernel32()
    kernel32.OpenMutexW.restype = ctypes.c_void_p
    kernel32.OpenMutexW.argtypes = [ctypes.c_ulong, ctypes.c_int,
                                    ctypes.c_wchar_p]
    handle = kernel32.OpenMutexW(SYNCHRONIZE, 0, name)
    if not handle:
        return False
    kernel32.CloseHandle(ctypes.c_void_p(handle))
    return True
