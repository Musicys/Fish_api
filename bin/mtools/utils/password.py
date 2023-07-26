from mtools.utils.strutils import random_str, compare, hash_str


def enc_passwd(password, algo='sha1'):
    salt = random_str(5)
    return '%s$%s$%s' % (algo, salt, hash_str(password, salt, algo))


def check(password, enc_password):
    algo, salt, hsh = enc_password.split('$')
    return compare(hsh, hash_str(password, salt, algo))


if __name__ == '__main__':
    print(check('768c1c687efe184ae6dd2420710b8799', 'sha1$1qaao$262b376497c3a7e865d9f3594dec3efe51901b77'))
    # for algo in ('crypt', 'md5', 'sha1'):
    #     enc_pwd = enc_passwd('123456', algo)
    #     print(enc_pwd)
    #     print(check('123456', enc_pwd))
