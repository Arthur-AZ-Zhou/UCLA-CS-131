from functools import reduce

def strip_characters(sentence, chars_to_remove):
    return "".join([char for char in sentence if char not in chars_to_remove])

def convert_to_decimal(bits):
    exponents = range(len(bits)-1, -1, -1)
    nums = [bit * (2 ** exp) for bit, exp in zip(bits, exponents)]
    return reduce(lambda acc, num: acc + num, nums)

def parse_csv(lines):
    return [(word, int(num)) for line in lines for word, num in [line.split(",")]]

def unique_chars(sentence):
    return {char for char in sentence}

def squares_dict(lower, upper):
    return {num: num ** 2 for num in range(lower, upper + 1)}

def main():
    print(strip_characters("Hello, world!", {"o", "h", "l"}))
    print(convert_to_decimal([1, 0, 1, 1, 0])) 
    print(convert_to_decimal([1, 0, 1]))
    print(parse_csv(["apple,8", "pear,24", "gooseberry,-2"]))
    print(unique_chars("happy"))
    print(squares_dict(1, 5))

main()