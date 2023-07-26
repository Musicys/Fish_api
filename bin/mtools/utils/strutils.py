import base64
import hashlib
import random
import string
import uuid
from urllib.parse import urlencode, urlparse, parse_qs


def md5(plaintext):
    ret = hashlib.md5()
    ret.update(bytes(plaintext, encoding='utf-8'))
    return ret.hexdigest()


def base64encoder(plaintext):
    return base64.b64encode(bytes(plaintext, encoding='utf-8'))


def get_uid():
    return base64.b32encode(uuid.uuid4().bytes).decode('utf-8').strip('=')


def add_url_params(url, params):
    old_url = urlparse(url)
    query = parse_qs(old_url.query)
    query.update(params)
    return old_url._replace(query=urlencode(query, doseq=True)).geturl()


def random_str(k, choices=string.ascii_lowercase + string.digits):
    return ''.join(random.choices(choices, k=k))


def compare(str1: str, str2: str) -> bool:
    if len(str1) != len(str2):
        return False
    result = 0
    for x, y in zip(str1, str2):
        result |= ord(x) ^ ord(y)
    return result == 0


def crypt_str(raw, salt=None):
    try:
        import crypt
    except ImportError:
        raise ValueError('"crypt" password algorithm not supported in this environment')
    return crypt.crypt(raw, salt)


def md5_str(raw, salt=None):
    return hashlib.md5(((salt or '') + raw).encode('utf-8')).hexdigest()


def sha1_str(raw, salt=None):
    return hashlib.sha1(((salt or '') + raw).encode('utf-8')).hexdigest()


hash_map = {
    'crypt': crypt_str,
    'md5': md5_str,
    'sha1': sha1_str,
}


def hash_str(raw, salt='', algo='sha1'):
    if algo in hash_map:
        return hash_map[algo](raw, salt)
    raise ValueError('Got unknown algorithm type .')
