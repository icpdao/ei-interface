import json
import math
import random
from statistics import geometric_mean, harmonic_mean
from collections import defaultdict
from decimal import Decimal
from itertools import repeat
from string import ascii_uppercase, ascii_lowercase

import numpy
from faker import Faker

from core.ei import calculate_es, calculate_ei
from core.error import NotYetVoteError
from core.pair import Pair, IID_KEY, SIZE_KEY, VOTED_KEY, PAIR_KEY, USER_KEY, \
    CATEGORY_KEY, PID_KEY
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

faker = Faker()


class GameSimulation:
    def __init__(self, sd: list[dict] or int):
        self._simula_user(sd)
        # self.data, self.all_size = simula_user(sd)
        self.pair_ins = Pair()
        self.paired: dict = dict()
        self.icp = dict()
        self.all_icp = dict()
        self.vote_result: list[dict] = []
        self.all_vote_result = {}
        self.all_user_reward = {}
        self.all_user_ei = {}
        self.sid = None
        self.user_size = {}
        self.user_real_size = {}
        self.user_reward = {}
        self.user_ei = {}

    def _simula_user(self, data):
        if isinstance(data, int):
            data = repeat(dict(), data)
        self.users = {}
        self.user_factor = {}
        self.all_user_factor = defaultdict(list)

        for i, d in enumerate(data):
            uid = d.get(USER_KEY) or str(i)
            greed = d.get(GREED_KEY) or DEFAULT_GREED
            dissent_tolerance = d.get(
                DISSENT_TOLERANCE_KEY) or DEFAULT_DISSENT_TOLERANCE
            objective_voting = d.get(
                SUBJECTIVE_VOTING_KEY) or DEFAULT_OBJECTIVE_VOTING
            reward_tolerance = d.get(
                'rt') or round(random.gauss(4, 1))
            reliability_factor = 1
            self.user_factor[uid] = {
                'greed': greed, 'dissent_tolerance': dissent_tolerance,
                'objective_voting': objective_voting,
                'reward_tolerance': reward_tolerance,
                'reliability_factor': reliability_factor
            }
            name = d.get(UNAME_KEY) or faker.name()
            self.users[uid] = {USER_KEY: uid, UNAME_KEY: name}
            print(f'用户 id={uid} {name} 加入了, 他的贪婪值是 {greed}, '
                  f'异议容忍度是 {dissent_tolerance}, '
                  f'报酬落差容忍度是 {reward_tolerance}, '
                  f'主观投票度是 {objective_voting}, '
                  f'目前可靠系数 1')
            self.all_user_factor[uid].append(self.user_factor[uid])

    def simula_icp(self, sid):
        all_size = 0
        self.icp = dict()
        self.sid = sid
        self.user_size = {}
        self.user_real_size = {}
        self.user_reward = {}
        self.user_ei = {}
        for u in self.users:
            icp_num = 3
            icp, size, real_size = self._gen_icp(u, icp_num)
            self.user_size[u] = size
            self.user_real_size[u] = real_size
            print(f'用户 id={u} {self.users[u][UNAME_KEY]} '
                  f'本次产出了 {icp_num} 个 ICP, '
                  f'实际工作 size={real_size}, '
                  f'申报 size={size}')
            all_size += size
            self.icp[u] = icp
        self.all_icp[sid] = self.icp

    def _gen_icp(self, uid: str, num: int) -> (list, float):
        icp = []
        all_size = 0
        all_real_size = 0
        for i in range(num):
            real_value = round(random.gauss(8, 1), 1)
            if real_value <= 0:
                continue
            iid = f'{uid}.{i}'
            offset = random.gauss(
                self.user_factor[uid]['greed'],
                self.user_factor[uid]['dissent_tolerance']
            )
            size = round(real_value + offset, 1)
            if size <= 0:
                size = 0.1
            icp.append({
                USER_KEY: uid,
                IID_KEY: iid,
                'title': f'this is {uid}-{i} icp.',
                'real_value': real_value,
                SIZE_KEY: size,
                CATEGORY_KEY: ascii_uppercase[random.randint(0, 25)]
            })
            all_size += size
            all_real_size += real_value
        return icp, all_size, all_real_size

    def do_pair(self):
        need_pair = []
        for x in self.icp.values():
            need_pair += x
        self.pair_ins.set(need_pair)
        self.paired = self.pair_ins.execute()
        return self.paired

    def do_vote(self, u, pv):
        if len(self.paired) == 0:
            raise NotYetPairedError
        for p in self.paired[u]:
            p[VOTED_KEY] = pv[p[PID_KEY]]
            self.vote_result.append(p)

    def auto_vote(self, u):
        ov = self.user_factor[u]['objective_voting']
        for p in self.paired[u]:
            pa_size = p[PAIR_KEY][0][SIZE_KEY]
            pb_size = p[PAIR_KEY][1][SIZE_KEY]
            ov_value = random.gauss(pa_size / pb_size, ov)
            if ov_value < 1:
                p[VOTED_KEY] = 0
            else:
                p[VOTED_KEY] = 1
            # if pa_size < pb_size:
            #     p[VOTED_KEY] = 0
            # else:
            #     p[VOTED_KEY] = 1
            self.vote_result.append(p)

    def all_auto_vote(self):
        if len(self.paired) == 0:
            raise NotYetPairedError
        self.vote_result = []
        for u in self.paired:
            self.auto_vote(u)
        self.all_vote_result[self.sid] = self.vote_result

    def _calculate_es(self):
        if len(self.vote_result) == 0:
            raise NotYetVotedError
        user_es = defaultdict(Decimal)
        for vr in self.vote_result:
            if vr[VOTED_KEY] == -1:
                raise NotYetVoteError
            for i, p in enumerate(vr[PAIR_KEY]):
                if i == vr[VOTED_KEY]:
                    user_es[p[USER_KEY]] += Decimal(str(p[SIZE_KEY]))
                else:
                    user_es[p[USER_KEY]] += Decimal('0')
        return user_es

    def stat_v2(self):
        user_es = self._calculate_es()
        not_good_user = {}
        for u in user_es:

            self.user_ei[u] = float(user_es[u]) / (self.user_size[u] * 2)
            if self.user_ei[u] == 0:
                self.user_ei[u] = 0.1
            if self.user_ei[u] < 0.5:
                print([self.user_factor[u]["reliability_factor"], self.user_ei[u]])
                self.user_factor[u]["reliability_factor"] = geometric_mean(
                    [self.user_factor[u]["reliability_factor"], self.user_ei[u]])
            else:
                self.user_factor[u]["reliability_factor"] = harmonic_mean(
                    [self.user_factor[u]["reliability_factor"], self.user_ei[u]])
            if self.user_ei[u] < 0.5:
                self.user_reward[u] = self.user_size[u] * self.user_factor[u]["reliability_factor"]
                if self.user_ei[u] < 0.25:
                    not_good_user[u] = self.user_factor[u]["reliability_factor"]
            else:
                self.user_reward[u] = self.user_size[u]

            self.user_factor[u]['dissent_tolerance'] = math.log(
                len(self.all_icp)) + self.all_user_factor[u][0]['dissent_tolerance']

            rc = random.gauss(self.user_reward[u]/self.user_size[u], self.user_factor[u]['dissent_tolerance'])
            if rc < 1:
                self.user_factor[u]['greed'] = self.user_factor[u]['greed'] * 0.9

            print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                  f'实际 size={self.user_real_size[u]}, '
                  f'申报了 {self.user_size[u]}, 最终得到了 '
                  f'{self.user_reward[u]}, 他本次的 EI 值为 {self.user_ei[u]}'
                  f'他的可靠系数为 {self.user_factor[u]["reliability_factor"]}, '
                  f'由于他具有异议容忍度, 他心理估计值为 {rc}, '
                  f'他的贪婪度为 {self.user_factor[u]["greed"]}')
        if len(not_good_user) > 0:
            sorted_not_good = sorted(not_good_user.keys(), key=lambda x: not_good_user[x])
            print(sorted_not_good)
            print(f'用户 id={sorted_not_good[0]} {self.users[sorted_not_good[0]][UNAME_KEY]}, 被淘汰了')
            del self.users[sorted_not_good[0]]
        else:
            print('没有用户被淘汰')

    def stat_v1(self):
        user_es = self._calculate_es()

        for u in user_es:

            self.user_ei[u] = float(user_es[u]) / (self.user_size[u] * 2)
            if self.user_ei[u] < 0.8:
                self.user_factor[u]["reliability_factor"] = geometric_mean(
                    [self.user_factor[u]["reliability_factor"], self.user_ei[u]])
            if self.user_factor[u]["reliability_factor"] < 0.8:
                self.user_reward[u] = self.user_size[u] * self.user_factor[u]["reliability_factor"]
            else:
                self.user_reward[u] = self.user_size[u]

            if self.user_real_size[u] > self.user_size[u]:
                # 奉献型人格
                if self.user_reward[u] < self.user_size[u]:
                    pt = self.user_size[u] - self.user_reward[u]
                    if pt >= self.user_factor[u]['reward_tolerance']:
                        print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                              f'本次具有"奉献型", 实际 size={self.user_real_size[u]}'
                              f'申报了 {self.user_size[u]}, 但只得到了 '
                              f'{self.user_reward[u]}, 他的容忍度为 {self.user_factor[u]["reward_tolerance"]} '
                              f'损失太大, 最终, 他选择了离开')
                        del self.users[u]
                    else:
                        self.user_factor[u]['reward_tolerance'] -= pt
                        self.user_factor[u]['dissent_tolerance'] = math.log(
                            len(self.all_icp)) + self.all_user_factor[u][0]['dissent_tolerance']
                        print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                              f'本次具有"奉献型", 实际 size={self.user_real_size[u]}'
                              f'申报了 {self.user_size[u]}, 但只得到了 '
                              f'{self.user_reward[u]}, 他愿意接受这次的损失'
                              f'他的容忍度只剩下 {self.user_factor[u]["reward_tolerance"]} '
                              f'可能下次再受损, 他就离开了')
                else:
                    self.user_factor[u]['dissent_tolerance'] = math.log(
                        len(self.all_icp)) + self.all_user_factor[u][0]['dissent_tolerance']
                    print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                          f'本次具有"奉献型", 实际 size={self.user_real_size[u]}'
                          f'申报了 {self.user_size[u]}, 最终得到了 '
                          f'{self.user_reward[u]}, 他在默默支持, 也得到了应得的. ')
            if self.user_real_size[u] <= self.user_size[u]:
                # 贪婪型人格
                if self.user_real_size[u] < self.user_reward[u] < self.user_size[u]:
                    # 自我相信: 凭本事贪到了
                    self.user_factor[u]['dissent_tolerance'] = math.log(
                        len(self.all_icp)) + self.all_user_factor[u][0]['dissent_tolerance']
                    print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                          f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                          f'申报了 {self.user_size[u]}, 最终得到了 '
                          f'{self.user_reward[u]}, 他贪的不多, 所以虽然没有全部拿到, '
                          f'但是, 他满意他的所得. ')
                elif self.user_reward[u] > self.user_size[u]:
                    # 根据 dt 判断, 1. 是不是贪多了, 下次少贪点, 2. 机会很大可以加大力度
                    rc = random.gauss(self.user_reward[u]/self.user_size[u], self.user_factor[u]['dissent_tolerance'])
                    if rc > 1:
                        # 1. 是不是贪多了, 下次少贪点
                        self.user_factor[u]['greed'] = self.user_factor[u]['greed'] * ((self.user_reward[u]/self.user_real_size[u]) - 1)
                        print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                              f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                              f'申报了 {self.user_size[u]}, 最终得到了 '
                              f'{self.user_reward[u]}, 他所得要高于自己的贡献,'
                              f'由于他具有异议容忍度, 他心理估计值为 {rc}, '
                              f'他过意不去, 觉得自己是不是贪多了, '
                              f'决定下次少贪点, 他的贪婪度修正为了 {self.user_factor[u]["greed"]}')
                    else:
                        # 2. 机会很大可以加大力度
                        self.user_factor[u]['greed'] = self.user_factor[u]['greed'] * 1.1
                        self.user_factor[u]['dissent_tolerance'] = math.log(
                            len(self.all_icp)) + self.all_user_factor[u][0]['dissent_tolerance']
                        print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                              f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                              f'申报了 {self.user_size[u]}, 最终得到了 '
                              f'{self.user_reward[u]}, 他所得要高于自己的贡献,'
                              f'由于他具有异议容忍度, 他心理估计值为 {rc}, '
                              f'他过意不去, 觉得自己是不是贪多了, '
                              f'决定下次少贪点, 他的贪婪度修正为了 {self.user_factor[u]["greed"]}')
                elif self.user_reward[u] == self.user_size[u]:
                    self.user_factor[u]['dissent_tolerance'] = math.log(
                        len(self.all_icp)) + self.all_user_factor[u][0]['dissent_tolerance']
                    print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                          f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                          f'申报了 {self.user_size[u]}, 最终得到了 '
                          f'{self.user_reward[u]}, 他很满意, 他贪到了他期望拿到的')
                else:
                    # 贪失败了, 根据 dt 判断, 1. 减少自己的贪婪值, 2. 这次运气不行
                    # 亏太多了, 那就离开
                    pt = self.user_real_size[u] - self.user_reward[u]
                    if pt >= self.user_factor[u]['reward_tolerance']:
                        print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                              f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                              f'申报了 {self.user_size[u]}, 最终得到了 '
                              f'{self.user_reward[u]}, 他贪失败了, 并且他觉得划不来, '
                              f'他的容忍度是 {self.user_factor[u]["reward_tolerance"]}, '
                              f'他选择离开(happy)')
                        del self.users[u]
                    else:
                        rc = random.gauss(self.user_reward[u]/self.user_size[u], self.user_factor[u]['dissent_tolerance'])
                        if rc > 1:
                            # 这次运气不行, 下次再试试
                            print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                                  f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                                  f'申报了 {self.user_size[u]}, 最终得到了 '
                                  f'{self.user_reward[u]}, 他贪失败了, '
                                  f'由于他具有异议容忍度, 他心理估计值为 {rc}, '
                                  f'他觉得这次只是个巧合, 所以他不打算收敛自己的贪婪, 他决定下次再试试')
                        else:
                            # 1. 减少自己的贪婪值
                            self.user_factor[u]['greed'] = self.user_factor[u]['greed'] * 0.9
                            print(f'用户 id={u} {self.users[u][UNAME_KEY]}, '
                                  f'本次具有"贪婪型", 实际 size={self.user_real_size[u]}'
                                  f'申报了 {self.user_size[u]}, 最终得到了 '
                                  f'{self.user_reward[u]}, 他贪失败了, '
                                  f'由于他具有异议容忍度, 他心理估计值为 {rc}, '
                                  f'他觉得或许是自己太过分了, 他调整自己的贪婪度为 {self.user_factor[u]["greed"]}')


