import json

from game.simulation import GameSimulation


def test_do_pair():
    sim = GameSimulation(3)
    print('gen data end')
    sim.do_pair()
    sim.do_vote()
    for sv in sim.vote_result:
        s = ''
        for i, v in enumerate(sv['pair']):
            if i == sv['voted']:
                s += f'\033[7m uid={v["uid"]} real_value={v["real_value"]} size={v["size"]} \033[0m'
            else:
                s += f' uid={v["uid"]} real_value={v["real_value"]} size={v["size"]} '
        print(sv['vote_uid'], s)
    print('es', sim.es)
    print('ei', sim.ei)


def test_do_vote():
    assert False


def test_es():
    assert False


def test_ei():
    assert False
