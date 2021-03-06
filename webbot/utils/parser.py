#!/usr/bin/env python
# -*- coding: utf-8 -*-

from HTMLParser import HTMLParser
from datetime import datetime
from functools import partial
from jsonpath import jsonpath
from lxml import html
from lxml.html.clean import Cleaner
from scrapy import log
from scrapy.contrib.loader.processor import *
from scrapy.utils.markup import remove_tags
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import flatten
import base64
import inspect
import re
import requests
import sys

try:
    from webbot.utils.dateparser import parse_date
except:
    pass

try:
    import simplejson as json
except ImportError:
    import json

class BaseParser(object):

    def __init__(self, inf):

        assert self.__class__.__name__.endswith('Parser')
        self.inf = inf

    def parse(self, data):

        return data
    
    def __call__(self, data):

        return flatten(MapCompose(self.parse)(data))

class GrepParser(BaseParser):

    def parse(self, data):

        return re.findall(self.inf.get('pattern', '.+'), data)

class HeadParser(BaseParser):

    def __call__(self, data):

        return data[:1]

class TailParser(BaseParser):

    def __call__(self, data):

        return data[1:]

class LastParser(BaseParser):

    def __call__(self, data):

        return data[-1:]

class LenParser(BaseParser):

    def __call__(self, data):

        return len(data)

class JoinParser(BaseParser):

    def __call__(self, data):

        data = BaseParser.__call__(self, data)
        sep = self.inf.get('sep', u' ')
        return [Join(sep)(data)]

class ListParser(BaseParser):

    def parse(self, data):

        return remove_tags(data).strip()

    def __call__(self, data):

        data = BaseParser.__call__(self, data)
        sep = self.inf.get('sep', u' ')
        return [Join(sep)(data)]

class HttpParser(BaseParser):

    def parse(self, data):

        url = data
        m = self.inf.get('method', 'get').upper()
        d = self.inf.get('data', {})
        e = self.inf.get('enc', 'utf-8')
        if m=='GET':
            return requests.get(url).content.decode(e)
        elif m=='POST':
            return requests.get(url, data=d).content.decode(e)
        else:
            return data

class MapParser(BaseParser):

    def parse(self, data):

        m = self.inf.get('map')
        d = self.inf.get('default')
        for k,v in m.iteritems():
            if not k.startswith('^'):
                k = '.*'+k
            if not k.endswith('$'):
                k = k+'.*'
            if re.search(k, data):
                return re.sub(k, v, data)
        else:
            return d

class XpathParser(BaseParser):

    def parse(self, data):

        qs = self.inf['query']
        dom = html.fromstring(data)
        return dom.xpath(qs)

class PurgeParser(BaseParser):

    def parse(self, data):

        qs = self.inf['query']
        dom = html.fromstring(data)
        es = dom.xpath(qs)
        for e in es:
            if e in dom:
                dom.remove(e)
        return html.tostring(dom, encoding=unicode)

class JpathParser(BaseParser):

    def parse(self, data):

        qs = self.inf.get('query')
        t = self.inf.get('type', 'object')
        if t=='object':
            lr = '{}'
        else:
            lr = '[]'
        l,r = data.find(lr[0]),data.rfind(lr[-1])
        data = data[l:r+1]
        return jsonpath(json.loads(data), qs)

class FloatParser(BaseParser):

    def parse(self, data):

        try:
            data = data.replace(',', '')
            data = re.search(r'([+-])?\s*[.0-9]+', data).group(0)
            return float(data)
        except:
            return 0.0

class IntParser(BaseParser):

    def parse(self, data):

        try:
            data = data.replace(',', '')
            data = re.search(r'([+-])?\s*[0-9]+', data).group(0)
            return int(data)
        except:
            return 0

class EpochParser(BaseParser):

    def parse(self, data):

        try:
            zero = datetime.utcfromtimestamp(0)
            epoch = int((data-zero).total_seconds())
            return epoch
        except:
            return 0

class DefaultParser(BaseParser):

    def parse(self, data):

        if not data:
            return self.inf.get('value')
        else:
            return data

class UnescParser(BaseParser):

    def parse(self, data):

        return HTMLParser().unescape(data)

class DateParser(BaseParser):

    def parse(self, data):

        fmt = self.inf.get('fmt', 'auto')
        tz = self.inf.get('tz', '+00:00')
        return parse_date(data, fmt, tz)

