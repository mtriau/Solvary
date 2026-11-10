"""
Python prelude: the standard-library names every Python submission gets
without importing them (the LeetCode convention). Covers all three ways
Python runs in the sandbox — plain scripts (stdin/stdout problems and
ad-hoc Run), and the candidate module in pytest judge mode.

How it works: a small `solvary_prelude.py` is shipped into the sandbox
alongside the code. Its `install()` imports each module below and copies
the module plus the listed names onto the `builtins` module, so name
lookup finds them after the code's own globals, exactly like `len` or
`print`. Nothing is prepended to the user's source, so line numbers in
tracebacks stay right, and a user who still writes the import loses
nothing. A name the sandbox's Python lacks (e.g. `itertools.batched`
before 3.12) is skipped, and an existing builtin is never overwritten.

Plain scripts cannot be run directly any more (there is no hook to run
before a script's first line), so `script_files()` wraps them: Piston runs
`main.py`, which installs the prelude and executes `solution.py` as
`__main__` with its own filename, forwarding stdin, stdout, the exit code
and a traceback that starts at the user's code.
"""

from __future__ import annotations

import json

# module -> names re-exported from it. The module itself is always exposed
# under its own name, so `math.gcd` and `gcd` both work. Order is the order
# shown to users.
PRELUDE: dict[str, list[str]] = {
    "collections": ["Counter", "defaultdict", "deque", "OrderedDict", "namedtuple", "ChainMap"],
    "itertools": [
        "accumulate",
        "chain",
        "combinations",
        "combinations_with_replacement",
        "count",
        "cycle",
        "dropwhile",
        "groupby",
        "islice",
        "pairwise",
        "permutations",
        "product",
        "repeat",
        "starmap",
        "takewhile",
        "tee",
        "zip_longest",
        "batched",
    ],
    "functools": [
        "reduce",
        "lru_cache",
        "cache",
        "partial",
        "cmp_to_key",
        "total_ordering",
        "wraps",
    ],
    "heapq": [
        "heappush",
        "heappop",
        "heapify",
        "heappushpop",
        "heapreplace",
        "nlargest",
        "nsmallest",
    ],
    "bisect": ["bisect_left", "bisect_right", "insort", "insort_left", "insort_right"],
    "math": [
        "inf",
        "gcd",
        "lcm",
        "sqrt",
        "isqrt",
        "ceil",
        "floor",
        "log2",
        "log10",
        "comb",
        "perm",
        "factorial",
        "hypot",
    ],
    "typing": [
        "Any",
        "Callable",
        "ClassVar",
        "DefaultDict",
        "Deque",
        "Dict",
        "Final",
        "FrozenSet",
        "Generator",
        "Generic",
        "Iterable",
        "Iterator",
        "List",
        "Literal",
        "Mapping",
        "MutableMapping",
        "NamedTuple",
        "Optional",
        "Protocol",
        "Sequence",
        "Set",
        "Tuple",
        "TypedDict",
        "TypeVar",
        "Union",
        "cast",
        "overload",
    ],
    "dataclasses": ["dataclass", "field", "asdict", "astuple"],
    "operator": ["itemgetter", "attrgetter"],
    "string": ["ascii_lowercase", "ascii_uppercase", "ascii_letters", "digits", "punctuation"],
    "enum": ["Enum", "IntEnum", "auto"],
    "abc": ["ABC", "abstractmethod"],
    "copy": ["deepcopy"],
    "re": [],
    "json": [],
    "random": [],
    "sys": [],
    "os": [],
    "time": [],
    "datetime": [],
}

PRELUDE_FILENAME = "solvary_prelude.py"
SCRIPT_FILENAME = "solution.py"

# ── solvary_prelude.py: shipped into the sandbox ───────────────────────

_PRELUDE_SOURCE = r'''
"""Solvary: standard-library names available without an import."""
import builtins
import importlib

SPEC = __SPEC__


def install():
    for modname, names in SPEC.items():
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        if not hasattr(builtins, modname):
            setattr(builtins, modname, mod)
        for name in names:
            try:
                obj = getattr(mod, name)
            except AttributeError:
                continue  # not in this Python version
            if not hasattr(builtins, name):
                setattr(builtins, name, obj)
'''

# ── main.py for plain scripts ──────────────────────────────────────────

_SCRIPT_RUNNER = r"""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # the sandbox may run with -I, which drops the script dir
import solvary_prelude  # noqa: E402

solvary_prelude.install()

PATH = os.path.join(HERE, __SCRIPT__)


def _main():
    with open(PATH, encoding="utf-8") as f:
        source = f.read()
    try:
        code = compile(source, __SCRIPT__, "exec")
    except SyntaxError:
        sys.stderr.write("".join(traceback.format_exception_only(*sys.exc_info()[:2])))
        sys.exit(1)
    sys.argv = [__SCRIPT__]
    namespace = {"__name__": "__main__", "__file__": __SCRIPT__, "__builtins__": __builtins__}
    try:
        exec(code, namespace)
    except SystemExit:
        raise
    except BaseException as exc:
        # Drop this runner's frame so the traceback starts in the user's code
        tb = exc.__traceback__.tb_next if exc.__traceback__ else None
        sys.stdout.flush()
        sys.stderr.write("".join(traceback.format_exception(type(exc), exc, tb)))
        sys.exit(1)


_main()
"""


def prelude_source() -> str:
    return _PRELUDE_SOURCE.replace("__SPEC__", json.dumps(PRELUDE, indent=4))


def prelude_file() -> dict:
    return {"name": PRELUDE_FILENAME, "content": prelude_source()}


def script_files(code: str) -> list[dict]:
    """The sandbox file set for a plain Python script: runner first (Piston
    runs files[0]), the prelude, then the user's code as `solution.py`."""
    runner = _SCRIPT_RUNNER.replace("__SCRIPT__", json.dumps(SCRIPT_FILENAME))
    return [
        {"name": "main.py", "content": runner},
        prelude_file(),
        {"name": SCRIPT_FILENAME, "content": code},
    ]


def describe() -> dict:
    """What the API tells the UI: modules and the names taken from each."""
    return {"modules": list(PRELUDE), "names": {m: list(n) for m, n in PRELUDE.items()}}
