import asyncio
import json
import random
from collections import defaultdict
from decimal import *
from math import sqrt
from faker import Faker

getcontext().prec = 12
faker_cn = Faker('zh_CN')


class UniEntity:
    pair_name = "X/ETH"
    p1_value = Decimal(0)
    p2_value = Decimal(0)
    pound_pool = {"p1": Decimal(0), "p2": Decimal(0)}
    pound_percent = Decimal('0.3') * Decimal('0.01')
    liquidity_account_book = defaultdict(
        lambda: {"p1": Decimal(0), "p2": Decimal(0), "lp": Decimal(0)}
    )
    total_lp = Decimal(0)

    def __init__(self, init_user, init_p1, init_p2):
        """初始质押, 添加交易对"""
        self.p1_value = Decimal(str(init_p1))
        self.p2_value = Decimal(str(init_p2))
        init_lp = Decimal(str(sqrt(self.k)))
        self.liquidity_account_book[init_user] = {
            "p1": self.p1_value, "p2": self.p2_value, "lp": init_lp
        }
        self.total_lp += init_lp

    def trans(self, p1=None, p2=None):
        """交易"""
        if (p1 is None and p2 is None) or (p1 is not None and p2 is not None):
            raise ValueError
        if p1 is not None:
            return self._trans_p1(p1)
        if p2 is not None:
            return self._trans_p2(p2)

    def _allot_pound(self, key, value):
        self.pound_pool[key] += value

    def _trans_p1(self, p1):
        p1 = Decimal(str(p1))
        pound_value = p1 * self.pound_percent
        p1 = p1 - pound_value
        self._allot_pound('p1', pound_value)
        current_k = self.k
        self.p1_value += p1
        current_p2 = self.p2_value
        obtain_p2 = current_p2 - (current_k / self.p1_value)
        self.p2_value -= obtain_p2
        return {"p2": obtain_p2}

    def _trans_p2(self, p2):
        p2 = Decimal(str(p2))
        pound_value = p2 * self.pound_percent
        p2 = p2 - pound_value
        self._allot_pound('p2', pound_value)
        current_k = self.k
        self.p2_value += p2
        current_p1 = self.p1_value
        obtain_p1 = current_p1 - (current_k / self.p2_value)
        self.p1_value -= obtain_p1
        return {"p1": obtain_p1}

    def add_liquidity(self, user, p1, p2):
        """质押增加流动性"""
        p1 = Decimal(str(p1))
        p2 = Decimal(str(p2))
        if abs((p2 * self.p1_value) - (p1 * self.p2_value)) > Decimal('0.1'):
            raise ValueError((p2, p1, self.p2_value, self.p1_value, (p1 * self.p2_value) - (p2 * self.p1_value)))
        self.liquidity_account_book[user]['p1'] += p1
        self.liquidity_account_book[user]['p2'] += p2

        self._lp_reward(user, (p1 / self.p1_value))

        self.p1_value += p1
        self.p2_value += p2

    def _lp_reward(self, user, p):
        obtain_lp = p * self.total_lp
        self.liquidity_account_book[user]['lp'] += obtain_lp
        print('=== total lp add ===\n', {
            'pre': self.total_lp, 'next': self.total_lp + obtain_lp, 'p': p})
        self.total_lp += obtain_lp
        print('=== lp ===\n', {
            'user': user, 'lp': f'{self.liquidity_account_book[user]}'})

    def redeem(self, user):
        """赎回"""
        origin = self.liquidity_account_book[user]
        if origin['lp'] <= Decimal(0):
            raise ValueError((user, origin))
        earn_p1 = (origin['lp'] / self.total_lp) * self.pound_pool['p1']
        earn_p2 = (origin['lp'] / self.total_lp) * self.pound_pool['p2']
        redeem_p1 = (origin['lp'] / self.total_lp) * self.p1_value
        redeem_p2 = (origin['lp'] / self.total_lp) * self.p2_value

        self.pound_pool['p1'] -= earn_p1
        self.pound_pool['p2'] -= earn_p2

        self.p1_value -= redeem_p1
        self.p2_value -= redeem_p2
        self.total_lp -= origin['lp']

        self.liquidity_account_book[user] = {
            "p1": Decimal(0), "p2": Decimal(0), "lp": Decimal(0)}

        redeem = {
            'p1': redeem_p1 + earn_p1, 'p2': redeem_p2 + earn_p2,
        }
        return redeem, origin

    @property
    def k(self):
        return self.p1_value * self.p2_value


