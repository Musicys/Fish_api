from collections import defaultdict


def with_class_cache(func):
    """类缓存"""

    def _(self, *args, **kw):
        key = gen_key(args, kw)
        if not getattr(self, '_class_cache', None):
            self._class_cache = defaultdict(dict)

        if key in self._class_cache[func.__name__]:
            return self._class_cache[func.__name__][key]

        ret = func(self, *args, **kw)
        self._class_cache[func.__name__][key] = ret
        return ret

    return _


def gen_key(args, kw):
    """生成对应的key"""
    params = list(map(str, args or []))
    params.extend(f'{k}:{v}' for k, v in (kw or {}).items())
    return f'{"::".join(params)}'


def test():
    class A:
        @with_class_cache
        def yyk(self):
            print('doing')
            return 'yyk'

    a1 = A()
    print('do', a1.yyk())
    print('from cache', a1.yyk())

    a2 = A()
    print('empty', getattr(a2, '_cache_data', None))
    print(a2.yyk())
    print('data', getattr(a2, '_cache_data', None))


if __name__ == '__main__':
    test()
