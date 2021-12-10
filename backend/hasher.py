import hashlib
import random
import string


def get_random_string(length=12):
    # return os.urandom(12) # TEST get random bytes string
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def hash_psw(password: str, salt: str = None):
    if salt is None:
        salt = get_random_string()
    enc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f'{salt}${enc.hex()}'


def validate(password: str, hashed_password: str):
    salt, _ = hashed_password.split("$")
    return hash_psw(password, salt) == hashed_password
