#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
from .page import Page
from .base import PageHandler
from controller import helper as h
from controller import validate as v
from .api import PageBoxApi


class PageTasklistApi(PageHandler):
    URL = '/api/page/task/list'

    def post(self):
        """获取页任务的页码"""
        try:
            rules = [(v.not_empty, 'search')]
            self.validate(self.data, rules)
            condition, _ = self.get_task_search_condition(self.data['search'], 'page')
            tasks = list(self.db.task.find(condition, {'doc_id': 1}))
            page_names = [task['doc_id'] for task in tasks]
            self.send_data_response(dict(names=page_names))

        except Exception as error:
            return self.send_db_error(error)


class PageTaskPublishApi(PageHandler):
    URL = '/api/page/task/publish'

    field_names = {
        'published': '任务已发布', 'pending': '任务已悬挂', 'finished_before': '任务已完成',
        'un_existed': '页面不存在', 'published_before': '任务曾被发布',
    }

    def post(self):
        """发布任务"""
        try:
            log = dict()
            self.get_page_names(log)
            rules = [
                (v.not_empty, 'page_names', 'task_type', 'priority', 'force', 'batch'),
                (v.in_list, 'task_type', list(self.task_types.keys())),
                (v.in_list, 'pre_tasks', list(self.task_types.keys())),
                (v.is_priority, 'priority'),
            ]
            self.validate(self.data, rules)
            log = self.check_and_publish(log)
            log_id = self.add_op_log(self.db, 'publish_task', None, log, self.username)
            message = '，'.join(['%s：%s条' % (self.field_names.get(k) or k, len(names)) for k, names in log.items()])
            return self.send_data_response(dict(message=message, id=str(log_id), **log))

        except self.DbError as error:
            return self.send_db_error(error)

    def get_page_names(self, log):
        """获取页码"""
        page_names = self.data.get('page_names')
        if page_names:
            if isinstance(page_names, str):
                page_names = page_names.split(',')
            pages = list(self.db.page.find({'name': {'$in': page_names}}, {'name': 1}))
            log['un_existed'] = set(page_names) - set([page['name'] for page in pages])
            page_names = [page['name'] for page in pages]
        names_file = self.request.files.get('names_file')
        if names_file:
            names_str = str(names_file[0]['body'], encoding='utf-8')
            try:
                page_names = json.loads(names_str)
            except json.decoder.JSONDecodeError:
                ids_str = re.sub(r'(\n|\r\n)+', ',', names_str)
                page_names = ids_str.split(r',')
            page_names = [n for n in page_names if n]
            pages = list(self.db.page.find({'name': {'$in': page_names}}, {'name': 1}))
            log['un_existed'] = set(page_names) - set([page['name'] for page in pages])
            page_names = [page['name'] for page in pages]
        elif self.data.get('prefix'):
            condition = {'name': {'$regex': self.data['prefix']}}
            page_names = [page['name'] for page in list(self.db.page.find(condition, {'name': 1}))]
        elif self.data.get('search'):
            condition = Page.get_page_search_condition(self.data['search'])[0]
            query = self.db.page.find(condition, {'name': 1})
            page = h.get_url_param('page', self.data['search'])
            if page:
                s = h.get_url_param('page_size', self.data['search']) or self.prop(self.config, 'pager.page_size', 10)
                query = query.skip((int(page) - 1) * int(s)).limit(int(s))
            page_names = [page['name'] for page in list(query)]
        self.data['page_names'] = page_names

    def check_and_publish(self, log):
        """检查页码并发布任务"""
        # 去掉已发布的页码
        page_names, task_type, num = self.data['page_names'], self.data['task_type'], self.data.get('num') or 1
        if page_names:
            cond = dict(task_type=task_type, num=int(num), doc_id={'$in': list(page_names)})
            log['published_before'] = set(t['doc_id'] for t in self.db.task.find(cond, {'doc_id': 1}))
            page_names = set(page_names) - log['published_before']

        # 剩下的页码，发布新任务
        if page_names:
            pre_tasks = self.data['pre_tasks']
            if pre_tasks:
                pre_tasks = [pre_tasks] if isinstance(pre_tasks, str) else pre_tasks
                db_pre_tasks = list(self.db.task.find(
                    {'doc_id': {'$in': list(page_names)}, 'task_type': {'$in': pre_tasks}},
                    {'task_type': 1, 'num': 1, 'status': 1, 'doc_id': 1}
                ))
                # 前置任务未发布、未完成（有一个未完成，即未完成）的情况，发布为PENDING
                un_published = set(page_names) - set(t['doc_id'] for t in db_pre_tasks)
                un_finished = set(t['doc_id'] for t in db_pre_tasks if t['status'] != self.STATUS_FINISHED)
                log['pending'] = set(un_finished | un_published)
                if log['pending']:
                    self.create_tasks(log['pending'], self.STATUS_PENDING, {t: None for t in pre_tasks})
                # 其它为前置任务全部已完成的情况，发布为PUBLISHED
                page_names = set(page_names) - log['pending']
                if page_names:
                    self.create_tasks(page_names, self.STATUS_PUBLISHED, {t: self.STATUS_FINISHED for t in pre_tasks})
                    log['published'] = page_names
            else:
                self.create_tasks(page_names, self.STATUS_PUBLISHED)
                log['published'] = page_names

        return {k: list(l) for k, l in log.items() if l}

    def create_tasks(self, page_names, status, pre_tasks=None):
        def get_task(page_name, char_count=None, params=None):
            num = int(self.data.get('num') or 1)
            priority = int(self.data['priority'])
            steps = self.data.get('steps') and dict(todo=self.data['steps']) or {}
            task = dict(task_type=task_type, num=num, batch=self.data['batch'], status=status, priority=priority,
                        steps=steps, pre_tasks=pre_tasks, is_oriented=is_oriented, collection='page', id_name='name',
                        doc_id=page_name, char_count=char_count, params=params or {}, result={},
                        create_time=self.now(), updated_time=self.now(), publish_time=self.now(),
                        publish_user_id=self.user_id, publish_by=self.username)
            not is_oriented and task.pop('is_oriented', 0)
            return task

        if not page_names:
            return
        task_type = self.data['task_type']
        is_oriented = self.data.get('is_oriented') == '1'
        pages = list(self.db.page.aggregate([
            {'$match': {'name': {'$in': list(page_names)}}},
            {'$project': {'name': 1, 'char_count': {'$size': {'$ifNull': ['$chars', []]}}}}
        ]))
        tasks = [get_task(page['name'], page['char_count']) for page in pages]
        if tasks:
            self.db.task.insert_many(tasks, ordered=False)
            update = {'tasks.%s.%s' % (task_type, self.data.get('num') or 1): status}
            self.db.page.update_many({'name': {'$in': list(page_names)}}, {'$set': update})


