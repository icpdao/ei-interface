import json

from game.simulation import GameSimulation


def test_do_pair():
    sim = GameSimulation(3)
    print('gen data end')
    sim.do_pair()
    sim.do_vote()
    print(json.dumps(sim.vote_result, indent=4))
    print('es', json.dumps(sim.es, indent=4))
    print('ei', sim.ei)


def test_do_vote():
    assert False


def test_es():
    assert False


def test_ei():
    assert False
