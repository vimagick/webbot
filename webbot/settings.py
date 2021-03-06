#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# A simple spider written by Kev++

BOT_NAME = 'webbot'
LOG_LEVEL = 'INFO'

SPIDER_MODULES = ['webbot.spiders']
NEWSPIDER_MODULE = 'webbot.spiders'

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0'

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh,en;q=0.5',
}

ITEM_PIPELINES = {
    'webbot.pipelines.BasicPipeline': 0,
    'webbot.pipelines.MongoPipeline': 1,
    'webbot.pipelines.MysqlPipeline': 2,
    'webbot.pipelines.ZmqPipeline': 3,
    'webbot.pipelines.DebugPipeline': 9,
}

try:
    from scrapy.contrib.pipeline.images import ImagesPipeline
    ITEM_PIPELINES['webbot.pipelines.ImgPipeline'] = 4
except:
    pass

EXTENSIONS = {
    'scrapy.webservice.WebService': None,
    'scrapy.telnet.TelnetConsole': None,
    'webbot.extensions.StatsPoster': 999,
}

DOWNLOADER_MIDDLEWARES = {
    'webbot.middlewares.RequestMiddleware': 0,
    'webbot.middlewares.DedupMiddleware': 999,
    'webbot.middlewares.ProxyMiddleware': 999,
}

SPIDER_MIDDLEWARES = {
    'webbot.middlewares.KeywordRelayMiddleware': 999,
}

WEBSERVICE_ENABLED = False
TELNETCONSOLE_ENABLED = False
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 2

DEFAULT_LOGGER = None #'mongodb://localhost:27017/result.data'
DEFAULT_DEDUP = None

FEED_URI_PARAMS = 'webbot.utils.utils.feed_uri_params_parser'
IMAGES_STORE = '/tmp'