class CstParser(BaseParser):

    def parse(self, data):

        fmt = self.inf.get('fmt', 'auto')
        tz = '+08:00'
        return parse_date(data, fmt, tz)

class Base64Parser(BaseParser):

    def parse(self, data):
        return base64.decodestring(data)

class CleanParser(BaseParser):

    def parse(self, data):
        try:
            cleaner = Cleaner(style=True, scripts=True, javascript=True, links=True, meta=True)
            return cleaner.clean_html(data)
        except:
            return data

class SubParser(BaseParser):

    def __init__(self, inf):

        super(SubParser, self).__init__(inf)
        self.fm = self.inf['from']
        self.to  = arg_to_iter(self.inf['to'])
        #self.parse = partial(re.sub, fm, to)

    def parse(self, data):

        for to in self.to:
            yield re.sub(self.fm, to, data)

class TextParser(BaseParser):

    def parse(self, data):
        if type(data) not in [str, unicode]:
            data = str(data)
        return remove_tags(data).strip()

class StrParser(BaseParser):

    def parse(self, data):
        if type(data) in [str, unicode]:
            data = data.strip()
        if not isinstance(data, unicode):
            data = unicode(str(data), encoding='utf-8')
        return data

class StringParser(BaseParser):

    def parse(self, data):
        method = self.inf['method']
        args = self.inf.get('args', [])
        kwargs = self.inf.get('kwargs', {})
        return getattr(data, method)(*args, **kwargs)

class TrimParser(BaseParser):

    def parse(self, data):
        return data.strip()

class NormParser(BaseParser):

    def parse(self, data):
        return re.sub(r'\s+', ' ', data).strip()

class FilterParser(BaseParser):

    def filter(self, op, x, y):

        if self.inf.get('swap'):
            x,y = y,x

        return {
            '$in':  lambda: x in y,
            '$nin': lambda: x not in y,
            '$eq':  lambda: x == y,
            '$ne':  lambda: x != y,
            '$lt':  lambda: x < y,
            '$lte': lambda: x <= y,
            '$gt':  lambda: x > y,
            '$gte': lambda: x >= y,
            '$regex': lambda: re.search(y, x),
        }[op]()

    def parse(self, data):

        for k,v in self.inf.iteritems():

            if k in ['type', 'args', 'kwargs', 'not', 'swap']:
                continue
            elif k=='delta':
                now = datetime.utcnow()
                ok = (now-data).total_seconds()<v
            elif k=='string':
                args = self.inf.get('args', [])
                kwargs = self.inf.get('kwargs', {})
                ok = getattr(data, v)(*args, **kwargs)
            elif k.startswith('$'):
                ok = self.filter(k, data, v)
            else:
                log.msg(u'invalid operator <{}>'.format(k), level=log.WARNING)
                continue

            if self.inf.get('not'):
                ok = not ok
            if not ok:
                return

        return data

class TeeParser(BaseParser):

    def __init__(self, inf):

        super(TeeParser, self).__init__(inf)
        self.parsers = [make_parser(i) for i in self.inf['tee']]

    def parse(self, data):

        for p in self.parsers:
            yield p(data)

class PipeParser(BaseParser):

    def __init__(self, inf):

        super(PipeParser, self).__init__(inf)
        self.parsers = [make_parser(i) for i in self.inf]
        self.func = Compose(*self.parsers)

    def __call__(self, data):
        return self.func(data)

all_parsers = {
    cname[0:-6].lower():cls\
        for cname,cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)\
            if issubclass(cls, BaseParser) and cname.endswith('Parser')
}

def make_parser(inf):

    if isinstance(inf, list):
        return PipeParser(inf)
    elif isinstance(inf, str) or isinstance(inf, unicode):
        if hasattr(str, inf):
            inf = {'type':'string', 'method':inf}
        else:
            inf = {'type':inf}
        return make_parser(inf)
    else:
        Parser = all_parsers.get(inf.get('type'), BaseParser)
        return Parser(inf)

if __name__=='__main__':

    data = ['<script>hello</script><p>   fff:oooo  </p>', 'b<i>bb</i>bb', 'foobar808foobar', u'今天::333', u'昨天']
    inf = [u'text', 'int', {'type':'filter', 'min':500}, 'head']
    parser = make_parser(inf)
    print data
    print parser(data)

