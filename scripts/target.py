from cryptography.hazmat.primitives.asymmetric import rsa


def case_1():
    privateKey= rsa.generate_private_key(
        public_exponent= 65537,
        key_size = 2048
    )
    print("case_1: ok..."'\n')
    return privateKey

def case_2():
    privateKey= rsa.generate_private_key(
        key_size = 2048,
        public_exponent= 65537
    )
    print("case_2: ok..."'\n')
    return privateKey

def case_3():
    privateKey= rsa.generate_private_key(
        65537,
        key_size = 8192
    )
    print("case_3: ok..."'\n')
    return privateKey

def case_4():
    privateKey= rsa.generate_private_key(
        65537,
        4096
    )
    print("case_4: ok..."'\n')
    return privateKey

def case_5():
    KEY_SIZE = 2048
    privateKey= rsa.generate_private_key(
        key_size = KEY_SIZE,
        public_exponent= 65537
    )
    print("case_5: ok..."'\n')
    return privateKey