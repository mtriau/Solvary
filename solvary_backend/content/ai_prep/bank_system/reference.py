from bisect import bisect_right
from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf


@dataclass
class Payment:
    seq: int
    owner: str
    amount: int
    due: int
    status: str = "PENDING"


class Bank:
    def __init__(self):
        self._balance: dict[str, int] = {}
        self._spent: dict[str, int] = {}
        self._history: dict[str, list[tuple[int, int]]] = {}  # (timestamp, balance)
        self._payments: dict[str, Payment] = {}
        self._due: list[tuple[int, int, str]] = []  # (due, seq, payment_id)

    # -- internals ---------------------------------------------------------

    def _set_balance(self, account_id: str, timestamp: int, balance: int) -> None:
        history = self._history[account_id]
        if history:  # keep checkpoints ordered even if a payment ran "late"
            timestamp = max(timestamp, history[-1][0])
        self._balance[account_id] = balance
        history.append((timestamp, balance))

    def _process_due(self, now: int) -> None:
        """Run every pending payment due at or before `now`, in scheduling order."""
        ready = []
        while self._due and self._due[0][0] <= now:
            ready.append(heappop(self._due))
        for _, _, payment_id in sorted(ready, key=lambda entry: entry[1]):
            payment = self._payments[payment_id]
            if payment.status != "PENDING":
                continue
            owner = payment.owner
            if self._balance[owner] >= payment.amount:
                self._set_balance(owner, payment.due, self._balance[owner] - payment.amount)
                self._spent[owner] += payment.amount
                payment.status = "PAID"
            else:
                payment.status = "FAILED"

    # -- level 1 -----------------------------------------------------------

    def create_account(self, timestamp: int, account_id: str) -> bool:
        self._process_due(timestamp)
        if account_id in self._balance:
            return False
        self._balance[account_id] = 0
        self._spent[account_id] = 0
        self._history[account_id] = [(timestamp, 0)]
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self._process_due(timestamp)
        if account_id not in self._balance:
            return None
        self._set_balance(account_id, timestamp, self._balance[account_id] + amount)
        return self._balance[account_id]

    def transfer(self, timestamp: int, source: str, target: str, amount: int) -> int | None:
        self._process_due(timestamp)
        if source == target or source not in self._balance or target not in self._balance:
            return None
        if self._balance[source] < amount:
            return None
        self._set_balance(source, timestamp, self._balance[source] - amount)
        self._set_balance(target, timestamp, self._balance[target] + amount)
        self._spent[source] += amount
        return self._balance[source]

    # -- level 2 -----------------------------------------------------------

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        self._process_due(timestamp)
        ranked = sorted(self._spent.items(), key=lambda item: (-item[1], item[0]))
        return [f"{account_id}({total})" for account_id, total in ranked[:n]]

    # -- level 3 -----------------------------------------------------------

    def schedule_payment(self, timestamp: int, account_id: str, amount: int, delay: int) -> str | None:
        self._process_due(timestamp)
        if account_id not in self._balance:
            return None
        seq = len(self._payments) + 1
        payment_id = f"payment{seq}"
        self._payments[payment_id] = Payment(seq, account_id, amount, timestamp + delay)
        heappush(self._due, (timestamp + delay, seq, payment_id))
        return payment_id

    def cancel_payment(self, timestamp: int, account_id: str, payment_id: str) -> bool:
        self._process_due(timestamp)
        payment = self._payments.get(payment_id)
        if payment is None or payment.owner != account_id or payment.status != "PENDING":
            return False
        payment.status = "CANCELED"
        return True

    def get_payment_status(self, timestamp: int, account_id: str, payment_id: str) -> str | None:
        self._process_due(timestamp)
        payment = self._payments.get(payment_id)
        if payment is None or payment.owner != account_id:
            return None
        return payment.status

    # -- level 4 -----------------------------------------------------------

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        self._process_due(timestamp)
        if account_id_1 == account_id_2 or account_id_1 not in self._balance or account_id_2 not in self._balance:
            return False
        self._set_balance(account_id_1, timestamp, self._balance[account_id_1] + self._balance[account_id_2])
        self._spent[account_id_1] += self._spent[account_id_2]
        for payment in self._payments.values():
            if payment.owner == account_id_2:
                payment.owner = account_id_1
        for table in (self._balance, self._spent, self._history):
            del table[account_id_2]
        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        self._process_due(timestamp)
        history = self._history.get(account_id)
        if history is None:
            return None
        i = bisect_right(history, (time_at, inf))
        return history[i - 1][1] if i else None
