class MemoryDB:
    """An in-memory database of records. See the statement for the rules.

    Part 1: set, get, delete. Later parts add more methods to this class.
    """

    def set(self, key: str, field: str, value: str) -> None:
        """Store `value` in `field` of the record `key` (creating either)."""
        raise NotImplementedError

    def get(self, key: str, field: str) -> str | None:
        """The value of the field, or None if the record or field is absent."""
        raise NotImplementedError

    def delete(self, key: str, field: str) -> bool:
        """Remove the field. True iff it existed."""
        raise NotImplementedError
