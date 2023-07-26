def must_true(f, exception: Exception):
    if not f:
        raise exception
    return f


def must_not_true(f, exception: Exception):
    if f:
        raise exception
    return f
