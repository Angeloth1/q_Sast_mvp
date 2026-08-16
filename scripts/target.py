from cryptography.hazmat.primitives.asymmetric import rsa


def gen_key():
    privateKey= rsa.generate_private_key(
        public_exponent=65537,
        key_size = 2048
    )
    print("RSA Key Generated")
    return privateKey