def simula():
    # 设定1: 所有 size 单位价值相同, 都经过 pr review, 因此目标是每月 real_size 尽可能多
    # 设定2: 贪婪度 gd: 可变的, 贪婪的人会把 size 标的比实际工作时间大
    # 设定3: 异议容忍度 dt: 可变的, 会 log 型增加, 在乎团队异议的人会把 size 标的小一些, 并且会以 sin 的形式变幻贪婪
    # 设定4: 客观投票度 sv: 认为不变的, 投票越客观的人, 越可能会投给 (size - real_size) 偏差值小的人
    # 方案1.1: ICP 结算报酬: 每次 ICP 结算, 都是 ES * 可靠系数, 每个成员初始可靠系数为 1.
    # 方案1.2: 可靠系数 rf: EI 低可靠系数遍低, EI 高可靠系数高, 最高 1, EI 的几何平均值
    # 方案1.3: 报酬落差容忍度 rt: 当 ICP 结算低于 size 高于 real_size 时: 他可接受
    #       当 ICP 结算低于 size 且低于 real_size 时 如果超过了报酬落差容忍度, 他会离开,
    #       当 ICP 结算高于 size 时, 下次结算周期他的报酬落差容忍度会略有增加
    # 方案2: 现行方案, 固定值, 下次减半
    A = {'gd': 1, 'dt': 0.1, 'sv': 1, 'rt': 4} # 贪婪/爱面子/认真投票/可以接受一定损失
    B = {'gd': 1, 'dt': 1, 'sv': 1, 'rt': 4} # 贪婪/不在乎别人眼光/认真投票/可以接受一定损失
    C = {'gd': 0, 'dt': 0.1, 'sv': 1, 'rt': 4} # 不贪婪/爱面子/认真投票/可以接受一定损失
    D = {'gd': 0, 'dt': 0.1, 'sv': 1, 'rt': 2} # 不贪婪/爱面子/认真投票/可接受损失小
    E = {'gd': 1, 'dt': 0.1, 'sv': 1, 'rt': 2} # 贪婪/爱面子/认真投票/可接受损失小
    sim = GameSimulation([A, B, C, D, E])
    a = input('=========')
    t = input('v 1/2 ?')
    while a == '':
        sim.simula_icp('1')
        sim.do_pair()
        sim.all_auto_vote()
        if t == '1':
            sim.stat_v1()
        if t == '2':
            sim.stat_v2()
        print(sim.user_factor)
        a = input('=========')
    else:
        print(sim.all_user_reward)
        print(sim.all_user_ei)
        print(sim.all_user_factor)


