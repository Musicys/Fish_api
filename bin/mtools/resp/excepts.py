
from mtools.base.excepts import MethodFail
from mtools.resp import define


class DevplatException(MethodFail):

    def __init__(self, respmsg='', respcd=define.PARAMERR, data=None):
        self.respmsg = respmsg
        self.respcd = getattr(self, 'respcd', respcd)
        self.data = data
        super(DevplatException, self).__init__(int(self.respcd), {
            'respmsg': respmsg,
            'data': data
        })

    def __str__(self):
        return '[code:%s] respmsg:%s' % (self.respcd, self.respmsg)


class LoginError(DevplatException):
    respcd = define.LOGINERR


class SessionError(DevplatException):
    respcd = define.SESSIONERR


class ParamError(DevplatException):
    respcd = define.PARAMERR


class ThirdError(DevplatException):
    respcd = define.THIRDERR


class DBError(DevplatException):
    respcd = define.DBERR


class CacheError(DevplatException):
    respcd = define.DATAERR


class ReqError(DevplatException):
    respcd = define.REQERR


class UserError(DevplatException):
    respcd = define.USERERR


class RoleError(DevplatException):
    respcd = define.ROLEERR


class MacError(DevplatException):
    respcd = define.MACERR


class HttpResultError(DevplatException):
    respcd = define.HTTPRESULTERR


class HttpCallError(DevplatException):
    respcd = define.HTTPCALLERR
