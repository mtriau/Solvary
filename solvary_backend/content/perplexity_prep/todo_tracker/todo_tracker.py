from enum import Enum


class TaskStatus(Enum):
    BLOCKED = 0
    READY_TO_EXECUTE = 1
    IN_PROGRESS = 2
    SUCCEEDED = 3
    FAILED = 4


class ToDoList:
    """Part 1: add / get / set / render. See the statement."""

    def __init__(self) -> None:
        raise NotImplementedError

    def add(self, description: str, deps: list[int] | None = None) -> int:
        raise NotImplementedError

    def get(self, task_id: int) -> str | None:
        raise NotImplementedError

    def set(self, task_id: int, new_status: TaskStatus) -> bool:
        raise NotImplementedError

    def render(self) -> str:
        raise NotImplementedError
