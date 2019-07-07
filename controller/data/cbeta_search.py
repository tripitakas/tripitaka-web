#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from yaml import load, SafeLoader
import os.path as path
from controller.data.diff import Diff
from controller.data.variant import normalize
from elasticsearch import Elasticsearch


def get_search_host():
    base_dir = path.dirname(path.dirname(path.dirname(__file__)))
    cfg_file = path.join(base_dir, 'app.yml')
    with open(cfg_file, 'r') as f:
        cfg = load(f, Loader=SafeLoader)
        return [cfg.get('cbeta')]


def find(q, index='cb4ocr-ik'):
    """ 从ES中寻找与q最匹配的document """
    if not q:
        return []

    if re.match(r'^[0-9a-zA-Z_]+', q):
        match = {'page_code': q}
    else:
        ocr = re.sub(r'[\x00-\xff]', '', q)
        ocr = re.sub(Diff.junk_cmp_str, '', ocr)
        match = {'normal': normalize(ocr)}

    dsl = {
        'query': {'match': match},
        'highlight': {'pre_tags': ['<kw>'], 'post_tags': ['</kw>'], 'fields': {'normal': {}}}
    }

    es = Elasticsearch(hosts=get_search_host())
    r = es.search(index=index, body=dsl)

    return r['hits']['hits']


def find_one(ocr, num=1):
    """ 从ES中寻找与ocr最匹配的document，返回第num个结果 """
    ret = find(ocr)
    if not ret or num - 1 not in range(0, len(ret)):
        return ''
    cb = ''.join(ret[num - 1]['_source']['origin'])
    diff = Diff.diff(ocr, cb, label=dict(base='ocr', cmp1='cb'))[0]
    txt = ''.join(['<kw>%s</kw>' % d['cb'] if d.get('is_same') else d['cb'] for d in diff])
    cmp_page_code = ret[num - 1]['_source']['page_code']
    return txt, cmp_page_code


def find_neighbor(page_code, neighbor='next'):
    """ 从ES中寻找page_code的前一页或后一页记录 """
    assert neighbor in ['prev', 'next']
    head = re.search(r'^([A-Z]{1,2}\d+n[A-Z]?\d+[A-Za-z_]?)p([a-z]?\d+)', page_code)
    page_no = head.group(2)
    neighbor_no = str(int(page_no) + 1 if neighbor == 'next' else int(page_no) - 1).zfill(len(page_no))
    neighbor_code = '%sp%s' % (head.group(1), neighbor_no)
    return find(neighbor_code)[0]


if __name__ == '__main__':
    print([r['_source'] for r in find('由業非以自性滅，故無賴耶亦能生', None)])