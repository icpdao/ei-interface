import json
import uuid
from collections import defaultdict
from statistics import pvariance

from core.kw import kw_algorithm

IID_KEY = 'iid'
PID_KEY = 'pid'
VOTE_USER_KEY = 'vote_uid'
VOTED_KEY = 'voted'
PAIR_KEY = 'pair'
SIZE_KEY = 'size'
CATEGORY_KEY = 'category'
USER_KEY = 'uid'


class Pair:

    def __init__(self, sd: list[dict] = None) -> None:
        self.all_pair: list[dict] = []
        self.all_user: set = set()
        self.all_category: set = set()
        self.unpaired_dict = dict()
        if sd is not None:
            self.set(sd)

    def set(self, pairs: list[dict]):
        self.all_pair = pairs
        for p in pairs:
            self.all_user.add(p[USER_KEY])
            self.all_category.add(p[CATEGORY_KEY])

    def add(self, iid, size, category, user):
        self.all_pair.append({
            IID_KEY: iid, SIZE_KEY: size,
            CATEGORY_KEY: category, USER_KEY: user
        })
        self.all_user.add(user)
        self.all_category.add(category)

    def execute(self) -> (float, dict):
        self._sort()
        paired_with_weight = kw_algorithm(
            self.all_pair, self.all_pair[::], calculate_pair_weight)
        print('paired_with_weight', json.dumps(paired_with_weight, indent=4))
        paired = self._pair_user(paired_with_weight)
        return paired

    def _sort(self):
        self.all_pair = sorted(self.all_pair, key=lambda p: p[SIZE_KEY],
                               reverse=True)

    def _pair_user(self, pair):
        ret = defaultdict(list)
        for p in pair:
            tmp_w = -1
            choice_u = None
            for u in self.all_user:
                w = calculate_pair_user_weight(p, u, len(ret[u]))
                if tmp_w == -1 or tmp_w < w:
                    tmp_w = w
                    choice_u = u
            ret[choice_u].append({
                PID_KEY: uuid.uuid4().hex,
                VOTED_KEY: -1,
                VOTE_USER_KEY: choice_u,
                PAIR_KEY: [p[0], p[1]]
            })
        return ret


def calculate_pair_weight(current, target):
    if current[IID_KEY] == target[IID_KEY]:
        return 0
    size_weight = pvariance([current[SIZE_KEY], target[SIZE_KEY]])
    find_category = {current[CATEGORY_KEY], target[CATEGORY_KEY]}
    category_weight = len(find_category)
    find_user = {current[USER_KEY], target[USER_KEY]}
    user_weight = len(find_user)
    sc_weight = (size_weight * category_weight)
    if sc_weight == 0:
        return user_weight
    return user_weight / sc_weight


def calculate_pair_user_weight(pair, user, need_vote):
    pair_user = {pair[0][USER_KEY], pair[1][USER_KEY]}
    if {user} == pair_user:
        return 0
    user_weight = 1
    if user in pair_user:
        user_weight = 0.5
    if need_vote == 0:
        return user_weight
    return user_weight + (1 / need_vote)
