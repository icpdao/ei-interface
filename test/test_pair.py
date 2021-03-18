from core.pair import Pair, IID_KEY, SIZE_KEY, USER_KEY, CATEGORY_KEY


def test_execute():
    ins = Pair()
    ins.set([
        {SIZE_KEY: 0.5, IID_KEY: '1', USER_KEY: 'Bob', CATEGORY_KEY: 'ICP_A'},
        {SIZE_KEY: 2, IID_KEY: '2', USER_KEY: 'Bob', CATEGORY_KEY: 'ICP_B'},
        {SIZE_KEY: 1, IID_KEY: '3', USER_KEY: 'Lily', CATEGORY_KEY: 'ICP_A'},
        {SIZE_KEY: 8, IID_KEY: '4', USER_KEY: 'Bob', CATEGORY_KEY: 'ICP_A'},
        {SIZE_KEY: 4, IID_KEY: '5', USER_KEY: 'Lily', CATEGORY_KEY: 'ICP_B'},
    ])
    ret = ins.execute()
    print(ret)