def simula_terminal():
    c = 0
    sd = []
    while True:
        op = input('输入仿真 继续[c]/随机[r]/结束[e]: ')
        if op == '' or op == 'c':
            print(f'输入第 {c+1} 个人的信息')
            name = input('输入用户名: ')
            factor = input('输入系数(贪婪度/异议容忍度/主观投票度): ')
            greed, dissent_tolerance, objective_voting = (float(f.strip()) for f in factor.split('/'))
            icp_num = int(input('输入用户的 icp 数量: '))
            tmp = {
                USER_KEY: str(c),
                UNAME_KEY: name,
                GREED_KEY: greed,
                DISSENT_TOLERANCE_KEY: dissent_tolerance,
                SUBJECTIVE_VOTING_KEY: objective_voting,
                ICP_NUM_KEY: icp_num
            }
            c += 1
            sd.append(tmp)
        if op == 'r':
            c += 1
            sd.append({USER_KEY: str(c)})
        if op == 'e':
            break
    sim = GameSimulation(sd)
    print('生成: ')
    print('all size', sim.all_size)
    print(json.dumps(sim.data, indent=2))
    bp = input('开始配对? ')
    if bp == '' or bp == 'y':
        sim.do_pair()
        print('配对')
        print(json.dumps(sim.paired, indent=2))
        for u in sim.paired:
            if len(sim.paired[u]) == 0:
                continue
            bv = input(f'user={u} 是否自动投票? ')
            if bv == '' or bv == 'y':
                sim.auto_vote(u)
            else:
                pv = {}
                for v in sim.paired[u]:
                    print(f'0: uid={v[PAIR_KEY][0]["uid"]} real_value={v[PAIR_KEY][0]["real_value"]} size={v[PAIR_KEY][0]["size"]}')
                    print(f'1: uid={v[PAIR_KEY][1]["uid"]} real_value={v[PAIR_KEY][1]["real_value"]} size={v[PAIR_KEY][1]["size"]}')
                    vote = input('0 or 1 ? ')
                    pv[v[PID_KEY]] = int(vote)
                sim.do_vote(u, pv)
        print('投票结果')
        for sv in sim.vote_result:
            s = ''
            for i, v in enumerate(sv['pair']):
                if i == sv['voted']:
                    s += f'\033[7m uid={v["uid"]} real_value={v["real_value"]} size={v["size"]} \033[0m'
                else:
                    s += f' uid={v["uid"]} real_value={v["real_value"]} size={v["size"]} '
            print(sv['vote_uid'], s)
        print('ES 结果: ', sim.es)
        print('EI 结果: ', sim.ei)
    return sim


if __name__ == '__main__':
    simula()
