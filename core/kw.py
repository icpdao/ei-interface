zero_threshold = 0.00000001


def kw_algorithm(a: list, b: list, wf):
    a_attr = []
    b_attr = []
    for an in a:
        a_attr.append({'weight': 0, 'match': None, 'visit': False, 'd': an})
    for bn in b:
        b_attr.append({'weight': 0, 'match': None, 'visit': False, 'd': bn})

    matrix = []

    for ai, an in enumerate(a):
        max_weight = -1
        tmp_matrix = []
        for bi, bn in enumerate(b):
            w = wf(an, bn)
            tmp_matrix.append(w)
            if max_weight == -1 or max_weight < w:
                max_weight = w
        matrix.append(tmp_matrix)
        a_attr[ai]['weight'] = max_weight

    for ai, an in enumerate(a):
        while True:
            min_z = float('inf')
            for n in a_attr:
                n['visit'] = False
            for m in b_attr:
                m['visit'] = False
            dfs, min_z = kw_dfs(a_attr, b_attr, matrix, min_z, b, ai)
            if dfs:
                break
            for n in a_attr:
                if n['visit'] is True:
                    n['weight'] += -min_z

            for m in b_attr:
                if m['visit'] is True:
                    m['weight'] += min_z

    return [(at['d'], b_attr[at['match']]['d'], matrix[ai][at['match']]) for
            ai, at in enumerate(a_attr)]


def kw_dfs(a_attr, b_attr, matrix, min_z, b, i):
    match_list = []
    while True:
        a_attr[i]['visit'] = True
        for bi, bn in enumerate(b):
            if b_attr[bi]['visit'] is False:
                t = a_attr[i]['weight'] + b_attr[bi]['weight'] - matrix[i][bi]
                if abs(t) < zero_threshold:
                    b_attr[bi]['visit'] = True
                    match_list.append((i, bi))
                    if b_attr[bi].get('match') is None:
                        for i, j in match_list:
                            a_attr[i]['match'] = j
                            b_attr[j]['match'] = i
                        return True, min_z
                    else:
                        i = b_attr[bi]['match']
                        break
                else:
                    if t >= zero_threshold:
                        min_z = min(min_z, t)
        else:
            return False, min_z