class PageTaskCutApi(PageHandler):
    URL = ['/api/task/do/(cut_proof|cut_review)/@task_id',
           '/api/task/update/(cut_proof|cut_review)/@task_id']

    def post(self, task_type, task_id):
        """切分校对、审定页面"""
        try:
            page = PageBoxApi.save_box(self, self.task['doc_id'], task_type)
            hint_no = self.get_user_hint_no(page, self.user_id)
            if self.data.get('submit') and self.task['status'] != self.STATUS_FINISHED:
                used_time = int((self.now() - self.task['picked_time']).seconds)
                self.db.task.update_one({'_id': self.task['_id']}, {'$set': {
                    'status': self.STATUS_FINISHED, 'finished_time': self.now(),
                    'used_time': used_time, **hint_no}})
                self.update_post_tasks(self.task)
                self.update_page_status(self.STATUS_FINISHED, self.task)
            else:
                self.db.task.update_one({'_id': self.task['_id']}, {'$set': hint_no})
            return self.send_data_response()

        except self.DbError as error:
            return self.send_db_error(error)


class PageTaskTextApi(PageHandler):
    URL = ['/api/task/do/(text_proof|text_review)/@task_id',
           '/api/task/update/(text_proof|text_review)/@task_id']

    def post(self, task_type, task_id):
        """文字校对、审定页面"""
        try:
            if self.data.get('submit') and self.task['status'] != self.STATUS_FINISHED:
                self.db.task.update_one({'_id': self.task['_id']}, {'$set': {
                    'status': self.STATUS_FINISHED, 'finished_time': self.now()}})
                self.update_page_status(self.STATUS_FINISHED, self.task)
            return self.send_data_response()

        except self.DbError as error:
            return self.send_db_error(error)
