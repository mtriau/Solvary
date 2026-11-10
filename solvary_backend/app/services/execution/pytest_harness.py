"""
pytest-style judging (`judge_mode == "pytest"`).

Interview screens of the "progressive parts" kind hand the candidate a
module stub plus a *provided* pytest suite per part: you implement the
module, run the suite, and read the failing test names. This harness
reproduces that inside the sandbox without pytest being installed there.

How a pytest problem is stored:
  - `Problem.harness = {"module": "todo_tracker", "files": {"test_x_p1.py": src, …}}`
  - one TestCase per test function; `stdin` is the test id
    (`test_x_p1.py::test_name`), `expected_stdout` is "PASS\n"; every case
    is a sample (the candidate may read the suite, and failures must show
    their assertion text)

How a submission runs (PistonExecutor):
  ONE sandbox execution with these files: `main.py` (RUNNER), `pytest.py`
  (SHIM: the slice of the pytest API the suites use), `solvary_prelude.py`
  (python_prelude.py: stdlib names available without an import),
  `<module>.py` (the candidate's code) and the suite files. stdin lists the test ids to run.
  The runner prints one record per test; `parse_output` turns the records
  back into per-case results, which the executor emits as ordinary
  `case_result` events (PASS → stdout "PASS", so the plain exact checker
  decides; FAIL → stdout "FAIL\n<traceback>"; TLE → status tle).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.services.execution import python_prelude
from app.services.execution.base import ExecCase, ExecJob

RECORD_MARK = "@@SOLVARY_TEST "
RECORD_END = "@@SOLVARY_END"
COMPILE_ERROR_MARK = "@@SOLVARY_COMPILE_ERROR"
DEFAULT_PER_TEST_S = 5.0
MAX_DETAIL_CHARS = 4000

# ── pytest.py: the subset of pytest the provided suites rely on ────────

SHIM = r'''
"""Minimal stand-in for the pytest API (pytest itself is not in the sandbox)."""
import math
import re as _re


class Skipped(Exception):
    pass


class _RaisesContext:
    def __init__(self, expected, match=None):
        self.expected = expected
        self.match = match
        self.value = None
        self.type = None
        self.tb = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            names = self.expected
            if isinstance(names, tuple):
                names = ", ".join(e.__name__ for e in names)
            else:
                names = names.__name__
            raise AssertionError(f"DID NOT RAISE {names}")
        if not issubclass(exc_type, self.expected):
            return False
        if self.match is not None and not _re.search(self.match, str(exc)):
            raise AssertionError(
                f"Regex pattern did not match.\n Regex: {self.match!r}\n Input: {str(exc)!r}"
            )
        self.value = exc
        self.type = exc_type
        self.tb = tb
        return True


def raises(expected, *args, match=None, **kwargs):
    if args:
        func, rest = args[0], args[1:]
        with _RaisesContext(expected, match) as ctx:
            func(*rest, **kwargs)
        return ctx
    return _RaisesContext(expected, match)


class approx:
    def __init__(self, expected, rel=None, abs=None, nan_ok=False):
        self.expected = expected
        self.rel = 1e-6 if rel is None else rel
        self.abs = 1e-12 if abs is None else abs
        self.nan_ok = nan_ok

    def _close(self, a, b):
        if isinstance(a, bool) or isinstance(b, bool):
            return a == b
        try:
            a = float(a)
            b = float(b)
        except (TypeError, ValueError):
            return a == b
        if math.isnan(a) or math.isnan(b):
            return self.nan_ok and math.isnan(a) and math.isnan(b)
        return math.isclose(a, b, rel_tol=self.rel, abs_tol=self.abs)

    def __eq__(self, actual):
        exp = self.expected
        if isinstance(exp, dict):
            return (
                isinstance(actual, dict)
                and exp.keys() == actual.keys()
                and all(self._close(actual[k], exp[k]) for k in exp)
            )
        if isinstance(exp, (list, tuple, set, frozenset)):
            try:
                actual = list(actual)
            except TypeError:
                return False
            exp = list(exp)
            return len(actual) == len(exp) and all(self._close(a, e) for a, e in zip(actual, exp))
        return self._close(actual, exp)

    def __ne__(self, actual):
        return not self.__eq__(actual)

    def __repr__(self):
        return f"approx({self.expected!r})"


def fail(msg="", pytrace=True):
    raise AssertionError(msg)


def skip(msg=""):
    raise Skipped(msg)


class _Mark:
    def parametrize(self, argnames, argvalues, **kwargs):
        if isinstance(argnames, str):
            names = [n.strip() for n in argnames.split(",")]
        else:
            names = list(argnames)

        def deco(func):
            params = getattr(func, "_solvary_params", [])
            params.append((names, list(argvalues)))
            func._solvary_params = params
            return func

        return deco

    def __getattr__(self, name):
        def deco(*args, **kwargs):
            if len(args) == 1 and callable(args[0]) and not kwargs:
                return args[0]
            return lambda func: func

        return deco


mark = _Mark()


def fixture(func=None, **kwargs):
    def deco(f):
        f._solvary_fixture = True
        return f

    return deco(func) if func is not None else deco


def param(*values, id=None, marks=()):
    return tuple(values) if len(values) != 1 else values[0]
'''

# ── main.py: collects, runs and reports the requested tests ────────────

RUNNER = r'''
import importlib.util
import inspect
import io
import json
import os
import signal
import sys
import time
import traceback

MODULE = __MODULE__
TEST_FILES = __TEST_FILES__
PER_TEST_S = __PER_TEST_S__
ALWAYS_CAPTURE = __ALWAYS_CAPTURE__
MARK = "@@SOLVARY_TEST "
END = "@@SOLVARY_END"
COMPILE_ERROR = "@@SOLVARY_COMPILE_ERROR"
MAX_DETAIL = __MAX_DETAIL__
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.__stdout__


class _TestTimeout(BaseException):
    pass


def _emit(test_id, status, ms, detail=""):
    detail = detail.strip("\n")
    if len(detail) > MAX_DETAIL:
        detail = detail[:MAX_DETAIL] + "\n… (truncated)"
    OUT.write(f"{MARK}{test_id}\n{status} {ms}\n")
    if detail:
        OUT.write(detail + "\n")
    OUT.write(END + "\n")
    OUT.flush()


def _format_exc(exc):
    """Traceback limited to the suite and the candidate's module, with bare file names."""
    keep = []
    for f in traceback.extract_tb(exc.__traceback__):
        base = os.path.basename(f.filename)
        if base in ("main.py", "pytest.py", "solvary_prelude.py"):
            continue
        keep.append(traceback.FrameSummary(base, f.lineno, f.name, line=f.line))
    lines = ["Traceback (most recent call last):\n"] if keep else []
    lines += traceback.format_list(keep)
    lines += traceback.format_exception_only(type(exc), exc)
    return "".join(lines)


