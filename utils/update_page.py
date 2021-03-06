#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python3 utils/update_page.py --uri=uri --func=apply_ocr_col
import re
import sys
import math
import json
import pymongo
from os import path, walk
from datetime import datetime
from operator import itemgetter

BASE_DIR = path.dirname(path.dirname(__file__))
sys.path.append(BASE_DIR)

from controller import helper as hp
from controller.page.base import PageHandler as Ph
from controller.char.base import CharHandler as Ch


def _update_box_log(page):
    """ 更新以前的box_logs格式"""
    for f in ['blocks', 'columns', 'chars']:
        boxes = page.get(f) or []
        for b in boxes:
            for k in ['x', 'y', 'w', 'h']:
                if b.get(k) and b[k] != round(b[k], 1):
                    b[k] = round(b[k], 1)
            if not b.get('box_logs'):
                continue
            for k in ['new', 'added', 'changed', 'updated']:
                if k in b:
                    b.pop(k, 0)
            if not len(b['box_logs']):
                b.pop('box_logs', 0)
            # 设置added/updated
            if b['box_logs'][0].get('username'):
                b['added'] = True
                if len(b['box_logs']) > 1:
                    b['changed'] = True
            else:
                b['changed'] = True
            # 设置log
            for i, log in enumerate(b['box_logs']):
                # 检查pos
                if log.get('x') and not log.get('pos'):
                    log['pos'] = {k: log[k] for k in ['x', 'y', 'w', 'h'] if log.get(k)}
                for k in ['x', 'y', 'w', 'h']:
                    log.pop(k, 0)
                # 检查op
                if i == 0:
                    if not log.get('username'):
                        log['op'] = 'initial'
                    else:
                        log['op'] = 'added'
                else:
                    log['op'] = 'changed'
                # 检查updated_time
                if log.get('updated_time'):
                    log['create_time'] = log['updated_time']
                    log.pop('updated_time', 0)
            # log按时间排序
            if len(b['box_logs']) > 1:
                if not b['box_logs'][0].get('create_time'):
                    b['box_logs'][0]['create_time'] = datetime.strptime('1999-1-1 00:00:00', '%Y-%m-%d %H:%M:%S')
                    b['box_logs'].sort(key=itemgetter('create_time'))
                    b['box_logs'][0].pop('create_time', 0)
                else:
                    b['box_logs'].sort(key=itemgetter('create_time'))
    return True


def update_sub_column_id(db, source=None):
    """ 更新子列的column_id"""
    size = 1000
    cond = {'source': source}
    item_count = db.page.count_documents(cond)
    page_count = math.ceil(item_count / size)
    print('[%s]%s items, %s pages' % (hp.get_date_time(), item_count, page_count))
    for i in range(page_count):
        print('[%s]processing page %s / %s' % (hp.get_date_time(), i + 1, page_count))
        fields = ['name', 'blocks', 'columns']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for p in pages:
            print('[%s]%s' % (hp.get_date_time(), p['name']))
            # 更新子列的column_id
            if not p.get('columns'):
                continue
            for c in p.get('columns'):
                if c.get('sub_columns'):
                    for s in c['sub_columns']:
                        s['column_id'] = s['column_id'].replace('#', 's')
                    db.page.update_one({'_id': p['_id']}, {'$set': {'columns': p['columns'], 'updated': True}})


def apply_ocr_col(db, source=None):
    """ 将ocr_col适配至page['chars']"""
    size = 1000
    cond = {'source': source}
    item_count = db.page.count_documents(cond)
    page_count = math.ceil(item_count / size)
    print('[%s]%s items, %s pages' % (hp.get_date_time(), item_count, page_count))
    for i in range(page_count):
        print('[%s]processing page %s / %s' % (hp.get_date_time(), i + 1, page_count))
        fields = ['name', 'blocks', 'columns', 'chars']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for p in pages:
            print('[%s]%s' % (hp.get_date_time(), p['name']))
            mis_len = Ph.apply_ocr_col(p)
            db.page.update_one({'_id': p['_id']}, {'$set': {
                'chars': p['chars'], 'txt_match.ocr_col.mis_len': mis_len, 'updated': True
            }})


