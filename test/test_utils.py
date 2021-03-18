from core.utils import get_two_dimensional_list_remain_element, \
    get_stirling_list


def test_get_two_dimensional_list_remain_element():
    assert get_two_dimensional_list_remain_element(
        [[1,2,3], ['a', 'b', 'c'], ['d', 'e']], 1) == ['a', 'b', 'c', 'd', 'e']

def test_get_stirling_list():
    ret = get_stirling_list(['a'], 2)
    assert [x for x in ret] == [
        [
            ['a'], []
        ],
        [
            [], ['a']
        ]
    ]
    ret = get_stirling_list(['a', 'b'], 2)
    assert [x for x in ret] == [[['b', 'a'], []], [['a'], ['b']], [['b'], ['a']], [[], ['b', 'a']]]
    ret = get_stirling_list(['A', 'B', 'C', 'D'], 2)
    assert [x for x in ret] == [[['D', 'C', 'B', 'A'], []], [['C', 'B', 'A'], ['D']], [['D', 'B', 'A'], ['C']], [['B', 'A'], ['D', 'C']], [['D', 'C', 'A'], ['B']], [['C', 'A'], ['D', 'B']], [['D', 'A'], ['C', 'B']], [['A'], ['D', 'C', 'B']], [['D', 'C', 'B'], ['A']], [['C', 'B'], ['D', 'A']], [['D', 'B'], ['C', 'A']], [['B'], ['D', 'C', 'A']], [['D', 'C'], ['B', 'A']], [['C'], ['D', 'B', 'A']], [['D'], ['C', 'B', 'A']], [[], ['D', 'C', 'B', 'A']]]
