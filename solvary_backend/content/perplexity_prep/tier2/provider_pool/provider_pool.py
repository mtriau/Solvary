class ProviderPool:
    """Priority routing with consecutive-failure health tracking. See PROBLEMS.md #1."""

    def __init__(self) -> None:
        raise NotImplementedError

    def add_provider(self, name: str, priority: int, capabilities: set[str],
                     failure_threshold: int = 3) -> None:
        raise NotImplementedError

    def route(self, capability: str) -> str | None:
        raise NotImplementedError

    def report_failure(self, name: str) -> None:
        raise NotImplementedError

    def report_success(self, name: str) -> None:
        raise NotImplementedError