class SushiEntity(UniEntity):
    def __init__(self, init_user, init_p1, init_p2, staking_percent, sushi=0, sushi_mining=100):
        super().__init__(init_user, init_p1, init_p2)
        self.sushi_percent = (Decimal('0.05') * Decimal('0.01')) / self.pound_percent
        self.sushi_account_book = defaultdict(lambda: Decimal(0))
        self.total_sushi = Decimal(str(sushi))  # 最开始的 sushi 币
        self.current_sushi = self.total_sushi
        self.sushi_mining = sushi_mining
        self.sushi_market_value = {"p1": Decimal(0), "p2": Decimal(0)}
        self.pound_pool = {"p1": Decimal(0), "p2": Decimal(0), 'sushi': {"p1": Decimal(0), "p2": Decimal(0)}}
        # staking percent
        self.stacking_lp = defaultdict(lambda: Decimal(0))
        self.staking_percent = Decimal(str(staking_percent))

    def mining(self):
        """假设所有的挖矿产生的 sushi 币, 都分配给了这个矿池"""
        print('=== mining sushi ===\n', {
            'pre': self.total_sushi,
            'next': self.sushi_mining + self.total_sushi
        })
        self.total_sushi += self.sushi_mining
        self.current_sushi += self.sushi_mining

    def _allot_pound(self, key, value):
        """0.05% 的交易费提供到 sushi 的市价"""
        self.pound_pool['sushi'][key] += self.sushi_percent * value
        self.pound_pool[key] += value * (1 - self.sushi_percent)
        self.add_sushi_market_value(key, self.sushi_percent * value)

    def add_sushi_market_value(self, key, value):
        """模拟 sushi 市值增加, 即外部花 "钱" (p1 or p2) 购买"""
        self.sushi_market_value[key] += Decimal(str(value))

    def _lp_reward(self, user, p):
        obtain_lp = p * self.total_lp
        self.liquidity_account_book[user]['lp'] += obtain_lp
        print('=== total lp add ===\n', {
            'user': user, 'pre': self.total_lp,
            'next': self.total_lp + obtain_lp,
            'p': p, 'obtain_lp': self.liquidity_account_book[user]['lp']})
        self.total_lp += obtain_lp
        # 质押获得 sushi 币
        self.sushi_account_book[user] += p * self.current_sushi
        self.current_sushi = (Decimal('1') - p) * self.current_sushi

    def farming(self, user):
        """质押所有 lp 获取 sushi 币"""
        amount = self.liquidity_account_book[user]['lp']
        self.stacking_lp[user] += amount
        self.liquidity_account_book[user]['lp'] -= amount
        self.sushi_account_book[user] += self.staking_percent * amount

    def redeem(self, user):
        amount = self.stacking_lp[user]
        self.stacking_lp[user] -= amount
        self.liquidity_account_book[user]['lp'] += amount
        return super(SushiEntity, self).redeem(user)

    def exchange_sushi(self, user):
        """
        用户查看自己的 sushi 价值
        已有的 sushi 币能换成 p1, p2 的数量, 也就是计算收益
        """
        amount = self.sushi_account_book[user]
        price_p1 = self.sushi_market_value['p1'] / self.total_sushi
        price_p2 = self.sushi_market_value['p2'] / self.total_sushi
        exchange_p1 = amount * price_p1
        exchange_p2 = amount * price_p2
        return {'p1': exchange_p1, 'p2': exchange_p2}

    def sale_all(self, user):
        exchange = self.exchange_sushi(user)
        self.add_sushi_market_value('p1', -exchange['p1'])
        self.add_sushi_market_value('p2', -exchange['p2'])


async def mn_uni_add_lp(uni, user):
    random_p = Decimal(str(round(random.uniform(0, 1), 3)))
    uni.add_liquidity(user, random_p * uni.p1_value, random_p * uni.p2_value)


async def mn_uni_trans(uni):
    for ti in range(random.randint(2, 5)):
        trans_k = random.choice(['p1', 'p2'])
        trans_v = round(abs(random.gauss(5, 0.5)), 2)
        earn = uni.trans(**{trans_k: trans_v})
        print('=== trans info ===\n', {'ti': ti, 'pay': f'{trans_k}-{trans_v}', 'earn': f'{earn}'})


