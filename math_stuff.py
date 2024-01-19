import random


def lcm(a, b):
    x, y = a, b
    while y:
        x, y = y, x % y
    return abs(a * b) // x


def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    else:
        d, x, y = extended_gcd(b, a % b)
        return d, y, x - y * (a // b)


def modular_inverse(a, m):
    d, x, y = extended_gcd(a, m)
    if d != 1:
        raise ValueError("Inverse does not exist")
    return x % m


def is_probably_prime(n, k=5):
    if n <= 1:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False  # Not prime

    return True  # Probably prime


def generate_large_prime(bit_length):
    while True:
        candidate = random.getrandbits(bit_length) | (1 << (bit_length - 1)) | 1
        if is_probably_prime(candidate):
            return candidate


def generate_keys(bit_length):
    _key_1 = generate_large_prime(bit_length)
    _key_2 = generate_large_prime(bit_length)
    while _key_1 == _key_2:
        _key_2 = generate_large_prime(bit_length)
    n = _key_1 * _key_2
    low = lcm(_key_1 - 1, _key_2 - 1)
    e = generate_large_prime(bit_length // 2)
    while e == _key_1 or e == _key_2:
        e = generate_large_prime(bit_length // 2)
    d = modular_inverse(e, low)
    print(f'\nn = {n}\nd (private) = {d}\ne (public) = {e}\n')
    return n, d, e
