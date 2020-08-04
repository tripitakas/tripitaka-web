#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python3 utils/update_page.py --uri=uri --func=init_variants
# 更新数据库的page表

import re
import sys
import math
import json
import pymongo
from os import path, walk
from operator import itemgetter
from functools import cmp_to_key

BASE_DIR = path.dirname(path.dirname(__file__))
sys.path.append(BASE_DIR)

from controller import helper as hp
from controller.page.base import PageHandler as Ph


def reorder_boxes(db, name=None):
    """ 切分框(包括栏框、列框、字框)重新排序"""
    size = 10
    cond = {'name': {'$regex': name}} if name else {}
    page_count = math.ceil(db.page.count_documents(cond) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        fields = ['name', 'width', 'height', 'blocks', 'columns', 'chars']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for page in pages:
            print('[%s]processing %s' % (hp.get_date_time(), page['name']))
            Ph.reorder_boxes(page=page)
            fields = ['blocks', 'columns', 'chars']
            db.page.update_one({'_id': page['_id']}, {'$set': {k: page.get(k) for k in fields}})


def update_sub_columns(db, name=None):
    """ 对于未设置sub_columns的情况，算法排序后，更新sub_columns"""
    size = 10
    cond = {'name': {'$regex': name}} if name else {}
    page_count = math.ceil(db.page.count_documents(cond) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        fields = ['name', 'width', 'height', 'blocks', 'columns', 'chars']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for page in pages:
            print('[%s]processing %s' % (hp.get_date_time(), page['name']))
            if not page.get('columns'):
                print('no columns')
                continue
            has_sub_columns = [c for c in page['columns'] if c.get('sub_columns')]
            if has_sub_columns:
                print('has sub columns')
                continue
            Ph.reorder_boxes(page=page)
            new_sub_columns = [c for c in page['columns'] if c.get('sub_columns')]
            if not new_sub_columns:
                print('algorithm no sub columns')
                continue
            db.page.update_one({'_id': page['_id']}, {'$set': {'columns': page['columns']}})
            print('sub columns updated')


def check_box_cover(db):
    """ 检查切分框(包括栏框、列框、字框)的覆盖情况"""
    size = 10
    page_count = math.ceil(db.page.count_documents({}) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        fields = ['name', 'width', 'height', 'blocks', 'columns', 'chars']
        pages = list(db.page.find({}, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for page in pages:
            print('[%s]processing %s' % (hp.get_date_time(), page['name']))
            valid, message, field, invalid_ids = Ph.check_box_cover(page)
            if not valid:
                print('%s: %s' % (message, invalid_ids))


def check_chars_col(db):
    """ 检查用户字序和算法字序是否一致"""

    def cmp_chars_col(chars_cols1, chars_cols2):
        if len(chars_cols1) != len(chars_cols2):
            return False
        for n, chars_col1 in enumerate(chars_cols1):
            for m, cid1 in enumerate(chars_col1):
                cid2 = chars_cols2[n][m] if len(chars_cols2[n]) > m else 0
                if cid1 != cid2:
                    return False
        return True

    size = 10
    page_count = math.ceil(db.page.count_documents({}) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        fields = ['name', 'width', 'height', 'blocks', 'columns', 'chars']
        pages = list(db.page.find({}, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for page in pages:
            print('[%s]processing %s' % (hp.get_date_time(), page['name']))
            old_chars_col = Ph.get_chars_col(page['chars'])
            blocks, columns, chars = Ph.reorder_boxes(page=page)
            new_chars_col = Ph.get_chars_col(chars)
            if not cmp_chars_col(old_chars_col, new_chars_col):
                print('invalid:', page['name'])


def update_cid(db):
    """ 更新切分框(包括栏框、列框、字框)的cid"""
    size = 10
    page_count = math.ceil(db.page.count_documents({}) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        project = {'name': 1, 'chars': 1, 'blocks': 1, 'columns': 1}
        pages = list(db.page.find({}, project).sort('_id', 1).skip(i * size).limit(size))
        for page in pages:
            print('[%s]processing %s' % (hp.get_date_time(), page['name']))
            updated = Ph.update_page_cid(page)
            if updated:
                update = {k: page.get(k) for k in ['chars', 'columns', 'blocks']}
                db.page.update_one({'_id': page['_id']}, {'$set': update})


def update_order_and_cid(db):
    """ 根据block_no/column_no/char_no等重新排序，按照顺序重新设置cid。
        如果有用户字序，则用新的cid同步更新用户字序
    """

    def cmp_char(a, b):
        for f in ['block_no', 'column_no', 'char_no']:
            s = int(a.get(f) or 10000) - int(b.get(f) or 10000)
            if s != 0:
                return s
        return False

    size = 1000
    cond = {'name': {'$regex': 'JS_'}}
    page_count = math.ceil(db.page.count_documents(cond) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        project = {'name': 1, 'chars': 1, 'blocks': 1, 'columns': 1, 'chars_col': 1}
        pages = list(db.page.find(cond, project).sort('_id', 1).skip(i * size).limit(size))
        for p in pages:
            print('[%s]processing %s' % (hp.get_date_time(), p['name']))
            if p['chars'][0].get('char_id') == 'b1c1c1':
                continue
            p['blocks'].sort(key=itemgetter('block_no'))
            p['columns'].sort(key=itemgetter('block_no', 'column_no'))
            p['chars'].sort(key=cmp_to_key(cmp_char))
            trans_cid = dict()
            no_error = True
            for n, c in enumerate(p['chars']):
                try:
                    trans_cid[c['cid']] = n + 1
                    c['cid'] = n + 1
                except KeyError:
                    no_error = False
                    print('key error: %s' % c)
            update = dict(blocks=p['blocks'], columns=p['columns'], chars=p['chars'])
            if p.get('chars_col'):
                chars_col = []
                for row in p['chars_col']:
                    try:
                        chars_col.append([trans_cid[cid] for cid in row])
                    except KeyError:
                        no_error = False
                        print('key error: %s' % row)
                update['chars_col'] = chars_col
            if no_error:
                db.page.update_one({'_id': p['_id']}, {'$set': update})


def update_task_char_count(db):
    """ 更新页任务的char_count"""
    tasks = db.task.find({'char_count': None, 'collection': 'page'}, {'doc_id': 1})
    names = [p['doc_id'] for p in list(tasks)]
    pages = db.page.find({'name': {'$in': names}}, {'chars': 1, 'name': 1})
    print('[%s]%s pages to process' % (hp.get_date_time(), len(pages)))
    for page in pages:
        print('[%s]processing %s' % (hp.get_date_time(), page['name']))
        db.task.update_many({'char_count': None, 'collection': 'page', 'doc_id': page['name']},
                            {'$set': {'char_count': len(page['chars'])}})


def trim_ocr_fields(db, name=None):
    """ 去掉切分框中ocr_x,ocr_y,ocr_w,ocr_h等字段"""
    size = 10
    cond = {'name': {'$regex': name}} if name else {}
    page_count = math.ceil(db.page.count_documents(cond) / size)
    print('[%s]%s pages to process' % (hp.get_date_time(), page_count))
    for i in range(page_count):
        fields = ['name', 'width', 'height', 'blocks', 'columns', 'chars']
        pages = list(db.page.find(cond, {k: 1 for k in fields}).sort('_id', 1).skip(i * size).limit(size))
        for page in pages:
            print('[%s]processing %s' % (hp.get_date_time(), page['name']))
            if not page.get('chars'):
                print('no chars')
                continue
            cnt1 = len([c for c in page['columns'] if c.get('ocr_x')])
            cnt2 = len([c for c in page['chars'] if c.get('ocr_x')])
            if not (cnt1 + cnt2):
                print('no ocr_x etc')
                continue
            fields = 'ocr_x,ocr_y,ocr_w,ocr_h'
            Ph.pop_fields(page['columns'], fields)
            Ph.pop_fields(page['chars'], fields)
            db.page.update_one({'_id': page['_id']}, {'$set': {k: page[k] for k in ['columns', 'chars']}})
            print('ocr_x etc updated')


def update_sub_columns_txt(db, json_path=''):
    """ 更新page表sub_columns的ocr_txt"""
    for root, dirs, files in walk(json_path):
        for fn in files:
            if fn.endswith('.json'):
                print('[%s]processing %s' % (hp.get_date_time(), fn))
                page = db.page.find_one({'name': fn.split('.')[0]})
                if not page:
                    print('no page in db')
                    continue
                columns = page['columns']
                with open(path.join(root, fn), encoding='UTF-8') as f:
                    info = json.load(f)
                    for col in info.get('columns', []):
                        if col.get('sub_columns') and len(col['sub_columns']) > 1:
                            page_column = [c for c in columns if c['cid'] == col['cid']][0]
                            assert len(page_column['sub_columns']) == len(col['sub_columns'])
                            page_column['sub_columns'] = col['sub_columns']
                db.page.update_one({'_id': page['_id']}, {'$set': {'columns': columns}})


def main(db_name='tripitaka', uri='localhost', func='', **kwargs):
    db = pymongo.MongoClient(uri)[db_name]
    eval(func)(db, **kwargs)


if __name__ == '__main__':
    import fire

    fire.Fire(main)
