#!/usr/bin/env python
# -*- coding: utf-8 -*-

import controller.validate as v
from controller.model import Model


class User(Model):
    primary = '_id'
    collection = 'user'
    fields = {
        'img': {'name': '头像'},
        'name': {'name': '姓名'},
        'gender': {'name': '性别', 'input_type': 'radio', 'options': ['男', '女']},
        'email': {'name': '邮箱'},
        'phone': {'name': '手机'},
        'password': {'name': '密码'},
        'roles': {'name': '角色'},
        'group': {'name': '用户组'},
        'task_batch': {'name': '任务批次'},
        'create_time': {'name': '创建时间'},
        'updated_time': {'name': '更新时间'},
        'agent': {'name': '浏览器类型'},
    }
    hide_fields = ['agent']
    rules = [
        (v.not_empty, 'name', 'password'),
        (v.not_both_empty, 'email', 'phone'),
        (v.is_name, 'name'),
        (v.is_email, 'email'),
        (v.is_phone, 'phone'),
        (v.is_password, 'password'),
    ]
