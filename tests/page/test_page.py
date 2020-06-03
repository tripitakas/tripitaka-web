#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from os import path
import tests.users as u
from tests.testcase import APITestCase
from utils.gen_chars import gen_chars


class TestCutTask(APITestCase):

    def setUp(self):
        super(TestCutTask, self).setUp()
        self.add_first_user_as_admin_then_login()
        self.add_users_by_admin(
            [dict(email=r[0], name=r[2], password=r[1]) for r in [u.expert1, u.expert2, u.expert3]],
            '切分专家,文字专家,数据管理员,单元测试用户'
        )
        self.add_users_by_admin(
            [dict(email=r[0], name=r[2], password=r[1]) for r in [u.proof1, u.proof2, u.proof3]],
            '普通用户,单元测试用户,切分校对员,聚类校对员,生僻校对员'
        )
        self.add_users_by_admin(
            [dict(email=r[0], name=r[2], password=r[1]) for r in [u.review1, u.review2, u.review3]],
            '普通用户,单元测试用户,切分审定员,聚类审定员,生僻审定员'
        )
        self.reset_tasks_and_data()

    def tearDown(self):
        super(TestCutTask, self).tearDown()

    @staticmethod
    def get_post_data(page, task_type=None):
        data = {k: page.get(k) for k in ['chars', 'columns', 'blocks']}
        if task_type:
            data['task_type'] = task_type
        return data

    def test_page_box(self):
        """ 测试切分校对"""
        name = 'QL_25_416'
        # 以校对员身份登录
        # 1. 测试以任务方式增删改
        self.login(u.proof1[0], u.proof1[1])
        # 测试修改数据
        page = self._app.db.page.find_one({'name': name})
        page['chars'][0].update({'changed': True, 'w': page['chars'][0]['w'] + 1})
        page['blocks'][0].update({'changed': True, 'w': page['blocks'][0]['w'] + 1})
        page['columns'][0].update({'changed': True, 'w': page['columns'][0]['w'] + 1})
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page, 'cut_proof')})
        self.assert_code(200, r)
        page1 = self._app.db.page.find_one({'name': name})
        self.assertIsNotNone(page1['chars'][0]['box_logs'])
        self.assertIsNotNone(page1['chars'][0]['box_level'])
        self.assertIsNotNone(page1['blocks'][0]['box_logs'])
        self.assertIsNotNone(page1['blocks'][0]['box_level'])
        self.assertIsNotNone(page1['columns'][0]['box_logs'])
        self.assertIsNotNone(page1['columns'][0]['box_level'])
        self.assertEqual(len(page['chars']), len(page1['chars']))
        # 测试新增数据
        page1['chars'].append({'x': 1, 'y': 1, 'w': 10, 'h': 10, 'added': True})
        page1['chars'].append({'x': 2, 'y': 2, 'w': 20, 'h': 20, 'added': True})
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page1, 'cut_proof')})
        self.assert_code(200, r)
        page2 = self._app.db.page.find_one({'name': name})
        self.assertEqual(len(page1['chars']), len(page2['chars']))
        # 测试删除数据
        page2['chars'].pop(-1)
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page2, 'cut_proof')})
        self.assert_code(200, r)
        page3 = self._app.db.page.find_one({'name': name})
        self.assertEqual(len(page2['chars']), len(page3['chars']))

        # 2. 测试直接增删改
        # 测试积分不够，无法修改数据
        page4 = self._app.db.page.find_one({'name': name})
        page4['chars'][1].update({'changed': True, 'w': page4['chars'][1]['w'] + 1})
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page4)})
        self.assert_code(200, r)
        page5 = self._app.db.page.find_one({'name': name})
        self.assertIsNone(page5['chars'][1].get('box_logs'))
        # 测试新增数据，不需要积分
        page5['chars'].append({'x': 1, 'y': 1, 'w': 10, 'h': 10, 'added': True})
        page5['chars'].append({'x': 2, 'y': 2, 'w': 20, 'h': 20, 'added': True})
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page5)})
        self.assert_code(200, r)
        page6 = self._app.db.page.find_one({'name': name})
        self.assertEqual(len(page6['chars']), len(page5['chars']))
        # 测试积分不够，无法删除数据
        page6['chars'].pop(-1)
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page6)})
        self.assert_code(200, r)
        page7 = self._app.db.page.find_one({'name': name})
        self.assertEqual(len(page7['chars']), len(page6['chars']) + 1)

        # 测试专家可以直接删除数据
        self.login(u.expert1[0], u.expert1[1])
        r = self.fetch('/api/page/box/' + name, body={'data': self.get_post_data(page6)})
        self.assert_code(200, r)
        page8 = self._app.db.page.find_one({'name': name})
        self.assertEqual(len(page8['chars']), len(page6['chars']))

    def test_gen_chars(self):
        """ 测试生成字表"""
        self._app.db.char.delete_many({})
        # 测试从page生成char数据
        name = 'YB_22_346'
        gen_chars(self._app.db, page_names=name)
        page = self._app.db.page.find_one({'name': name}, {'chars': 1})
        cnt = self._app.db.char.count_documents({})
        self.assertEqual(cnt, len(page['chars']))
        # 测试删除和更新char数据
        ch = page['chars'][0]
        ch['w'] += 1
        del page['chars'][-1]
        self._app.db.page.update_one({'_id': page['_id']}, {'$set': {'chars': page['chars']}})
        gen_chars(self._app.db, page_names=name)
        page = self._app.db.page.find_one({'name': name}, {'chars': 1})
        cnt = self._app.db.char.count_documents({})
        self.assertEqual(cnt, len(page['chars']))
        char = self._app.db.char.find_one({'name': 'YB_22_346_%s' % ch['cid']})
        self.assertEqual(char['pos']['w'], ch['w'])
