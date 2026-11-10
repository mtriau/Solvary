"""
The Sierra practice set (content/sierra_prep): every reference solution must
pass its full provided suite through the real pytest harness (fake Piston
running the local interpreter), and every stub must fail every test.
"""

from pathlib import Path

import pytest

from app.services.execution.piston_executor import PistonExecutor
from tests.test_pytest_harness import _fake_piston, _job, _results

CONTENT = Path(__file__).resolve().parent.parent / "content" / "sierra_prep"
FOLDERS = sorted(p for p in CONTENT.iterdir() if p.is_dir()) if CONTENT.is_dir() else []


def _suite(folder: Path) -> dict[str, str]:
    return {
        t.name: t.read_text(encoding="utf-8")
        for t in sorted(folder.glob(f"test_{folder.name}_p*.py"))
    }


@pytest.mark.skipif(not FOLDERS, reason="sierra content not present")
@pytest.mark.asyncio
async def test_every_reference_is_green_and_every_stub_is_red():
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    summary = {}
    for folder in FOLDERS:
        module = folder.name
        files = _suite(folder)
        assert len(files) == 3, f"{module}: expected three part suites"

        reference = (folder / "reference.py").read_text(encoding="utf-8")
        job = _job(reference, files, module=module)
        results = [e for e in await _results(executor, job) if e.kind == "case_result"]
        failed = [job.cases[e.ordinal - 1].stdin for e in results if e.stdout != "PASS\n"]
        assert failed == [], f"{module}: reference fails {failed}"
        assert len(results) == len(job.cases)

        stub = (folder / f"{module}.py").read_text(encoding="utf-8")
        stub_results = [
            e for e in await _results(executor, _job(stub, files, module=module))
            if e.kind == "case_result"
        ]
        passing = [job.cases[e.ordinal - 1].stdin for e in stub_results if e.stdout == "PASS\n"]
        assert passing == [], f"{module}: stub passes {passing}"
        summary[module] = len(results)

    assert summary["conversation_history"] >= 30
    assert sum(summary.values()) >= 200
