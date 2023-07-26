# -*- coding: utf-8 -*-

import os
import email
import logging
import types
import urllib
import urllib.request
import http
import time
import io


log = logging.getLogger()

client = None
conn_pool = None

def timeit(func):
    def _(self, *args, **kwargs):
        starttm = time.time()
        code = 0
        content = ''
        err = ''
        try:
            retval = func(self, *args, **kwargs)
            code = self.code
            if '\0' in self.content:
                content = '[binary data %d]' % len(self.content)
            else:
                content = self.content[:4000]
            return retval
        except Exception as e:
            err = str(e)
            raise
        finally:
            endtm = time.time()
            log.info('server=HTTPClient|name=%s|func=%s|code=%s|time=%d|args=%s|kwargs=%s|err=%s|content=%s',
                     self.name,func.__name__,str(code),
                     int((endtm-starttm)*1000000),
                     str(args),str(kwargs),
                     err,content)
    return _

def install(name, **kwargs):
    global client
    x = globals()
    for k in x.keys():
        v = x[k]
        if type(v) == types.ClassType and v != HTTPClient and issubclass(v, HTTPClient):
            if v.name == name:
                client = v(**kwargs)
                return client

def utf8urlencode(data):
    #tmp = {}
    #for k,v in data.items():
    #    tmp[k.encode('utf-8') if isinstance(k, unicode) else str(k)] = \
    #        v.encode('utf-8') if isinstance(v, unicode) else str(v)
    #return urllib.parse.urlencode(tmp)
    return urllib.parse.urlencode(data)

def dict2xml(root, sep='', cdata=True, encoding='utf-8'):
    '''sep 可以为 \n'''
    xml = ''
    for key in sorted(root.keys()):
        #if isinstance(key, unicode):
        #    u_key = key.encode(encoding)
        #else:
        #    u_key = str(key)
        u_key = key
        if isinstance(root[key], dict):
            xml = '%s<%s>%s%s</%s>%s' % (xml, u_key, sep, dict2xml(root[key], sep), u_key, sep)
        elif isinstance(root[key], list):
            xml = '%s<%s>' % (xml, u_key)
            for item in root[key]:
                xml = '%s%s' % (xml, dict2xml(item,sep))
            xml = '%s</%s>' % (xml, u_key)
        else:
            value = root[key]
            #if isinstance(value, unicode):
            #    value = value.encode(encoding)

            if cdata:
                xml = '%s<%s><![CDATA[%s]]></%s>%s' % (xml, u_key, value, u_key, sep)
            else:
                xml = '%s<%s>%s</%s>%s' % (xml, u_key, value, u_key, sep)
    return xml


class HTTPClient:
    code = 0
    content = ''
    headers = {}
    charset = 'utf-8'

    def __init__(self, verify_ssl_certs=False, timeout=10, conn_pool=False, allow_redirect=False):
        self._verify_ssl_certs = verify_ssl_certs
        self._timeout = timeout
        self._conn_pool = conn_pool
        self._allow_redirect = allow_redirect

    @timeit
    def get(self, url, params={}, **kwargs):
        if params:
            if '?' in url:
                url = url + '&' + utf8urlencode(params)
            else:
                url = url + '?' + utf8urlencode(params)

        header = {}
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        content, code, headers = self.request('get', url, header, **kwargs)

        return content

    @timeit
    def put(self, url, params={}, **kwargs):
        header = {
            'Content-Type':'application/x-www-form-urlencoded'
        }
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        put_data = utf8urlencode(params)
        content, code, headers = self.request('put', url, header, put_data, **kwargs)

        return content

    @timeit
    def post(self, url, params={}, **kwargs):
        header = {
            'Content-Type':'application/x-www-form-urlencoded'
        }
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        post_data = utf8urlencode(params)
        content, code, headers = self.request('post', url, header, post_data, **kwargs)

        return content

    @timeit
    def post_json(self, url, json_dict={}, escape = True, **kwargs):
        import json

        header = {
            'Content-Type':'application/json'
        }
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        if isinstance(json_dict, dict):
            post_data = json.dumps(json_dict, ensure_ascii = escape).encode()
        else:
            post_data = json_dict

        #if isinstance(post_data, unicode):
        #    post_data = post_data.encode('utf-8')

        log.debug('post_data=%s', post_data)

        content, code, headers = self.request('post', url, header, post_data, **kwargs)

        return content

    @timeit
    def post_xml(self, url, xml={}, **kwargs):

        header = {
            'Content-Type':'application/xml',
        }
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        if isinstance(xml, dict):
            xml = dict2xml(xml)
        #if isinstance(xml, unicode):
        #    xml = xml.encode('utf-8')

        log.debug('post_data=%s', xml)

        if isinstance(xml,str):
            xml = xml.encode(encoding="utf-8")

        content, code, headers = self.request('post', url, header, xml, **kwargs)

        return content

    @timeit
    def delete(self, url, params={}, **kwargs):
        header = {
            'Content-Type':'application/x-www-form-urlencoded'
        }
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        post_data = utf8urlencode(params)
        content, code, headers = self.request('delete', url, header, post_data, **kwargs)

        return content


    def request(self, method, url, headers, post_data=None, **kwargs):
        raise NotImplementedError(
            'HTTPClient subclasses must implement `request`')

class RequestsClient(HTTPClient):
    name = 'requests'


    @timeit
    def post_file(self, url, data={}, files={}, **kwargs):
        '''
        requests发文件方便一些  就不实现协议报文了
        '''
        header = {
        }
        if 'headers' in kwargs:
            header.update(kwargs.pop('headers'))

        content, code, headers = self.request('post', url, header, post_data=data, files=files, **kwargs)

        return content

    def request(self, method, url, headers, post_data=None,  **kwargs):

        # 如果是长连接模式
        if self._conn_pool:
            global conn_pool
            if not conn_pool:
                import requests
                conn_pool = requests.Session()
            requests = conn_pool
        else:
            import requests


        if self._verify_ssl_certs:
            kwargs['verify'] = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/ca-certificates.crt')
        else:
            kwargs['verify'] = False

        if self._allow_redirect:
            kwargs['allow_redirects'] = True
        else:
            kwargs['allow_redirects'] = False

        result = requests.request(method,
                                  url,
                                  headers=headers,
                                  data=post_data,
                                  timeout=self._timeout,
                                  **kwargs)

        self.content, self.code, self.headers = result.content.decode(self.charset), result.status_code, result.headers

        return self.content, self.code, self.headers

