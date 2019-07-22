#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tests.testcase import APITestCase
from controller.periodic import periodic_task
from controller.task.base import TaskHandler as Th
import tests.users as u


class TestPeriodicTask(APITestCase):
    def setUp(self):
        super(TestPeriodicTask, self).setUp()
        self.add_first_user_as_admin_then_login()
        self.add_users_by_admin([dict(email=r[0], name=r[2], password=r[1]) for r in [u.expert1]], '切分专家')

    def get_data_lock(self, page_name, task_type):
        page = self._app.db.page.find_one({'name': page_name})
        data_field = Th.get_shared_data_field(task_type)
        return data_field and Th.prop(page, 'lock.' + data_field)

    def test_do_task_release(self):
        self.login_as_admin()
        # 发布任务，前置任务为空
        self.revert()
        self.assert_code(200, self.publish(dict(task_type='block_cut_proof', pages='GL_1056_5_6')))
        # 领取任务
        self.login(u.expert1[0], u.expert1[1])
        self.fetch('/api/task/pick/block_cut_proof', body={'data': {'page_name': 'GL_1056_5_6'}})
        self.assertEqual(self.get_data_lock('GL_1056_5_6', 'block_cut_proof').get('locked_by'), u.expert1[2])
        # 自动回收任务
        periodic_task(self._app, dict(at_once=True, minutes=1))
        self.assertTrue(self.get_data_lock('GL_1056_5_6', 'block_cut_proof'))
        periodic_task(self._app, dict(at_once=True, minutes=0))
        self.assertFalse(self.get_data_lock('GL_1056_5_6', 'block_cut_proof'))