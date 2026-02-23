def generate_even_numbers(upper_limit):
    return [num for num in range(2, upper_limit+1, 2)]

if __name__ == '__main__':
    print(generate_even_numbers(100))