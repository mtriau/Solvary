from pydantic import BaseModel


class RunRequest(BaseModel):
    language: str
    code: str
    stdin: str = ""
    workspace_id: str | None = None
    # pytest-mode problems: run their provided suite (stdin = test ids) instead
    # of executing the buffer as a script
    problem_id: str | None = None


class RunResponse(BaseModel):
    run_id: str


class PreludeResponse(BaseModel):
    """Names a Python submission can use without importing them."""

    language: str = "python"
    modules: list[str]
    names: dict[str, list[str]]
