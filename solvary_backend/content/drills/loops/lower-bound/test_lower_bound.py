from lower_bound import lower_bound


class Counting:
    """A sorted sequence that counts how many elements were looked at."""

    def __init__(self, n):
        self.n = n
        self.reads = 0

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        if not 0 <= i < self.n:
            raise IndexError(i)
        self.reads += 1
        return 2 * i  # 0, 2, 4, ...


def test_first_of_duplicates():
    assert lower_bound([1, 3, 3, 5], 3) == 1


def test_value_absent_goes_between():
    assert lower_bound([1, 3, 3, 5], 4) == 3


def test_larger_than_all():
    assert lower_bound([1, 3, 3, 5], 9) == 4


def test_smaller_than_all():
    assert lower_bound([1, 3, 3, 5], 0) == 0


def test_empty():
    assert lower_bound([], 1) == 0


def test_logarithmic_reads():
    seq = Counting(1_000_000)
    assert lower_bound(seq, 777_777) == 388_889
    assert seq.reads <= 25
    seq.reads = 0
    assert lower_bound(seq, 5_000_000) == 1_000_000
    assert seq.reads <= 25
