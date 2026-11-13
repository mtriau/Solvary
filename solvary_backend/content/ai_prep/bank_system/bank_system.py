class Bank:
    """Level 1: accounts, deposits, transfers. See the statement."""

    def create_account(self, timestamp: int, account_id: str) -> bool:
        raise NotImplementedError

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        raise NotImplementedError

    def transfer(self, timestamp: int, source: str, target: str, amount: int) -> int | None:
        raise NotImplementedError
