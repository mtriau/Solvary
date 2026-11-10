"""
The Python idiom drills (content/drills): every reference solution must pass
its provided suite through the real pytest harness (fake Piston running the
local interpreter), every stub must fail every test, and the content layout
the seeder relies on must hold (ORDER file, one test file per drill, a title
line, notes).
"""

from pathlib import Path

import pytest

from app.services.drill_service import TOPIC_BY_SLUG
from app.services.execution.piston_executor import PistonExecutor
from tests.test_pytest_harness import _fake_piston, _job, _results

CONTENT = Path(__file__).resolve().parent.parent / "content" / "drills"
TOPICS = sorted(p for p in CONTENT.iterdir() if p.is_dir()) if CONTENT.is_dir() else []


def _drills() -> list[tuple[str, str, Path]]:
    out = []
    for topic in TOPICS:
        for slug in (topic / "ORDER").read_text(encoding="utf-8").split():
            out.append((topic.name, slug, topic / slug))
    return out


@pytest.mark.skipif(not TOPICS, reason="drill content not present")
def test_layout_matches_what_the_seeder_expects():
    drills = _drills()
    assert len(drills) >= 30
    assert len({slug for _, slug, _ in drills}) == len(drills), "duplicate drill slug"
    for topic, slug, folder in drills:
        assert topic in TOPIC_BY_SLUG, f"{slug}: topic {topic} not in drill_service.TOPICS"
        module = slug.replace("-", "_")
        for name in ("PROBLEM.md", "NOTES.md", "reference.py", f"{module}.py", f"test_{module}.py"):
            assert (folder / name).is_file(), f"{slug}: missing {name}"
        first = (folder / "PROBLEM.md").read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith("# "), f"{slug}: PROBLEM.md must start with a '# Title' line"


@pytest.mark.skipif(not TOPICS, reason="drill content not present")
@pytest.mark.asyncio
async def test_every_reference_is_green_and_every_stub_is_red():
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    total = 0
    for _topic, slug, folder in _drills():
        module = slug.replace("-", "_")
        test_name = f"test_{module}.py"
        files = {test_name: (folder / test_name).read_text(encoding="utf-8")}

        reference = (folder / "reference.py").read_text(encoding="utf-8")
        job = _job(reference, files, module=module)
        results = [e for e in await _results(executor, job) if e.kind == "case_result"]
        failed = [job.cases[e.ordinal - 1].stdin for e in results if e.stdout != "PASS\n"]
        assert failed == [], f"{slug}: reference fails {failed}"
        assert len(results) == len(job.cases) >= 4, f"{slug}: want at least 4 tests"

        stub = (folder / f"{module}.py").read_text(encoding="utf-8")
        stub_results = [
            e
            for e in await _results(executor, _job(stub, files, module=module))
            if e.kind == "case_result"
        ]
        passing = [job.cases[e.ordinal - 1].stdin for e in stub_results if e.stdout == "PASS\n"]
        assert passing == [], f"{slug}: stub passes {passing}"
        total += len(results)
    assert total >= 150
