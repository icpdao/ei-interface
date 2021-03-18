from collections import defaultdict

from core.error import NotYetVoteError
from core.pair import VOTED_KEY, PAIR_KEY, USER_KEY, SIZE_KEY


def calculate_es(vote_result) -> (dict, Exception):
    user_es = defaultdict(float)
    for vr in vote_result:
        if vr[VOTED_KEY] == -1:
            return user_es, NotYetVoteError
        for p in vr[PAIR_KEY][vr[VOTED_KEY]]:
            user_es[p[USER_KEY]] += 1 * p[SIZE_KEY]
    return user_es, None


def calculate_ei(user_es: dict, all_size: float) -> dict:
    return {u: round(user_es[u] / all_size, 1) for u in user_es}
