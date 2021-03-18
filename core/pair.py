import json
import logging
import uuid
from statistics import pvariance

from core.utils import get_full_stirling_list, get_stirling_list

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
        self.all_user: tuple = tuple()
        self.all_category: tuple = tuple()
        self.unpaired_dict = dict()
        self.max_var: float = 0.025
        if sd is not None:
            self.set(sd)

    def set(self, pairs: list[dict]):
        self.all_pair = pairs

    def add(self, iid, size, category, user):
        self.all_pair.append({
            IID_KEY: iid, SIZE_KEY: size,
            CATEGORY_KEY: category, USER_KEY: user
        })

    def execute(self) -> (float, dict):
        self._sort()
        var = 0
        paired = []
        paired_index = []
        unpaired = []
        all_user = set()
        all_category = set()
        for i, p in enumerate(self.all_pair):
            all_user.add(p[USER_KEY])
            all_category.add(p[CATEGORY_KEY])
            if i in paired_index:
                continue
            tmp_var, pair = self._get_last_pair(i, p)
            if pair == -1:
                unpaired.append(p)
            else:
                paired.append([
                    [p], [self.all_pair[pair]]
                ])
                paired_index.append(pair)
                var += tmp_var
        print('paired1 end', paired)
        self.all_user = tuple(all_user)
        self.all_category = tuple(all_category)
        min_var, min_paired = self._compose_unpaired(unpaired)
        var += min_var
        paired += min_paired
        print('paired', json.dumps(paired, indent=4))
        avg_var = round(var / len(paired), 1)
        paired_user = self._pair_user(paired)
        return avg_var, paired_user

    def _sort(self):
        self.all_pair = sorted(self.all_pair, key=lambda p: p[SIZE_KEY],
                               reverse=True)

    def _get_last_pair(self, i, current) -> (int, int):
        j = 1
        optimal: int = -1
        weight: float = 0
        while True:
            if (i + j) >= len(self.all_pair):
                break
            pair = self.all_pair[i + j]
            pv = self._calculate_weight(current, pair)
            if current[USER_KEY] != pair[USER_KEY] \
                    and pv != -1 and pv < weight:
                weight = pv
                optimal = i + j
            j += 1
        return weight, optimal

    def _calculate_sum_size(self, l):
        return sum([self.unpaired_dict[ll][SIZE_KEY] for ll in l])

    def _find_min_var(self, s: list[list]):
        if len(s) < 2:
            return 0, None, ValueError
        min_var = 0
        min_pair = None
        find_user = set()
        find_category = set()
        for ss in get_stirling_list(s, 2):
            clear_s1 = []
            clear_s2 = []
            s1_size = 0
            s2_size = 0
            for ll in ss[0]:
                s1_size += self.unpaired_dict[ll][SIZE_KEY]
                find_user.add(self.unpaired_dict[ll][USER_KEY])
                find_category.add(self.unpaired_dict[ll][CATEGORY_KEY])
                clear_s1.append(self.unpaired_dict[ll])
            for ll in ss[1]:
                s2_size += self.unpaired_dict[ll][SIZE_KEY]
                find_user.add(self.unpaired_dict[ll][USER_KEY])
                find_category.add(self.unpaired_dict[ll][CATEGORY_KEY])
                clear_s2.append(self.unpaired_dict[ll])
            pv = pvariance([s1_size, s2_size])
            if min_pair is None or pv < min_var:
                min_var = pv
                min_pair = [clear_s1, clear_s2]
        if len(find_user) == 1 and len(self.all_user) != 1:
            return min_var, min_pair, ValueError
        min_var += round(len(find_user) / len(self.all_user), 2)
        min_var += round(len(find_category) / len(self.all_category), 2)
        return min_var, min_pair, None

    def _compose_unpaired(self, unpaired: list):
        print('paired2 begin', unpaired)
        for up in unpaired:
            self.unpaired_dict[up[IID_KEY]] = up
        min_var = -1
        min_pair = None
        for sl in get_full_stirling_list(list(self.unpaired_dict.keys())):
            # print(sl)
            tmp_min_var = 0
            tmp_min_pair = []
            tmp_err = None
            for s in sl:
                tt_min_var, tt_min_pair, tt_err = self._find_min_var(s)
                if tt_err is not None:
                    tmp_err = tt_err
                    continue
                tmp_min_var += tt_min_var
                tmp_min_pair.append(tt_min_pair)
            if tmp_err is not None:
                continue
            if min_var == -1 or (tmp_min_var < min_var and len(tmp_min_pair) > 0):
                min_var = tmp_min_var
                min_pair = tmp_min_pair
        print('paired2 end', min_var, min_pair)
        return min_var, min_pair

    def _calculate_weight(self, current, target) -> float:
        pv = pvariance([current[SIZE_KEY], target[SIZE_KEY]])
        if pv > self.max_var:
            return -1
        return pv

    def _pair_user_check(self, check, index) -> int:
        if len(check) == 0:
            return -1
        a = len(check)
        in_pair_user = set()
        [in_pair_user.add(xx[USER_KEY]) for c in check for x in c for xx in x]
        if self.all_user[index] in in_pair_user:
            return a + 1
        return a

    @staticmethod
    def _struct_pair(pair: list, uid):
        ret = []
        for pa in pair:
            ret.append({
                PID_KEY: uuid.uuid4().hex,
                VOTED_KEY: -1,
                VOTE_USER_KEY: uid,
                PAIR_KEY: pa
            })
        return ret

    def _pair_user(self, paired) -> dict:
        min_var = -1
        min_pair = None
        print('paired', paired)
        for c in get_stirling_list(paired, len(self.all_user)):
            tmp_var = pvariance(
                [self._pair_user_check(x, i) for i, x in enumerate(c)])
            if min_var == -1 or tmp_var < min_var:
                min_var = tmp_var
                min_pair = c
        pair_result = {}
        if min_pair is None:
            return pair_result
        for i, u in enumerate(self.all_user):
            pair_result[u] = self._struct_pair(min_pair[i], u)
        return pair_result
