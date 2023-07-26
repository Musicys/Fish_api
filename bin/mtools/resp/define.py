CONFIG_STATES = (CONF_OPEN, CONF_CLOSE) = (1, 2)


# 2开头的错误代码第二位代表错误等级
# 0. 严重错误; 1. 普通错误; 2. 规则错误; 3. 一般信息; 4. 未知错误
# 3 开头代表业务错误
# 31XX 代表用户信息相关错误
OK = "0000"
STOREDEVICEERR = "1010"
DBERR = "2000"
THIRDERR = "2001"
SESSIONERR = "2002"
DATAERR = "2003"
IOERR = "2004"
LOGINERR = "2100"
PARAMERR = "2101"
USERERR = "2102"
ROLEERR = "2103"
PWDERR = "2104"
VCODERROR = "2105"
PERMERR = "2106"
BEENBOUND = "2107"
UNBOUNDED = "2108"
CROSSERR = "2109"
NEVERREPEAT = "2110"
NOASSOCIATED = "2111"
NODEVICE = "2112"
REQERR = "2200"
IPERR = "2201"
MACERR = "2202"
NODATA = "2300"
DATAEXIST = "2301"
UNKOWNERR = "2400"
HTTPRESULTERR = "2501"
HTTPCALLERR = "2501"

# 用户信息相关错误
NOUSER = '3100'
OPENUSER_UNBIND = '3101'
COMLETE_USERINFO = '3102'
WXTOKEN_OVERDUE = '3103'

error_map = {
    OK: u"成功",
    DBERR: u"数据库查询错误",
    STOREDEVICEERR: "门店设备不匹配",
    THIRDERR: u"第三方系统错误",
    SESSIONERR: u"用户未登录",
    DATAERR: u"数据错误",
    IOERR: u"文件读写错误",
    LOGINERR: u"用户登录失败",
    PARAMERR: u"参数错误",
    USERERR: u"用户不存在或未激活",
    ROLEERR: u"用户身份错误",
    PWDERR: u"密码错误",
    VCODERROR: u"验证码错误",
    REQERR: u"非法请求或请求次数受限",
    IPERR: u"IP受限",
    MACERR: u"MAC校验失败",
    NODATA: u"无数据",
    DATAEXIST: u"数据已存在",
    UNKOWNERR: u"未知错误",
    PERMERR: u"用户无权限访问",
    BEENBOUND: u"设备已被绑定",
    UNBOUNDED: u"用户未绑定设备",
    CROSSERR: u"数据越界",
    NEVERREPEAT: u"不能重复",
    NOASSOCIATED: u"未关联",
    NODEVICE: u"设备不存在",

    NOUSER: '用户不存在',
    OPENUSER_UNBIND: '未绑定',
    COMLETE_USERINFO: '用户信息不完善',
    WXTOKEN_OVERDUE: '微信token不存在或已过期',
}


def get_errmsg(code):
    return error_map.get(code, "未知错误")

# 默认数据库
DEFAULT_DATABASE = "fish"


DT_FMT = '%Y-%m-%d'
DTM_FMT = '%Y-%m-%d %H:%M:%S'
DTMF_FMT = '%Y-%m-%d %H:%M:%S,%f'


