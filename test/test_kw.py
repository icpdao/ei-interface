import random

from core.kw import kw_algorithm


def test_kw():
    def test_f(a, t):
        return random.random()

    print(kw_algorithm(['a', 't', 'y', 'z'], [1, 2, 3, 4], test_f))
