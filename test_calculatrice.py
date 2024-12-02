# test_calculatrice.py
from calculatrice import addition, soustraction

def test_addition():
    assert addition(2, 3) == 9
    assert addition(-1, 1) == 0
    assert addition(0, 0) == 0

def test_soustraction():
    assert soustraction(5, 2) == 3
    assert soustraction(0, 0) == 0
    assert soustraction(-1, -1) == 0