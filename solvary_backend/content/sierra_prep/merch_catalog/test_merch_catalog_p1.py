# Provided tests for Part 1: retry with exponential backoff and a timeout.

import pytest
from merch_catalog import retry


class Flaky:
    def __init__(self, failures: int, exc=ConnectionError, result="ok"):
        self.failures = failures
        self.exc = exc
        self.result = result
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc(f"fail #{self.calls}")
        return self.result


class FakeClock:
    """Each sleep(d) advances the clock by d."""

    def __init__(self):
        self.now = 1000.0
        self.slept: list[float] = []

    def sleep(self, d):
        self.slept.append(d)
        self.now += d

    def clock(self):
        return self.now


def test_spec_example():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("503")
        return "ok"

    slept = []
    assert retry(flaky, sleep=slept.append) == "ok"
    assert slept == [0.1, 0.2]


def test_success_first_time_does_not_sleep():
    f = Flaky(0, result=42)
    slept = []
    assert retry(f, sleep=slept.append) == 42
    assert f.calls == 1 and slept == []


def test_backoff_sequence_is_capped():
    f = Flaky(7)
    slept = []
    assert retry(f, attempts=8, sleep=slept.append) == "ok"
    assert slept == pytest.approx([0.1, 0.2, 0.4, 0.8, 1.6, 2.0, 2.0])
    assert f.calls == 8


def test_custom_base_and_factor():
    f = Flaky(3)
    slept = []
    retry(f, base_delay=1.0, factor=3.0, max_delay=100.0, sleep=slept.append)
    assert slept == pytest.approx([1.0, 3.0, 9.0])


def test_exhausted_attempts_reraise_the_last_exception():
    f = Flaky(10)
    slept = []
    with pytest.raises(ConnectionError) as info:
        retry(f, attempts=3, sleep=slept.append)
    assert "fail #3" in str(info.value)
    assert f.calls == 3
    assert slept == pytest.approx([0.1, 0.2])  # no sleep after the final failure


def test_single_attempt_never_sleeps():
    f = Flaky(1)
    slept = []
    with pytest.raises(ConnectionError):
        retry(f, attempts=1, sleep=slept.append)
    assert f.calls == 1 and slept == []


def test_non_matching_exception_propagates_immediately():
    f = Flaky(2, exc=KeyError)
    slept = []
    with pytest.raises(KeyError):
        retry(f, retry_on=(ConnectionError, TimeoutError), sleep=slept.append)
    assert f.calls == 1 and slept == []


def test_retry_on_subclass_matches():
    class MyErr(ConnectionError):
        pass

    f = Flaky(1, exc=MyErr)
    assert retry(f, retry_on=(ConnectionError,), sleep=lambda d: None) == "ok"
    assert f.calls == 2


def test_timeout_stops_before_a_sleep_that_would_exceed_it():
    fc = FakeClock()
    f = Flaky(10)
    with pytest.raises(ConnectionError) as info:
        retry(f, attempts=10, timeout=0.5, sleep=fc.sleep, clock=fc.clock)
    # slept 0.1 (t=0.1), 0.2 (t=0.3); next 0.4 would reach 0.7 > 0.5 -> stop
    assert fc.slept == pytest.approx([0.1, 0.2])
    assert f.calls == 3
    assert "fail #3" in str(info.value)


def test_timeout_allows_a_sleep_that_fits_the_budget():
    fc = FakeClock()
    f = Flaky(2)
    assert retry(f, timeout=0.35, sleep=fc.sleep, clock=fc.clock) == "ok"
    assert fc.slept == pytest.approx([0.1, 0.2])


def test_clock_is_read_through_the_injected_callable():
    reads = []

    def clock():
        reads.append(1)
        return 0.0

    f = Flaky(1)
    retry(f, timeout=10.0, sleep=lambda d: None, clock=clock)
    assert len(reads) >= 1


def test_result_value_is_passed_through():
    assert retry(lambda: [1, 2, 3], sleep=lambda d: None) == [1, 2, 3]
    assert retry(lambda: None, sleep=lambda d: None) is None
