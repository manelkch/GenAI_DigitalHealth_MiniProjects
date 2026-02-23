def is_odd(a_value, b_value):
    if a_value % 2 != 0 and b_value % 2 != 0:
        return True
    else:
        return False

if __name__ == '__main__':
    a_value = 0
    b_value = 10
    print(is_odd(a_value, b_value))