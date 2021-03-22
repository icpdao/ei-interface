from collections import defaultdict
from decimal import Decimal, getcontext

from core.error import NotYetVoteError
from core.pair import VOTED_KEY, PAIR_KEY, USER_KEY, SIZE_KEY

getcontext().prec = 2


def calculate_es(vote_result) -> (dict, Exception):
    user_es = defaultdict(Decimal)
    for vr in vote_result:
        if vr[VOTED_KEY] == -1:
            return user_es, NotYetVoteError
        for i, p in enumerate(vr[PAIR_KEY]):
            if i == vr[VOTED_KEY]:
                user_es[p[USER_KEY]] += Decimal(str(p[SIZE_KEY]))
            else:
                user_es[p[USER_KEY]] += Decimal('0')
    return user_es, None


def calculate_ei(user_es: dict, all_size: float) -> dict:
    return {u: user_es[u] / Decimal(str(all_size)) for u in user_es}
