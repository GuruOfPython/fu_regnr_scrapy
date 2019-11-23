# -*- coding: utf-8 -*-

# Scrapy settings for fu_regnr project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'fu_regnr'

SPIDER_MODULES = ['fu_regnr.spiders']
NEWSPIDER_MODULE = 'fu_regnr.spiders'

ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
# DOWNLOAD_DELAY = 1
dont_filter = True
# RETRY_ENABLED = True
COOKIES_ENABLED = True
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

DOWNLOADER_MIDDLEWARES = {
    'scrapy_crawlera.CrawleraMiddleware': 610,
}
# CRAWLERA_ENABLED = True
CRAWLERA_APIKEY = 'b53dfcfc223c403096ecf19c679bcde3'

ITEM_PIPELINES = {
    'fu_regnr.pipelines.FuRegnrPipeline': 0,
}
