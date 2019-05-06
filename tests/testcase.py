#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@time: 2018/12/22
"""
from tornado.escape import json_decode, to_basestring, native_str
from tornado.options import options
from tornado.testing import AsyncHTTPTestCase
from tornado.httpclient import HTTPRequest
from tornado.util import PY3
from bson import json_util
import re
import controller as c
from controller.app import Application

if PY3:
    import http.cookies as Cookie
else:
    import Cookie

cookie = Cookie.SimpleCookie()


class APITestCase(AsyncHTTPTestCase):

    def get_app(self):
        options.testing = True
        options.debug = False
        options.port = self.get_http_port()
        return Application(c.handlers + c.views, db_name_ext='_test', ui_modules=c.modules,
                           default_handler_class=c.InvalidPageHandler)

    def tearDown(self):
        super(APITestCase, self).tearDown()
        self._app.stop()

    @staticmethod
    def parse_response(response):
        body = response.body and to_basestring(response.body) or '{}'
        if body and body.startswith('{'):
            body = json_util.loads(body)
            if 'data' in body and isinstance(body['data'], dict):  # 将data的内容赋给body，以便测试使用
                body.update(body['data'])
        return body

    def get_code(self, response):
        response = self.parse_response(response)
        return response.get('code')

    def assert_code(self, code, response, msg=None):
        """
        判断response中是否存在code
        :param code: 有三种类型：code; (code, message); [(code, message), (code, message)...]
        :param response: 请求的响应体
        """
        code = code[0] if isinstance(code, tuple) else code
        r_code = self.get_code(response) if self.get_code(response) else response.code
        if isinstance(code, list):
            self.assertIn(r_code, [c[0] if isinstance(c, tuple) else c for c in code], msg=msg)
        else:
            self.assertEqual(code, r_code, msg=msg)

    def fetch(self, url, **kwargs):
        if isinstance(kwargs.get('body'), dict):
            if isinstance(kwargs['body'].get('data'), dict):
                kwargs['body']['data'] = json_util.dumps(kwargs['body']['data'])
            kwargs['body'] = json_util.dumps(kwargs['body'])
            kwargs['method'] = kwargs.get('method', 'POST')

        headers = kwargs.get('headers', {})
        headers['Cookie'] = ''.join(['%s=%s;' % (x, morsel.value) for (x, morsel) in cookie.items()])

        request = HTTPRequest(self.get_url(url), headers=headers, **kwargs)
        self.http_client.fetch(request, self.stop)

        response = self.wait()
        headers = response.headers
        try:
            sc = headers._dict.get('Set-Cookie') if hasattr(headers, '_dict') else headers.get('Set-Cookie')
            if sc:
                text = native_str(sc)
                text = re.sub(r'Path=/(,)?', '', text)
                cookie.update(Cookie.SimpleCookie(text))
                while True:
                    cookie.update(Cookie.SimpleCookie(text))
                    if ',' not in text:
                        break
                    text = text[text.find(',') + 1:]
        except KeyError:
            pass

        return response

    def add_admin_user(self):
        """ 在创建其他用户前先创建超级管理员，避免测试用例乱序执行时其他用户先创建而成为管理员 """
        r = self.register_login(dict(email='admin@test.com', name='管理员', password='test123'))
        self.assert_code([200, 1012], r)
        return r

    def add_users(self, users, roles=None):
        admin = self.add_admin_user()
        for u in users:
            r = self.parse_response(self.register_login(u))
            u['_id'] = r.get('_id')
        self.assert_code(200, self.login_as_admin())
        for u in users:
            r = self.fetch('/api/user/role', body={'data': dict(_id=u['_id'], roles=u.get('roles', roles))})
            self.assert_code(200, r)
        return self.parse_response(admin)

    def login_as_admin(self):
        return self.login('admin@test.com', 'test123')

    def login(self, email, password):
        return self.fetch('/api/user/login', body={'data': dict(phone_or_email=email, password=password)})

    def register_login(self, info):
        r = self.fetch('/api/user/login', body={'data': dict(phone_or_email=info['email'], password=info['password'])})
        return r if self.get_code(r) == 200 else self.fetch('/api/user/register', body={'data': info})
