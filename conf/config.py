# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

from webconfig import *

# 服务地址
HOST = '0.0.0.0'

# 服务端口
PORT = 9900

# 协议
PROTO = 'http'

# 工作模式:  simple/gevent
WORK_MODE = 'gevent'

# 服务名称，也是服务目录名
MYNAME = os.path.basename(HOME)
os.environ['MYNAME'] = MYNAME

# 服务名称上报时间间隔，单位秒
NAME_REPORT_TIME = 10

# 命名服务的地址
NAMECENTER = os.environ.get('NAMECENTER')

# IDC标识
IDC = os.environ.get('IDC')

# 调试模式: True/False
# 生产环境必须为False
DEBUG = False

# 日志文件配置
if DEBUG:
    LOGFILE = 'stdout'
else:
    # LOGFILE = os.path.join(HOME, 'log/project.log')
    LOGFILE = 'stdout'

REDIS_CONF = {
    'host': '127.0.0.1',
    'port': 6379,
    'password': '',
}

SESSION_EXPIRE = 3600 * 72

# 数据库配置
DATABASE = {
    'fish': {
        'engine': 'pymysql',
        'passwd': 'sql@jianjin',
        'charset': 'utf8',
        'port': 3306,
        'idle_timeout': 60,
        'host': 'bjcore01.vanshin.fun',
        'user': 'jianjin',
        'db': 'fish',
        'port': 3306,
        'conn': 50
    },
}


# cookie
COOKIE_CONFIG = {
    'max_age': 10000,
    # 'domain': '.uyu.com',
    # 'domain': '127.0.0.1',
}
