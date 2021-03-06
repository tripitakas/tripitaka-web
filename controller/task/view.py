#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from bson import json_util
from bson.objectid import ObjectId
from controller import errors as e
from controller.task.base import TaskHandler


class PageTaskLobbyHandler(TaskHandler):
    URL = '/task/lobby/@page_task'

    def get(self, task_type):
        """任务大厅"""
        try:
            q = self.get_query_argument('q', '')
            batch = self.prop(self.current_user, 'task_batch.%s' % task_type)
            tasks, total_count = self.find_lobby(task_type, q=q, batch=batch)
            fields = [('doc_id', '页编码'), ('num', '校次'), ('char_count', '单字数量')]
            self.render('task_lobby.html', tasks=tasks, task_type=task_type, total_count=total_count,
                        fields=fields, batch=batch, search_tips='搜索页编码，请输入全部或部分页编码',
                        format_value=self.format_value)

        except Exception as error:
            return self.send_db_error(error)


class CharTaskLobbyHandler(TaskHandler):
    URL = '/task/lobby/@char_task'

    def get(self, task_type):
        """任务大厅"""
        try:
            q = self.get_query_argument('q', '')
            batch = self.prop(self.current_user, 'task_batch.%s' % task_type)
            tasks, total_count = self.find_lobby(task_type, q=q, batch=batch)
            fields = [('base_txts', '聚类字种'), ('num', '校次'), ('char_count', '单字数量')]
            self.render('task_lobby.html', tasks=tasks, task_type=task_type, total_count=total_count,
                        fields=fields, batch=batch, search_tips='搜索聚类字种，请输入单个汉字',
                        format_value=self.format_value)

        except Exception as error:
            return self.send_db_error(error)


class MyPageTaskHandler(TaskHandler):
    URL = '/task/my/@page_task'

    table_fields = ['batch', 'doc_id', 'num', 'status', 'char_count', 'added', 'deleted', 'changed', 'total',
                    'used_time', 'picked_time', 'finished_time', 'updated_time', 'nav_times', 'my_remark']
    hide_fields = ['num', 'added', 'deleted', 'changed', 'updated_time']
    search_fields = ['batch', 'doc_id', 'my_remark']
    operations = [
        {'operation': 'btn-search', 'label': '综合检索', 'data-target': 'searchModal'},
        {'operation': 'btn-dashboard', 'label': '结果统计'},
        {'operation': 'btn-nav', 'label': '继续浏览'},
    ]
    actions = [
        {'action': 'my-task-view', 'label': '查看'},
        {'action': 'my-task-update', 'label': '更新'},
        {'action': 'my-task-nav', 'label': '浏览'},
        {'action': 'my-task-remark', 'label': '备注'},
    ]

    def get(self, task_type):
        """我的任务"""
        try:
            kwargs = self.get_template_kwargs()
            kwargs['page_title'] = '我的任务-' + self.get_task_name(task_type)
            if self.get_hide_fields() is not None:
                kwargs['hide_fields'] = self.get_hide_fields()
            cond, params = self.get_task_search_condition(self.request.query, 'page')
            status = {'$in': [self.STATUS_PICKED, self.STATUS_FINISHED]}
            cond.update({'task_type': task_type, 'status': status, 'picked_user_id': self.user_id})
            docs, pager, q, order = self.find_by_page(self, cond, default_order='_id')
            self.render('task_my_page.html', task_type=task_type, docs=docs, pager=pager, q=q, order=order,
                        params=params, format_value=self.format_value, **kwargs)

        except Exception as error:
            return self.send_db_error(error)


class MyCharTaskHandler(TaskHandler):
    URL = '/task/my/@char_task'

    table_fields = ['batch', 'base_txts', 'num', 'status', 'char_count', 'used_time', 'picked_time',
                    'finished_time', 'updated_time', 'my_remark']
    search_fields = ['batch', 'my_remark']
    operations = [
        {'operation': 'btn-search', 'label': '综合检索', 'data-target': 'searchModal'},
    ]
    actions = [
        {'action': 'my-task-view', 'label': '查看'},
        {'action': 'my-task-update', 'label': '更新'},
        {'action': 'my-task-remark', 'label': '备注'},
    ]

    def get(self, task_type):
        """我的任务"""
        try:
            kwargs = self.get_template_kwargs()
            kwargs['page_title'] = '我的任务-' + self.get_task_name(task_type)
            if self.get_hide_fields() is not None:
                kwargs['hide_fields'] = self.get_hide_fields()
            cond, params = self.get_task_search_condition(self.request.query, 'char')
            status = {'$in': [self.STATUS_PICKED, self.STATUS_FINISHED]}
            cond.update({'task_type': task_type, 'status': status, 'picked_user_id': self.user_id})
            docs, pager, q, order = self.find_by_page(self, cond, default_order='-picked_time')
            self.render('task_my_char.html', task_type=task_type, docs=docs, pager=pager, q=q, order=order,
                        params=params, format_value=self.format_value, **kwargs)

        except Exception as error:
            return self.send_db_error(error)


class TaskInfoHandler(TaskHandler):
    URL = '/task/info/@task_id'

    @classmethod
    def format_value(cls, value, key=None, doc=None):
        """格式化task表的字段输出"""
        if key == 'txt_equals' and value:
            return ','.join(['%s:%s' % (k, v) for k, v in value.items()])
        if key == 'base_txts':
            return ','.join(['%s:%s' % (t.get('txt'), t.get('count')) for t in value])
        return super().format_value(value, key, doc)

    def get(self, task_id):
        """任务详情"""
        try:
            task = self.db.task.find_one({'_id': ObjectId(task_id)})
            if not task:
                return self.send_error_response(e.no_object, message='没有找到该任务')
            self.render('task_info.html', task=task)

        except Exception as error:
            return self.send_db_error(error)


class TaskSampleHandler(TaskHandler):
    URL = '/task/sample/@task_type'

    def get(self, task_type):
        """练习任务"""
        try:
            tasks = list(self.db.task.aggregate([
                {'$match': {'task_type': task_type, 'batch': '练习任务'}}, {'$sample': {'size': 1}}
            ]))
            if tasks:
                return self.redirect('/task/%s/%s' % (task_type, tasks[0]['_id']))
            else:
                return self.send_error_response(e.no_object, message='没有找到练习任务')

        except Exception as error:
            return self.send_db_error(error)