def update_page_txt(db, source=None):
    """ 更新page['chars']的txt字段"""
    size = 1000
    cond = {'source': source}
    item_count = db.page.count_documents(cond)
    page_count = math.ceil(item_count / size)
    print('[%s]%s items, %s pages' % (hp.get_date_time(), item_count, page_count))
    for i in range(page_count):
        print('[%s]processing page %s / %s' % (hp.get_date_time(), i + 1, page_count))
        fields = ['name', 'chars']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for p in pages:
            print('[%s]%s' % (hp.get_date_time(), p['name']))
            if p.get('chars'):
                for c in p.get('chars'):
                    c['cmb_txt'] = Ch.get_cmb_txt(c)
                    if not c.get('txt_logs'):
                        c['txt'] = c['cmb_txt']
                db.page.update_one({'_id': p['_id']}, {'$set': {'chars': p['chars']}})


def statistic_chars(db):
    total = 0
    size = 10000
    cond = {'name': {'$regex': 'JS_'}}
    item_count = db.page.count_documents(cond)
    page_count = math.ceil(item_count / size)
    print('[%s]%s items, %s pages' % (hp.get_date_time(), item_count, page_count))
    for i in range(page_count):
        print('[%s]processing page %s / %s' % (hp.get_date_time(), i + 1, page_count))
        fields = ['name', 'chars']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for p in pages:
            if p.get('chars'):
                cnt = len([c for c in p.get('chars') if not c.get('deleted')])
                print('[%s]%s, %s' % (hp.get_date_time(), p['name'], cnt))
                total += cnt
    print('total count: %s' % total)


def update_source_by_task(db):
    """根据任务设置页数据的分类"""
    # 径山藏
    cond = {'task_type': 'cut_proof', 'num': 1, 'doc_id': {'$regex': 'JS_'}}
    print('径山藏切分校对#一校：', db.task.count_documents(cond))
    # 全职校对人员
    users1 = list(db.user.find({'group': '全职校对人员'}, {'_id': 1, 'name': 1}))
    print('全职校对人员：', '，'.join([u['name'] for u in users1]))
    tasks1 = list(db.task.find({**cond, 'picked_user_id': {'$in': [u['_id'] for u in users1]}}, {'doc_id': 1}))
    print('完成任务总数：', len(tasks1))
    page_names1 = [t['doc_id'] for t in tasks1]
    db.page.update_many({'name': {'$in': page_names1}}, {'$set': {'source': '径山藏-全职'}})
    # 实习学生
    users2 = list(db.user.find({'group': '实习学生'}, {'_id': 1, 'name': 1}))
    print('实习学生：', '，'.join([u['name'] for u in users2]))
    tasks2 = list(db.task.find({**cond, 'picked_user_id': {'$in': [u['_id'] for u in users2]}}, {'doc_id': 1}))
    print('完成任务总数：', len(tasks2))
    page_names2 = [t['doc_id'] for t in tasks2]
    db.page.update_many({'name': {'$in': page_names2}, 'source': {'$ne': '径山藏-全职'}},
                        {'$set': {'source': '径山藏-学生'}})
    # 义工
    users3 = [u['_id'] for u in users1] + [u['_id'] for u in users2]
    tasks3 = list(db.task.find({**cond, 'picked_user_id': {'$nin': users3}}, {'doc_id': 1}))
    print('其它人完成任务总数：', len(tasks3))
    page_names3 = [t['doc_id'] for t in tasks3]
    db.page.update_many({'name': {'$in': page_names3}, 'source': {'$nin': ['径山藏-全职', '径山藏-学生']}},
                        {'$set': {'source': '径山藏-义工'}})


def update_source_by_nav(db):
    """根据任务浏览设置页数据的分类"""
    cond = {'task_type': 'cut_proof', 'num': 1, 'doc_id': {'$regex': 'JS_'}, 'nav_times': {'$gte': 1}}
    print('已完成自查任务数：', db.task.count_documents(cond))
    tasks = list(db.task.find(cond, {'doc_id': 1}))
    page_names = [t['doc_id'] for t in tasks]
    db.page.update_many({'name': {'$in': page_names}, 'source': '径山藏-全职'},
                        {'$set': {'source': '径山藏-全职-已自查'}})


def main(db_name='tripitaka', uri='localhost', func='', **kwargs):
    db = pymongo.MongoClient(uri)[db_name]
    eval(func)(db, **kwargs)


if __name__ == '__main__':
    import fire

    fire.Fire(main)
