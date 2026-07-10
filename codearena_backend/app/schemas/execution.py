from pydantic import BaseModel


class RunRequest(BaseModel):
    language: str
    code: str
    stdin: str = ""
    workspace_id: str | None = None


class RunResponse(BaseModel):
    run_id: str
