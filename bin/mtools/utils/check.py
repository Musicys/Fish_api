import sys
import logging
import traceback

from mtools.web.validator import Validator
from mtools.resp import define, error, success, excepts
from mtools.resp.excepts import DevplatException
from mtools.utils.tools import get_fn, to_list
from mtools.resp.excepts import SessionError
from mtools.utils.asserts import must_true


log = logging.getLogger()

def check_must(func):
    def _(self, *args, **kw):
        fields = getattr(self, '_check_fields', [])
        wrap_fn = getattr(self, '_wrap_check_fields', None)
        if wrap_fn:
            fields = wrap_fn(fields)

        self.validator = Validator(fields)
        ret = self.validator.verify(self.req.input(True))
        if ret:
            raise excepts.ParamError('validator error:' + ','.join(ret))
        self.data = self.validator.data
        log.debug(f'self.data={self.data}')

        return func(self, *args, **kw)

    return _

def check(fns=None):
    def _(func):
        def __(self, *args, **kwargs):
            respcd, respmsg, respdata = define.OK, '', None
            deco_funcs = []
            try:
                del_func = func
                deco_funcs.extend(to_list(fns or []))
                for f in deco_funcs[::-1]:
                    if callable(f):
                        del_func = f(del_func)
                    else:
                        fn = get_fn(sys.modules[__name__], 'check_' + f)
                        if fn:
                            del_func = fn(del_func)

                return del_func(self, *args, **kwargs)
            except DevplatException as e:
                if e.respcd != define.OK:
                    log.warning(traceback.format_exc())
                respcd, respmsg, respdata = e.respcd, e.respmsg, e.data
                fn = getattr(self, '_on_exception', None)
                if fn:
                    fn(e)
            except Exception:
                log.warning(traceback.format_exc())
                respmsg = getattr(self, '_base_err', 'param error')
                respcd = define.UNKOWNERR

            return error(respcd, respmsg=respmsg, data=respdata)

        return __

    return _


def login(func):
    def _(self, *args, **kwargs):
        # check role
        must_true(
            getattr(self, 'ses', None) and
            self.ses.is_login(),
            SessionError('session error')
        )
        self.userid = self.ses.data['userid']

        return func(self, *args, **kwargs)

    return _
