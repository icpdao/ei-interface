import json

from game.simulation import GameSimulation, simula_terminal


def test_do_pair():
    sim = GameSimulation(3)
    print('gen data end', sim.data)
    sim.do_pair()
    sim.do_vote()
    print('es', sim.es)
    print('ei', sim.ei)


def test_do_vote():
    assert False


def test_es():
    assert False


def test_ei():
    assert False