def _load(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _collect(mod, filename):
    """[(test_id, callable)] in definition order; Test* classes get an instance per test."""
    found = []
    for name, obj in vars(mod).items():
        if name.startswith("test") and inspect.isfunction(obj):
            found.append((obj.__code__.co_firstlineno, f"{filename}::{name}", obj, None))
        elif name.startswith("Test") and inspect.isclass(obj) and obj.__module__ == mod.__name__:
            for mname, meth in vars(obj).items():
                if mname.startswith("test") and inspect.isfunction(meth):
                    found.append(
                        (meth.__code__.co_firstlineno, f"{filename}::{name}::{mname}", meth, obj)
                    )
    found.sort(key=lambda t: t[0])
    return [(tid, fn, cls) for _, tid, fn, cls in found]


def _resolve_args(mod, fn, finalizers):
    args = {}
    for pname in inspect.signature(fn).parameters:
        if pname == "self":
            continue
        fx = getattr(mod, pname, None)
        if fx is None or not getattr(fx, "_solvary_fixture", False):
            continue
        value = fx()
        if inspect.isgenerator(value):
            gen = value
            value = next(gen)
            finalizers.append(gen)
        args[pname] = value
    return args


def _alarm(signum, frame):
    raise _TestTimeout()


def _run_one(mod, fn, cls):
    """-> (status, detail)"""
    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = buf
    finalizers = []
    status, detail = "PASS", ""
    has_alarm = hasattr(signal, "SIGALRM")
    try:
        if has_alarm:
            signal.signal(signal.SIGALRM, _alarm)
            signal.setitimer(signal.ITIMER_REAL, PER_TEST_S)
        try:
            kwargs = _resolve_args(mod, fn, finalizers)
            if cls is not None:
                fn(cls(), **kwargs)
            else:
                fn(**kwargs)
        finally:
            if has_alarm:
                signal.setitimer(signal.ITIMER_REAL, 0)
            for gen in finalizers:
                try:
                    next(gen)
                except StopIteration:
                    pass
                except Exception:
                    pass
    except _TestTimeout:
        status, detail = "TLE", f"test exceeded {PER_TEST_S:g}s"
    except Exception as exc:  # pytest reports errors as failures too
        if type(exc).__name__ == "Skipped":
            status, detail = "PASS", f"skipped: {exc}"
        else:
            status, detail = "FAIL", _format_exc(exc)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    captured = buf.getvalue()
    if captured.strip() and (ALWAYS_CAPTURE or status != "PASS"):
        detail += "\n--- captured output ---\n" + captured[-1500:]
    return status, detail


def main():
    sys.path.insert(0, HERE)
    sys.setrecursionlimit(1000)
    import solvary_prelude

    solvary_prelude.install()
    requested = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]

    # Syntax errors in the candidate's module are a compile error, not N failures
    try:
        with open(os.path.join(HERE, MODULE + ".py"), encoding="utf-8") as f:
            compile(f.read(), MODULE + ".py", "exec")
    except SyntaxError:
        OUT.write(COMPILE_ERROR + "\n" + traceback.format_exc(limit=0) + "\n")
        return

    tests = {}
    import_errors = {}
    for filename in TEST_FILES:
        try:
            mod = _load(os.path.join(HERE, filename))
        except BaseException as exc:
            import_errors[filename] = _format_exc(exc) if isinstance(exc, Exception) else repr(exc)
            continue
        for tid, fn, cls in _collect(mod, filename):
            tests[tid] = (mod, fn, cls)

    if not requested:
        requested = list(tests)

    for tid in requested:
        filename = tid.split("::", 1)[0]
        if filename in import_errors:
            _emit(tid, "FAIL", 0, "could not import the test module:\n" + import_errors[filename])
            continue
        entry = tests.get(tid)
        if entry is None:
            _emit(tid, "FAIL", 0, "test not found in the provided suite")
            continue
        start = time.perf_counter()
        status, detail = _run_one(*entry)
        ms = int((time.perf_counter() - start) * 1000)
        _emit(tid, status, ms, detail)


