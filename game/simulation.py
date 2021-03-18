import random
from itertools import repeat
from string import ascii_uppercase, ascii_lowercase

from core.ei import calculate_es, calculate_ei
from core.pair import Pair, IID_KEY, SIZE_KEY, VOTED_KEY, PAIR_KEY, USER_KEY, \
    CATEGORY_KEY
from game.error import NotYetPairedError, NotYetVotedError

DEFAULT_GREED: int = 0
DEFAULT_DISSENT_TOLERANCE: float = 0.1
DEFAULT_OBJECTIVE_VOTING = 1

UNAME_KEY = 'name'
ICP_NUM_KEY = 'icp_num'
GREED_KEY = 'gd'
DISSENT_TOLERANCE_KEY = 'dt'
SUBJECTIVE_VOTING_KEY = 'sv'
ICP_KEY = 'icp'
FACTOR_KEY = 'factor'


def simula_user(data: list[dict] or int) -> (list, float):
    if isinstance(data, int):
        data = repeat(dict(), data)
    users = []
    all_size = 0
    for i, d in enumerate(data):
        uid = d.get(USER_KEY) or str(i)
        icp_num = d.get(ICP_NUM_KEY) or random.randint(1, 3)
        greed = d.get(GREED_KEY) or DEFAULT_GREED
        dissent_tolerance = d.get(
            DISSENT_TOLERANCE_KEY) or DEFAULT_DISSENT_TOLERANCE
        objective_voting = d.get(
            SUBJECTIVE_VOTING_KEY) or DEFAULT_OBJECTIVE_VOTING
        name = d.get(UNAME_KEY) or (
                ascii_uppercase[random.randint(0, 25)] +
                ascii_lowercase[random.randint(0, 25)]
        )
        icp = []
        if icp_num > 0:
            icp, size = simula_icp(
                str(i), icp_num, DEFAULT_GREED, DEFAULT_DISSENT_TOLERANCE)
            all_size += size
        users.append({
            USER_KEY: uid,
            UNAME_KEY: name,
            FACTOR_KEY: (greed, dissent_tolerance, objective_voting),
            ICP_KEY: icp
        })
    return users, all_size


def simula_icp(uid: str, num: int, greed: int,
               dissent_tolerance: float) -> (list, float):
    icp = []
    all_size = 0
    for i in range(num):
        real_value = round(random.gauss(8, 1), 1)
        if real_value <= 0:
            continue
        iid = f'{uid}.{i}'
        offset = abs(random.gauss(greed, dissent_tolerance))
        size = round(real_value + offset * real_value, 1)
        icp.append({
            USER_KEY: uid,
            IID_KEY: iid,
            'title': f'this is {uid}-{i} icp.',
            'real_value': real_value,
            SIZE_KEY: size,
            CATEGORY_KEY: ascii_uppercase[random.randint(0, 25)]
        })
        all_size += size
    return icp, all_size


class GameSimulation:
    # user: [{'uid': '', 'name': '', 'factor': ['greed', 'dissent_tolerance', 'subjective_voting']}]
    # icp: [{'iid': '', 'title': '', 'user': 'uid', 'size': '', 'real_value': ''}]
    # ei: {'uid': 'ei'}

    # greed: unit expansion multiplier, default = 0
    # dissent_tolerance: unit resistance to expansion coefficient, default = 0.1
    # real_value: real work metrics, unit: hour
    # subjective_voting:
    def __init__(self, sd: list[dict] or int):
        self.data, self.all_size = simula_user(sd)
        self.pair_ins = Pair()
        self.paired: dict = dict()
        self.paired_var: float = -1
        self.vote_result: list[dict] = []

    def do_pair(self):
        icp = self._extract_icp()
        self.pair_ins.set(icp)
        print('icp', icp)
        self.paired_var, self.paired = self.pair_ins.execute()
        return self.paired

    def do_vote(self):
        if self.paired_var == -1:
            raise NotYetPairedError
        user_ov = self._extract_user_ov()
        vote_result: list[dict] = []
        for u in self.paired:
            ov = user_ov[u]
            for p in self.paired[u]:
                pa_size = sum([x[SIZE_KEY] for x in p[PAIR_KEY][0]])
                pb_size = sum([x[SIZE_KEY] for x in p[PAIR_KEY][1]])
                ov_value = random.gauss(pa_size / pb_size, ov)
                if ov_value < 1:
                    p[VOTED_KEY] = 0
                else:
                    p[VOTED_KEY] = 1
                vote_result.append(p)
        self.vote_result = vote_result
        return vote_result

    @property
    def es(self):
        if len(self.vote_result) == 0:
            raise NotYetVotedError
        es, e = calculate_es(self.vote_result)
        if e is not None:
            raise e
        return es

    @property
    def ei(self):
        return calculate_ei(self.es, self.all_size)

    def _extract_icp(self):
        icp = []
        for d in self.data:
            icp += d[ICP_KEY]
        return icp

    def _extract_user_ov(self) -> dict[float]:
        user_ov = {}
        for d in self.data:
            user_ov[d[USER_KEY]] = d[FACTOR_KEY][2]
        return user_ov
