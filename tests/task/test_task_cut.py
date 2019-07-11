#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tests.users as u
from controller import errors
from tests.testcase import APITestCase
from tornado.escape import json_encode


class TestTaskFlow(APITestCase):

    def setUp(self):
        super(TestTaskFlow, self).setUp()
        self.add_first_user_as_admin_then_login()
        self.add_users_by_admin(
            [dict(email=r[0], name=r[2], password=r[1]) for r in [u.expert1, u.expert2, u.expert3]],
            '切分专家,文字专家'
        )
        self.revert()

    def tearDown(self):
        super(TestTaskFlow, self).tearDown()

    def test_cut_flow(self):
        """ 测试任务流程 """
        for task_type in [
            'block_cut_proof', 'block_cut_review',
            'column_cut_proof', 'column_cut_review',
            'char_cut_proof', 'char_cut_review',
        ]:
            # 发布任务
            self.login_as_admin()
            page_names = ['GL_1056_5_6', 'JX_165_7_12', 'QL_25_16']
            self.set_task_status({task_type: 'ready'}, page_names)
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(page_names))))
            published = r.get('data', {}).get('published')
            pending = r.get('data', {}).get('pending')
            if 'proof' in task_type:
                self.assertEqual(set(page_names), set(published), msg=task_type)
            else:
                self.assertIsNotNone(published)
                self.assertTrue(set(published).issubset(set(page_names)), msg=task_type)
                self.assertTrue(set(pending).issubset(set(page_names)), msg=task_type)

            # 任务大厅
            lobby_type = 'text_proof' if 'text_proof' in task_type else task_type
            r = self.fetch('/task/lobby/%s?_raw=1&_no_auth=1' % lobby_type)
            self.assert_code(200, r, msg=task_type)
            r = self.parse_response(r)
            self.assertEqual(set(published), set([t['name'] for t in r['tasks']]), msg=task_type)

            # 领取第一个任务
            self.login(u.expert1[0], u.expert1[1])
            page_name = page_names[0]
            r = self.parse_response(self.fetch('/api/task/pick/' + task_type, body={'data': {'page_name': page_name}}))
            self.assertEqual(page_name, r.get('page_name'), msg=task_type)
            page = self._app.db.page.find_one({'name': page_name})
            self.assertIn(task_type, page['tasks'])
            self.assertEqual(page['tasks'][task_type]['status'], 'picked')
            self.assertEqual(page['tasks'][task_type]['picked_by'], u.expert1[2])

            # 其他人不能领取此任务
            self.login(u.expert2[0], u.expert2[1])
            r = self.fetch('/api/task/pick/' + task_type, body={'data': {'page_name': page_name}})
            self.assert_code(errors.task_not_published, r, msg=task_type)

            # 再领取新任务时，提示有未完成任务
            self.login(u.expert1[0], u.expert1[1])
            r = self.parse_response(self.fetch('/api/task/pick/' + task_type, body={'data': {}}))
            self.assertEqual(errors.task_uncompleted[0], r.get('code'), msg=task_type)

            # 保存第一个任务
            box_type = task_type.split('_')[0]
            data = {'box_type': box_type, 'boxes': json_encode(page[box_type + 's'])}
            r = self.fetch('/api/task/do/%s/%s?_raw=1' % (task_type, page_name), body={'data': data})
            self.assert_code(200, r, msg=task_type)
            self.assertTrue(self.parse_response(r).get('updated'))

            # 提交第一个任务
            data['submit'] = True
            r = self.fetch('/api/task/do/%s/%s?_raw=1' % (task_type, page_name), body={'data': data})
            self.assert_code(200, r, msg=task_type)
            self.assertTrue(self.parse_response(r).get('submitted'))

            # 领取第二个任务
            page_name = page_names[1]
            r = self.parse_response(self.fetch('/api/task/pick/' + task_type, body={'data': {'page_name': page_name}}))
            self.assertEqual(page_name, r.get('page_name'), msg=task_type)

            if 'proof' in task_type:
                # 提交第二个任务
                page = self._app.db.page.find_one({'name': page_name})
                box_type = task_type.split('_')[0]
                data = {'box_type': box_type, 'boxes': json_encode(page[box_type + 's']), 'submit': True}
                r = self.fetch('/api/task/do/%s/%s?_raw=1' % (task_type, page_name), body={'data': data})
                self.assert_code(200, r, msg=task_type)
                self.assertTrue(self.parse_response(r).get('submitted'))

                # 领取第三个任务
                page_name = page_names[2]
                r = self.parse_response(
                    self.fetch('/api/task/pick/' + task_type, body={'data': {'page_name': page_name}}))
                self.assertEqual(page_name, r.get('page_name'), msg=task_type)

                # 退回第三个任务
                url = '/api/task/return/%s/%s' % (task_type, page_name)
                r = self.parse_response(self.fetch(url, body={'data': {}}))
                self.assertTrue(r.get('returned'))
            else:
                # 退回第二个任务
                url = '/api/task/return/%s/%s' % (task_type, page_name)
                r = self.parse_response(self.fetch(url, body={'data': {}}))
                self.assertTrue(r.get('returned'))

    def test_cut_relation(self):
        """ 测试切分审校的前后依赖关系 """
        cut_pre_tasks = {
            'block_cut_proof': 'block_cut_review',
            'column_cut_proof': 'column_cut_review',
            'char_cut_proof': 'char_cut_review',
        }

        for t1, t2 in cut_pre_tasks.items():
            # 发布t1，领取t1并提交
            self.login_as_admin()
            page_names = ['GL_1056_5_6', 'JX_165_7_12']
            r = self.publish(dict(task_type=t1, pre_tasks=self.pre_tasks.get(t1), pages=','.join(page_names)))
            self.assert_code(200, r)
            self.login(u.expert1[0], u.expert1[1])
            self.parse_response(self.fetch('/api/task/pick/' + t1, body={'data': {'page_name': page_names[0]}}))
            page = self._app.db.page.find_one({'name': page_names[0]})
            box_type = t1.split('_')[0]
            boxes = page[box_type + 's']
            r = self.fetch(
                '/api/task/do/%s/%s?_raw=1' % (t1, page['name']),
                body={'data': dict(submit=True, box_type=box_type, boxes=json_encode(boxes))}
            )
            self.assertTrue(self.parse_response(r).get('submitted'))

            # 发布t2，任务大厅应有任务
            self.login_as_admin()
            r = self.publish(dict(task_type=t2, pre_tasks=self.pre_tasks.get(t2), pages=','.join(page_names)))
            self.assert_code(200, r)
            self.login(u.expert2[0], u.expert2[1])
            r = self.parse_response(self.fetch('/task/lobby/%s?_raw=1' % t2))
            self.assertIn(page_names[0], [t['name'] for t in r.get('tasks')], msg=t2)
