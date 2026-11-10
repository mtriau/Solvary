class FileSystem:
    """Part 1: mkdir (strict) / touch / write / read / ls. See the statement."""

    def __init__(self) -> None:
        raise NotImplementedError

    def mkdir(self, path: str) -> None:
        raise NotImplementedError

    def touch(self, path: str) -> None:
        raise NotImplementedError

    def write(self, path: str, content: str) -> None:
        raise NotImplementedError

    def read(self, path: str) -> str:
        raise NotImplementedError

    def ls(self, path: str) -> list[str]:
        raise NotImplementedError