if __name__ == "__main__":
    main()
'''


# ── executor-side helpers ──────────────────────────────────────────────


@dataclass
class HarnessRecord:
    status: str  # PASS | FAIL | TLE
    runtime_ms: int
    detail: str


@dataclass
class HarnessOutput:
    compile_error: str | None
    records: dict[str, HarnessRecord]


def harness_module(harness: dict) -> str:
    return str(harness.get("module") or "main")


def build_files(
    job: ExecJob, per_test_s: float | None = None, *, always_capture: bool = False
) -> list[dict]:
    """The sandbox file set: runner first (Piston runs files[0]). With
    `always_capture` the runner reports printed output for passing tests too
    (ad-hoc Run); judging only shows it on failures."""
    harness = job.harness or {}
    module = harness_module(harness)
    files: dict[str, str] = dict(harness.get("files") or {})
    runner = (
        RUNNER.replace("__MODULE__", json.dumps(module))
        .replace("__TEST_FILES__", json.dumps(list(files)))
        .replace("__PER_TEST_S__", repr(float(per_test_s or DEFAULT_PER_TEST_S)))
        .replace("__MAX_DETAIL__", str(MAX_DETAIL_CHARS))
        .replace("__ALWAYS_CAPTURE__", repr(bool(always_capture)))
    )
    out = [
        {"name": "main.py", "content": runner},
        {"name": "pytest.py", "content": SHIM},
        python_prelude.prelude_file(),
        {"name": f"{module}.py", "content": job.code},
    ]
    out += [{"name": name, "content": src} for name, src in files.items()]
    return out


def stdin_for(cases: list[ExecCase]) -> str:
    return "".join(c.stdin.strip() + "\n" for c in cases)


def requested_ids(stdin: str) -> list[str]:
    """Test ids typed into the Run box, one per line (blank → the whole suite)."""
    return [line.strip() for line in stdin.splitlines() if line.strip()]


def all_test_ids(harness: dict) -> list[str]:
    ids: list[str] = []
    for name, src in (harness.get("files") or {}).items():
        try:
            ids += collect_test_ids(name, src)
        except SyntaxError:
            continue
    return ids


def format_run_output(requested: list[str], parsed: HarnessOutput) -> str:
    """Ad-hoc Run over a provided suite: a pytest-like transcript — one line per
    test, then that test's traceback / printed output, then a summary line."""
    lines: list[str] = []
    passed = failed = 0
    for tid in requested:
        record = parsed.records.get(tid)
        if record is None:
            failed += 1
            lines.append(f"?     {tid}  (no result: the run ended before this test reported)")
            continue
        if record.status == "PASS":
            passed += 1
        else:
            failed += 1
        lines.append(f"{record.status:<5} {tid}  ({record.runtime_ms} ms)")
        if record.detail:
            lines.append("    " + record.detail.replace("\n", "\n    "))
            lines.append("")
    lines.append(f"{passed} passed, {failed} failed")
    return "\n".join(lines).rstrip("\n") + "\n"


def parse_output(stdout: str) -> HarnessOutput:
    """Split the runner's stdout back into per-test records (tolerates a truncated tail)."""
    if COMPILE_ERROR_MARK in stdout:
        _, _, rest = stdout.partition(COMPILE_ERROR_MARK)
        return HarnessOutput(compile_error=rest.strip() or "SyntaxError", records={})
    records: dict[str, HarnessRecord] = {}
    for chunk in stdout.split(RECORD_MARK)[1:]:
        body, sep, _ = chunk.partition(RECORD_END)
        if not sep:
            continue  # the run died mid-record: leave it unreported
        lines = body.split("\n")
        if len(lines) < 2:
            continue
        test_id = lines[0].strip()
        head = lines[1].split()
        status = head[0] if head else "FAIL"
        try:
            ms = int(head[1]) if len(head) > 1 else 0
        except ValueError:
            ms = 0
        detail = "\n".join(lines[2:]).strip("\n")
        records[test_id] = HarnessRecord(status=status, runtime_ms=ms, detail=detail)
    return HarnessOutput(compile_error=None, records=records)


def case_stdout(record: HarnessRecord) -> str:
    """What the checker compares against the case's expected "PASS"."""
    if record.status == "PASS":
        return "PASS\n"
    return "FAIL\n" + record.detail + "\n"


def collect_test_ids(filename: str, source: str) -> list[str]:
    """Test ids in definition order, mirroring the runner's collection rules
    (module-level `test*` functions, `test*` methods of `Test*` classes)."""
    import ast

    tree = ast.parse(source, filename=filename)
    ids: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test"
        ):
            ids.append(f"{filename}::{node.name}")
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    item.name.startswith("test")
                ):
                    ids.append(f"{filename}::{node.name}::{item.name}")
    return ids
