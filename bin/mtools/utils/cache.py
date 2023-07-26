'''缓存模块'''

import time
import redis
import gevent
import logging
import threading

log = logging.getLogger()


class CacheItem(object):

    name = None
    expired_time = None # second


    def __init__(self, name, redis_conf=None, ttl=300, gasync=True):
        self.name = name
        self._data = {}
        self.ttl = ttl
        # gevent 异步模式
        self.gasync = gasync
        # redis配置
        if not redis_conf:
            self.redis = redis.Redis('127.0.0.1', 6379)
        else:
            self.redis = redis.Redis(**redis_conf)

    def format_key(self, tag):
        return f'_remote_pay_{self.name}_{tag}_cache_'

    def get_store(self, key):

        key = str(key)

        data_name = self.format_key(key[-1])

        data_dict = getattr(self, data_name, None)
        if not data_dict:
            setattr(self, data_name, {})
        return getattr(self, data_name)


    def get(self, key):

        key = str(key)

        cache_key = self.format_key(key[-1])
        utime_key = f'{key}_update_time'

        now = int(time.time())

        local_store = self.get_store(key)

        redis_update_time = int(self.redis.hget(cache_key, utime_key) or 0)

        # redis更新时间不存在 = redis值不存在
        if not redis_update_time or redis_update_time < (now - self.ttl):
            value = self.getter(key)
            self.redis.hset(cache_key, key, self.dumps(value))
            self.redis.hset(cache_key, utime_key, now)
            local_store[key] = value
            local_store[utime_key] = now

        if not local_store.get(utime_key) or local_store[utime_key] < redis_update_time:
            value = self.redis.hget(cache_key, key)
            utime = self.redis.hget(cache_key, utime_key)
            local_store[key] = self.loads(value)
            local_store[utime_key] = int(utime)

        return local_store[key]

    def set(self, key, value):

        key = str(key)

        cache_key = self.format_key(key[-1])
        utime_key = f'{key}_update_time'

        local_store = self.get_store(key)

        # 清楚缓存
        local_store[key] = None
        local_store[utime_key] = 0
        self.redis.hset(cache_key, key, '')
        self.redis.hset(cache_key, utime_key, 0)

        # 更新数据库
        self.setter(key, value)

        self.delay_clear_redis(key)

    def clear_redis(self, key, is_delay=False):
        if is_delay:
            if self.gasync:
                gevent.sleep(1)
            else:
                time.sleep(1)

        cache_key = self.format_key(key[-1])
        utime_key = f'{key}_update_time'

        local_store = self.get_store(key)
        local_store[key] = None
        local_store[utime_key] = 0
        self.redis.hset(cache_key, key, '')
        self.redis.hset(cache_key, utime_key, 0)


    def delay_clear_redis(self, key):
        t = threading.Thread(target=self.clear_redis, args=(key, True))
        t.start()


    def getter(self, key):
        pass

    def setter(self, key, value):
        pass

    def loads(self, value):
        return value

    def dumps(self, value):
        return value

import json
class TestC(CacheItem):

    def setter(self, key, value):
        self.redis.set(key, value)
        print(f'setter {key} {value}')

    def getter(self, key):
        self.redis.get(key)
        print(f'getter {key}')

    def dumps(self, value):
        return json.dumps(value)

    def loads(self, value):
        return json.loads(value)



if __name__ == '__main__':


    tc = TestC('test', ttl=2)

    tc.set(123, 'kkkkkkkkdfadfasdf')
    tc.get(123)
    tc.get(223)



