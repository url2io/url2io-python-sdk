#coding: utf-8
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING (copied as below) for more details.
#
#                DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
#                        Version 2, December 2004 
#
#     Copyright (C) 2004 Sam Hocevar <sam@hocevar.net> 
#
#     Everyone is permitted to copy and distribute verbatim or modified 
#     copies of this license document, and changing it is allowed as long 
#     as the name is changed. 
#
#                DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
#       TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION 
#
#      0. You just DO WHAT THE FUCK YOU WANT TO. 

"""a simple url2io sdk
example:
api = API(token)
api.article(url='http://www.url2io.com/products', fields=['next', 'text'])
"""

__all__ = ['APIError', 'API']


DEBUG_LEVEL = 1

import sys
import socket
import json
import urllib
import urllib2
import time
from collections import Iterable

class APIError(Exception):
    code = None
    """HTTP status code"""

    url = None
    """request URL"""

    body = None
    """server response body; or detailed error information"""

    def __init__(self, code, url, body):
        self.code = code
        self.url = url
        self.body = body

    def __str__(self):
        return 'code={s.code}\nurl={s.url}\n{s.body}'.format(s = self)

    __repr__ = __str__


class API(object):
    token = None
    server = 'http://api.url2io.com/'

    decode_result = True
    timeout = None
    max_retries = None
    retry_delay = None

    def __init__(self, token, srv = None,
                 decode_result = True, timeout = 30, max_retries = 5,
                 retry_delay = 3):
        """:param srv: The API server address
        :param decode_result: whether to json_decode the result
        :param timeout: HTTP request timeout in seconds
        :param max_retries: maximal number of retries after catching URL error
            or socket error
        :param retry_delay: time to sleep before retrying"""
        self.token = token
        if srv:
            self.server = srv
        self.decode_result = decode_result
        assert timeout >= 0 or timeout is None
        assert max_retries >= 0
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        _setup_apiobj(self, self, [])

    def update_request(self, request):
        """overwrite this function to update the request before sending it to
        server"""
        pass


def _setup_apiobj(self, apiobj, path):
    if self is not apiobj:
        self._api = apiobj
        self._urlbase = apiobj.server + '/'.join(path)

    lvl = len(path)
    done = set()
    for i in _APIS:
        if len(i) <= lvl:
            continue
        cur = i[lvl]
        if i[:lvl] == path and cur not in done:
            done.add(cur)
            setattr(self, cur, _APIProxy(apiobj, i[:lvl + 1]))


class _APIProxy(object):
    _api = None

    _urlbase = None

    def __init__(self, apiobj, path):
        _setup_apiobj(self, apiobj, path)

    def __call__(self, post = False, *args, **kwargs):
        # /article
        # url = 'http://xxxx.xxx',
        # fields = ['next',],
        #
        if len(args):
            raise TypeError('only keyword arguments are allowed')
        if type(post) is not bool:
            raise TypeError('post argument can only be True or False')

        url = self.geturl(**kwargs)

        request = urllib2.Request(url)

        self._api.update_request(request)

        retry = self._api.max_retries
        while True:
            retry -= 1
            try:
                ret = urllib2.urlopen(request, timeout = self._api.timeout).read()
                break
            except urllib2.HTTPError as e:
                raise APIError(e.code, url, e.read())
            except (socket.error, urllib2.URLError) as e:
                if retry < 0:
                    raise e
                _print_debug('caught error: {}; retrying'.format(e))
                time.sleep(self._api.retry_delay)

        if self._api.decode_result:
            try:
                ret = json.loads(ret)
            except:
                raise APIError(-1, url, 'json decode error, value={0!r}'.format(ret))
        return ret

    def _mkarg(self, kargs):
        """change the argument list (encode value, add api key/secret)
        :return: the new argument list"""
        def enc(x):
            #if isinstance(x, unicode):
            #    return x.encode('utf-8')
            #return str(x)
            return x.encode('utf-8') if isinstance(x, unicode) else str(x)

        kargs = kargs.copy()
        kargs['token'] = self._api.token
        for (k, v) in kargs.items():
            if isinstance(v, Iterable) and not isinstance(v, basestring):
                kargs[k] = ','.join([enc(i) for i in v])
            else:
                kargs[k] = enc(v)

        return kargs

    def geturl(self, **kargs):
        """return the request url"""
        return self._urlbase + '?' + urllib.urlencode(self._mkarg(kargs)) 


def _print_debug(msg):
    if DEBUG_LEVEL:
        sys.stderr.write(str(msg) + '\n')

_APIS = [
    '/article',
    #'/images',
]

_APIS = [i.split('/')[1:] for i in _APIS]

