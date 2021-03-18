from itertools import repeat


def get_two_dimensional_list_remain_element(_list, i):
    ret = []
    for l in _list[i:]:
        ret += l
    return ret


def merge_two_list_by_same_sum(list1, list2):
    if len(list1) != len(list2):
        return []
    return list(map(lambda x, y: x + y, list1, list2))


def get_stirling_list(n: list, m: int) -> list:
    """
    Get Stirling Number Exhaustive list, dynamic programming algorithm
    state transition equation: D(n, m) = D(n[0], m) && D(n[1:], m)
    There is room for optimization
    :param n: to be divided
    :param m: numbers of heaps
    :return: stirling list
    """
    if len(n) == 1:
        for i in range(m):
            tmp = list(repeat([], m))
            tmp[i] = [n[0]]
            yield tmp
    else:
        for i, o in enumerate(get_stirling_list([n[0]], m)):
            for t in get_stirling_list(n[1:], m):
                yield merge_two_list_by_same_sum(t, o)


def get_full_stirling_list(n: list):
    ret = []
    lower = round(len(n) / 3) or 1
    upper = round(2 * len(n) / 3) or 1
    for i in range(lower, upper):
        ret += get_stirling_list(n, i)
    return ret
