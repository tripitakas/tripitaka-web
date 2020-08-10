#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
from os import path
from tornado.options import options
from elasticsearch import Elasticsearch

BASE_DIR = path.dirname(path.dirname(path.dirname(path.dirname(__file__))))
sys.path.append(BASE_DIR)

from controller.helper import load_config
from controller.page.tool.diff import Diff
from controller.page.tool.variant import normalize


def get_hosts():
    config = load_config() or {}
    hosts = [config.get('esearch')]
    if hasattr(options, 'testing') and options.testing:
        hosts = [dict(host='dev.tripitakas.net')]
    return hosts


def find(q, index='cb4ocr-ik'):
    """ 从ES中寻找与q最匹配的document """
    if not q:
        return []

    if re.match(r'^[0-9a-zA-Z_]+', q):
        match = {'page_code': q}
    else:
        ocr = re.sub(r'[\x00-\xff]', '', q)
        ocr = re.sub(Diff.cmp_junk_char, '', ocr)
        match = {'normal': normalize(ocr)}

    dsl = {
        'query': {'match': match},
        'highlight': {'pre_tags': ['<kw>'], 'post_tags': ['</kw>'], 'fields': {'normal': {}}}
    }

    es = Elasticsearch(hosts=get_hosts())
    r = es.search(index=index, body=dsl)

    return r['hits']['hits']


def find_one(ocr, num=1):
    """ 从ES中寻找与ocr最匹配的document，返回第num个结果 """
    ocr = ''.join(ocr) if isinstance(ocr, list) else ocr.replace('|', '')
    ret = find(ocr)
    if not ret or num - 1 not in range(0, len(ret)):
        return '', []
    hit_page_codes = [r['_source']['page_code'] for r in ret]
    cb = ''.join(ret[num - 1]['_source']['origin'])
    diff = Diff.diff(ocr, cb, label=dict(base='ocr', cmp1='cb'))[0]
    txt = ''.join(['<kw>%s</kw>' % d['cb'] if d.get('is_same') else d['cb'] for d in diff])
    return txt.strip('\n'), hit_page_codes


def find_neighbor(page_code, neighbor='next'):
    """ 从ES中寻找page_code的前一页或后一页记录 """
    assert neighbor in ['prev', 'next']
    head = re.search(r'^([A-Z]{1,2}\d+n[A-Z]?\d+[A-Za-z_]?)p([a-z]?\d+)', page_code)
    page_no = head.group(2)
    neighbor_no = str(int(page_no) + 1 if neighbor == 'next' else int(page_no) - 1).zfill(len(page_no))
    neighbor_code = '%sp%s' % (head.group(1), neighbor_no)
    neighbor_node = find(neighbor_code)
    return neighbor_node and neighbor_node[0]


def find_match(ocr):
    """ 从cbeta文中找出与ocr匹配的文本"""
    ocr = ''.join(ocr) if isinstance(ocr, list) else ocr.replace('|', '')
    if len(ocr) < 10 or (len(ocr) < 20 and re.findall(r'[第苐][一二三四五六七八九十]+[張张]', ocr)):
        return ''
    ret = find(ocr)
    if not ret:
        return ''
    cb = ''.join(ret[0]['_source']['origin'])
    diff = Diff.diff(ocr, cb, label=dict(base='ocr', cmp1='cb'))[0]
    # 寻找第一个和最后一个同文
    start, end = 0, 0
    for i, d in enumerate(diff):
        if d.get('is_same') and len(d['ocr']) > 2 and not start:
            start = i
        if diff[-i - 1].get('is_same') and len(diff[-i - 1]['ocr']) > 2 and not end:
            end = len(diff) - i - 1
        if start and end:
            break
    match = ''
    if start > 0:
        _ocr = ''.join([d['ocr'] for d in diff[:start]])
        match1 = find_match(_ocr)
        match += match1
    if end >= start:
        match2 = ''.join([d['cb'] for d in diff[start:end + 1]])
        match += match2
    if end + 1 < len(diff):
        _ocr = ''.join([d['ocr'] for d in diff[end + 1:]])
        match3 = find_match(_ocr)
        match += match3
    return match


if __name__ == '__main__':
    ocr_txt = '薩行依深入剿切波羅蜜行巷薩行依一切|菩薩滿足諸願行菩薩行依無量菩提心行|菩薩行依一切諸佛菩提行菩薩行佛子是|爲菩薩摩訶薩十種依止菩薩依此行菩薩行|佛子菩薩摩訶薩有十種發無畏心何等爲|十所謂滅一切業障發無畏心佛滅度後受|持守護正法發無畏心降一切魔發無畏心|不惜身命發無畏心如法調伏一切外道發|無畏心令二切衆生皆悉歡喜發無畏心令|一切大衆皆悉歡喜發無畏心調伏一切天|龍夜义乾闥婆阿脩羅迦樓羅緊那羅摩睺|羅伽發無畏心遠離聲聞緣覺地入甚深法'
    res = find_match(ocr_txt)
    print(res)
