"""
The AI-company practice set (content/ai_prep): every reference solution must
pass its full provided suite through the real pytest harness (fake Piston
running the local interpreter), every stub must fail every test, and every
folder must match a Spec in scripts/seed_ai_prep.py (part count = suites).
"""

from pathlib import Path

import pytest

from app.services.execution.piston_executor import PistonExecutor
from tests.test_pytest_harness import _fake_piston, _job, _results

CONTENT = Path(__file__).resolve().parent.parent / "content" / "ai_prep"
FOLDERS = sorted(p for p in CONTENT.iterdir() if p.is_dir()) if CONTENT.is_dir() else []


def _suite(folder: Path) -> dict[str, str]:
    return {
        t.name: t.read_text(encoding="utf-8")
        for t in sorted(folder.glob(f"test_{folder.name}_p*.py"))
    }


@pytest.mark.skipif(not FOLDERS, reason="ai_prep content not present")
def test_every_folder_has_a_spec_with_matching_parts():
    from scripts.seed_ai_prep import SPECS

    specs = {spec.folder: spec for spec, _ in SPECS}
    for folder in FOLDERS:
        assert folder.name in specs, f"{folder.name}: no Spec in seed_ai_prep.py"
        spec = specs[folder.name]
        suites = _suite(folder)
        assert len(suites) == len(spec.parts), (
            f"{folder.name}: {len(suites)} suites vs {len(spec.parts)} parts in the Spec"
        )
        for n in range(1, len(spec.parts) + 1):
            text = (folder / f"PART{n}.md").read_text(encoding="utf-8")
            assert "Interviewer notes" in text, f"{folder.name} PART{n}: no interviewer notes"
            assert "pytest " not in text.replace("`pytest`", ""), (
                f"{folder.name} PART{n}: mentions a pytest command (use Submit)"
            )
        assert (folder / f"{folder.name}.py").is_file(), f"{folder.name}: stub missing"
        assert (folder / "reference.py").is_file(), f"{folder.name}: reference missing"


@pytest.mark.skipif(not FOLDERS, reason="ai_prep content not present")
@pytest.mark.asyncio
async def test_every_reference_is_green_and_every_stub_is_red():
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    summary = {}
    for folder in FOLDERS:
        module = folder.name
        files = _suite(folder)
        assert 3 <= len(files) <= 5, f"{module}: expected three to five part suites"

        reference = (folder / "reference.py").read_text(encoding="utf-8")
        job = _job(reference, files, module=module)
        results = [e for e in await _results(executor, job) if e.kind == "case_result"]
        failed = [job.cases[e.ordinal - 1].stdin for e in results if e.stdout != "PASS\n"]
        assert failed == [], f"{module}: reference fails {failed}"
        assert len(results) == len(job.cases)

        stub = (folder / f"{module}.py").read_text(encoding="utf-8")
        stub_results = [
            e
            for e in await _results(executor, _job(stub, files, module=module))
            if e.kind == "case_result"
        ]
        passing = [job.cases[e.ordinal - 1].stdin for e in stub_results if e.stdout == "PASS\n"]
        assert passing == [], f"{module}: stub passes {passing}"
        summary[module] = len(results)

    assert all(n >= 25 for n in summary.values()), summary
    assert sum(summary.values()) >= 150, summary
