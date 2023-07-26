# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :
import os
import sys

HOME = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HOME), 'conf'))

from mtools.base import loader

if __name__ == '__main__':
    loader.loadconf_argv(HOME)
else:
    loader.loadconf(HOME)

import config

if config.WORK_MODE == 'gevent':
    from gevent import monkey;
    monkey.patch_all()

from mtools.base import logger

# 导入服务日志
log = logger.install(getattr(config, 'LOGFILE', 'stdout'))

from mtools.web import core
from mtools.web import runner
from mtools.base import redispool

redispool.patch()

import datetime

config.starttime = str(datetime.datetime.now())[:19]

# 导入WEB URLS
import urls

config.URLS = urls

# 注册中间件
app = core.WebApplication(config)

if __name__ == '__main__':
    # 导入自定义服务端口
    if len(sys.argv) > 2:
        config.PORT = int(sys.argv[2])

    log.info('WORK_MODE: %s', config.WORK_MODE)
    if config.WORK_MODE == 'gevent':
        import gevent
        runner.run_gevent(app, host=config.HOST, port=config.PORT)
    else:
        log.error('config.WORK_MODE must use simple/gevent !!!')
