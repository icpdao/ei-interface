from statistics import pvariance

IID_KEY = 'iid'
SIZE_KEY = 'size'
CATEGORY_KEY = 'category'
USER_KEY = 'user'


class Pair:

    def __init__(self) -> None:
        self.all_pair: list[dict] = []
        self.all_user: list[str] = []
        self.max_var: float = 0.025

    def set(self, pairs: list[dict]):
        self.all_pair = pairs

    def add(self, iid, size, category, user):
        self.all_pair.append({
            IID_KEY: iid, SIZE_KEY: size,
            CATEGORY_KEY: category, USER_KEY: user
        })

    def execute(self):
        self._sort()
        paired = []
        paired_index = []
        unpaired = []
        for i, p in enumerate(self.all_pair):
            if i in paired_index:
                continue
            pair = self._get_last_pair(i, p)
            if pair == -1:
                unpaired.append(p)
            else:
                paired.append([p, self.all_pair[pair]])
                paired_index.append(pair)
        paired += self._compose_unpaired(unpaired)
        return paired

    def _sort(self):
        self.all_pair = sorted(self.all_pair, key=lambda p: p[SIZE_KEY],
                               reverse=True)

    def _get_last_pair(self, i, current) -> int:
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
        return optimal

    def _compose_unpaired(self, unpaired: list):
        reverse_unpaired = unpaired[::-1]
        compose_ret = []
        while len(unpaired) > 0:
            up = unpaired[0]
            p, i = self._calculate_compose(up, reverse_unpaired)
            compose_ret.append([p, reverse_unpaired[:i]])
            reverse_unpaired = reverse_unpaired[i:]
            unpaired = unpaired[:i]
        return compose_ret

    def _calculate_compose(self, up, reverse_unpaired):
        p = []
        for i, rup in enumerate(reverse_unpaired):
            if pvariance([up[SIZE_KEY], rup[SIZE_KEY]]) >= self.max_var:
                return p, i
            p.append(rup)
        return reverse_unpaired, len(reverse_unpaired)

    def _calculate_weight(self, current, target) -> float:
        pv = pvariance([current[SIZE_KEY], target[SIZE_KEY]])
        if pv > self.max_var:
            return -1
        weight = pv
        if current[CATEGORY_KEY] == target[CATEGORY_KEY]:
            weight += 1
        else:
            weight += 0
        return weight