async def mn_uni_main():
    uni = UniEntity("a", 30, 1)
    users = [faker_cn.name() for x in range(9)]
    max_count = 10
    i = 0
    while True:
        if i >= max_count:
            break
        i += 1
        random_u = random.choice(users)
        await asyncio.gather(
            mn_uni_add_lp(uni, random_u),
            mn_uni_trans(uni),
        )


async def mn_sushi_run(sushi):
    users = [faker_cn.name() for x in range(9)]
    max_count = 10
    i = 0
    while True:
        if i >= max_count:
            break
        i += 1
        random_u = random.choice(users)
        random_u2 = random.choice(users)
        await asyncio.gather(
            mn_uni_add_lp(sushi, random_u),
            mn_uni_trans(sushi),
            mn_sushi_outside_by_sushi(sushi),
            # mn_sushi_farming(sushi, random_u2)
        )


async def mn_sushi_usd_run(sushi):
    init_assets = {
        faker_cn.name(): {'p1': Decimal(0), 'p2': Decimal(100)} for x in range(9)
    }
    earn_p1 = {}
    for u in init_assets:
        asset = init_assets[u]
        buy_p1_percent = Decimal(str(round(random.uniform(0, 1), 2)))
        p1 = sushi.trans(p2=asset['p2'] * buy_p1_percent)
        asset['p2'] -= asset['p2'] * buy_p1_percent
        asset['p1'] += p1['p1']
        lp_p2 = asset['p1'] * sushi.p2_value / sushi.p1_value
        if lp_p2 < asset['p2']:
            lp_p1 = asset['p2'] * sushi.p1_value / sushi.p2_value
            sushi.add_liquidity(u, lp_p1, asset['p2'])
            earn_p1[u] = asset['p1'] - lp_p1
        else:
            sushi.add_liquidity(u, asset['p1'], lp_p2)
            earn_p2 = asset['p2'] - lp_p2
            earn_p1[u] = sushi.trans(p2=earn_p2)['p1']
        sushi.farming(u)
    earn_p2 = {}
    for u in init_assets:
        redeem, origin = sushi.redeem(u)
        earn_p2[u] = sushi.trans(
            p1=sushi.sushi_account_book[u]+redeem['p1']+earn_p1[u])['p2']
    print(init_assets)
    print(earn_p2)


async def mn_sushi_mining(sushi):
    while True:
        await asyncio.sleep(0.0002)
        sushi.mining()


async def mn_sushi_outside_by_sushi(sushi):
    for x in range(random.randint(2, 5)):
        outside_k = random.choice(['p1', 'p2'])
        outside_v = round(abs(random.gauss(30, 0.5)), 2)
        sushi.add_sushi_market_value(outside_k, outside_v)


async def mn_sushi_farming(sushi, user):
    if sushi.liquidity_account_book[user]['lp'] != Decimal(0):
        sushi.farming(user)
        print('=== exchange sushi ===\n', sushi.exchange_sushi(user))


async def mn_sushi_main():
    sushi = SushiEntity('b', 30, 1, 200, 100)
    run_task = asyncio.create_task(mn_sushi_run(sushi))
    mining_task = asyncio.create_task(mn_sushi_mining(sushi))
    done, pending = await asyncio.wait(
        {run_task, mining_task}, return_when=asyncio.FIRST_COMPLETED)
    if run_task in done:
        mining_task.cancel()
        print('========')
        print(sushi.sushi_market_value)
        print(dict(sushi.sushi_account_book))
        for u in sushi.sushi_account_book:
            print(f'{u} 未赎回时持有 sushi 币值:', sushi.exchange_sushi(u))
        for u in sushi.sushi_account_book:
            print(f'{u} 赎回收益:', sushi.redeem(u))
            print(f'{u} 持有 sushi 币值:', sushi.exchange_sushi(u))
            sushi.sale_all(u)
            print(f'{u} 抛售所有 sushi')


async def mn_sushi_usd_main():
    sushi = SushiEntity('b', 1000, 1000, 2)
    run_task = asyncio.create_task(mn_sushi_usd_run(sushi))
    mining_task = asyncio.create_task(mn_sushi_mining(sushi))
    done, pending = await asyncio.wait(
        {run_task, mining_task}, return_when=asyncio.FIRST_COMPLETED)
    if run_task in done:
        mining_task.cancel()

if __name__ == '__main__':
    # asyncio.run(mn_uni_main())

    # asyncio.run(mn_sushi_main()

    asyncio.run(mn_sushi_usd_main())
