#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@time: 2018/6/12
"""
import tests.users as u
import controller.errors as e
from tests.testcase import APITestCase
from os import path


class TestUserCommonApi(APITestCase):
    def setUp(self):
        super(TestUserCommonApi, self).setUp()

    def test_user_login(self):
        """ 登录api """
        self.add_first_user_as_admin_then_login()
        self.add_users_by_admin([dict(email=u.user1[0], password=u.user1[1], name=u.user1[2])])

        # 密码有误
        r = self.fetch('/api/user/login', body={'data': dict(login_id=u.user1[0], password='!@#$%^%$1234')})
        self.assert_code(e.incorrect_password, r)

        # 正常登陆
        r = self.fetch('/api/user/login', body={'data': dict(login_id=u.user1[0], password=u.user1[1])})
        self.assert_code(200, r)

    def test_user_logout(self):
        """ 登出api """
        self.add_first_user_as_admin_then_login()
        self.add_users_by_admin([dict(email=u.user1[0], password=u.user1[1], name=u.user1[2])])
        r = self.fetch('/api/user/login', body={'data': dict(login_id=u.user1[0], password=u.user1[1])})
        self.assert_code(200, r)

        r = self.fetch('/api/user/logout', body={'data': {}})
        self.assert_code(200, r)

        r = self.fetch('/user/my/profile')
        self.assertNotIn(u.user1[0], self.parse_response(r))

    def test_user_register(self):
        """ 用户注册 """
        self._app.db.user.drop()
        # 姓名为空
        data = dict(email=u.user1[0], password=u.user1[1], name='')
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.not_allowed_empty, r)

        # 姓名格式有误
        data = dict(email=u.user1[0], password=u.user1[1], name='张三123')
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.invalid_name, r)

        # 手机和邮箱同时为空
        data = dict(password=u.user1[1], name=u.user1[2])
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.not_allowed_both_empty, r)

        # 手机格式有误
        data = dict(phone='13800000000-1', password=u.user1[1], name=u.user1[2])
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.invalid_phone, r)

        # 邮箱格式有误
        data = dict(email='user1#test.com', password=u.user1[1], name=u.user1[2])
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.invalid_email, r)

        # 密码为空
        data = dict(email=u.user1[0], password='', name=u.user1[2])
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.not_allowed_empty, r)

        # 密码格式有误
        data = dict(email=u.user1[0], password='123456', name=u.user1[2])
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(e.invalid_password, r)

        # 正常注册
        data = dict(email=u.user1[0], password=u.user1[1], name=u.user1[2])
        r = self.fetch('/api/user/register', body={'data': data})
        self.assert_code(200, r)
        data = self.parse_response(r)
        self.assertEqual(u.user1[0], data['email'])

    def test_user_change_my_pwd(self):
        """修改个人密码"""
        self.add_first_user_as_admin_then_login()
        users = self.add_users_by_admin([dict(email=u.user1[0], password=u.user1[1], name=u.user1[2])])
        user1 = users[0]
        self.assert_code(200, self.login(user1['email'], user1['password']))

        # 原始密码错误
        data = dict(old_password='wrong_psw_1', password='user1!@#$')
        r = self.fetch('/api/user/my/pwd', body={'data': data})
        self.assert_code(e.incorrect_old_password, r)

        # 原始密码和新密码一致
        data = dict(old_password=user1['password'], password=user1['password'])
        r = self.fetch('/api/user/my/pwd', body={'data': data})
        self.assert_code(e.both_times_equal, r)

        # 正常修改
        data = dict(old_password=user1['password'], password='user1!@#$%')
        r = self.fetch('/api/user/my/pwd', body={'data': data})
        self.assert_code(200, r)

    def test_user_change_my_profile(self):
        """修改个人信息"""
        self.add_first_user_as_admin_then_login()
        users = self.add_users_by_admin([dict(email=u.user1[0], password=u.user1[1], name=u.user1[2])])
        user1 = users[0]
        self.assert_code(200, self.login(user1['email'], user1['password']))

        # 手机和邮箱同时为空
        data = dict(name=user1['name'], phone='', email='')
        r = self.fetch('/api/user/my/profile', body={'data': data})
        self.assert_code(e.not_allowed_both_empty, r)

        # 姓名格式有误
        data = dict(name='张三1', phone='', email=user1['email'])
        r = self.fetch('/api/user/my/profile', body={'data': data})
        self.assert_code(e.invalid_name, r)

        # 邮箱格式有误
        data = dict(name=user1['name'], phone='13800000000', email='user1#test.com')
        r = self.fetch('/api/user/my/profile', body={'data': data})
        self.assert_code(e.invalid_email, r)

        # 手机格式有误
        data = dict(name=user1['name'], phone='138000000001111', email=user1['email'])
        r = self.fetch('/api/user/my/profile', body={'data': data})
        self.assert_code(e.invalid_phone, r)

        # 正常修改
        data = dict(name='张三', phone='13800000000', email='user1_new@test.com', gender='男')
        r = self.fetch('/api/user/my/profile', body={'data': data})
        self.assert_code(200, r)

    def test_user_upload_image(self):
        img_path = path.join(self._app.IMAGE_PATH, '..', 'imgs', 'ava1.png')
        self.assertTrue(path.exists(img_path))
        r = self.register_and_login(dict(email=u.user1[0], password=u.user1[1], name=u.user1[2]))
        self.assert_code(200, r)
        r = self.fetch('/api/user/my/avatar', files={'img': img_path}, body={})
        self.assert_code(200, r)
        r = self.fetch('/api/user/my/avatar', files={'img': img_path}, body={'data': dict(x=10, y=10)})
        self.assert_code(200, r)
