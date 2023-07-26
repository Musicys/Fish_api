import time
import redis


class RedisLock:

    def __init__(self, expire=60, count=3, redis_conf=None):
        self.expire = expire
        self.count = count
        if not redis_conf:
            self.redis_client = redis.Redis('localhost', 6379)
        else:
            self.redis_client = redis.Redis(**redis_conf)

    def acquire(self, key):
        """获取锁 尝试三次没有就放弃"""

        count = self.count
        while count > 0:
            result = self.redis_client.setnx(key, time.time())
            if result:
                # 设置过期时间
                self.redis_client.expire(key, self.expire)
                return True
            else:
                # 等待一段时间后重新尝试获取锁
                time.sleep(0.1)
                count -= 1

    def release(self, key):
        """释放锁"""

        self.redis_client.delete(key)
