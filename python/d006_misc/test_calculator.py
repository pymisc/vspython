# test_calculator.py
# from .calculator import add_numbers

# def test_add_numbers():
#     # Test that 2 + 3 equals 5
#     assert add_numbers(2, 3) == 5
    
#     # Test that -1 + 1 equals 0
#     assert add_numbers(-1, 1) == 0

# test_calculator.py
from python.d006_misc.calculator import add_numbers

def test_add_numbers():
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0