# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest
import requests
from time import sleep, time
from lxml import html
import csv
from os.path import dirname, abspath
from fu_regnr.pipelines import FuRegnrPipeline
from fu_regnr.items import FuRegnrItem
from inline_requests import inline_requests

def make_headers_1():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
    }
    return headers


def make_headers_2():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    return headers


class FuRegnrScrapySpider(scrapy.Spider):
    name = 'fu-regnr_scrapy'
    allowed_domains = []
    start_urls = []

    def __init__(self):
        # self.input_data = csv.reader(open(dirname(abspath(__file__)) + '/' + 'Test.csv', 'r', encoding='utf-8'))
        # self.input_data = csv.reader(open('Test.csv', 'r', encoding='utf-8'))
        r = requests.get('https://file-post.net/en/p0/d1/1574367207_221136163_48/dir/Test.csv')
        self.input_data = list(csv.reader(r.content.decode().splitlines(), delimiter=','))
        self.result_file_name = dirname(abspath(__file__)) + '/' + 'Result.csv'
        self.already_list = []
        try:
            with open(self.result_file_name, 'r') as f:
                self.already_list = [line[0] for line in csv.reader(f)]
        except:
            pass

        if not self.already_list:
            heading = ['Registreringsnummer', 'Försäkringsbolag', 'Försäkringsdatum']
            self.insert_row(result_row=heading)

        self.api_key = '843e38cc8b492d76f1b4c809c6bbfe7d'
        self.google_key = '6Ld3rbsUAAAAAHAu6XLBz6HeF44fZmaoTMWw6qjM'

        self.get_url = "https://fu-regnr.transportstyrelsen.se/extweb/UppgifterAnnatFordon"
        self.post_url = "https://fu-regnr.transportstyrelsen.se/extweb/UppgifterAnnatFordon/Fordonsuppgifter"

        self.captcha_in = "http://2captcha.com/in.php"
        self.captcha_res = "http://2captcha.com/res.php?key={}&action=get".format(self.api_key) + "&id={}"

        self.max_resp_cnt = 20
        self.resp_time = 5
        self.total_cnt = 0

    # @inline_requests
    def start_requests(self):
        self.input_data.reverse()
        while self.input_data:
            line = self.input_data.pop()
            Registreringsnummer = line[18]
            self.total_cnt += 1
            print("[{}] Scanning ...".format(Registreringsnummer))
            if Registreringsnummer in self.already_list or Registreringsnummer == 'Registreringsnummer':
                print("\t[Already {}] {}".format(self.total_cnt, Registreringsnummer))
            else:
                break

        request = FormRequest(
            url=self.get_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get__RequestVerificationToken,
            errback=self.fail__RequestVerificationToken,
            dont_filter=True,
            meta={
                'Registreringsnummer': Registreringsnummer,
            }
        )
        yield request

    @inline_requests
    def get__RequestVerificationToken(self, response):
        Registreringsnummer = response.meta['Registreringsnummer']

        __RequestVerificationToken = response.xpath(
            '//input[@name="__RequestVerificationToken"]/@value').extract_first()

        try:
            self.cookie = response.headers[b'Set-Cookie'].decode()
        except:
            self.cookie = ""

        formdata = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': self.google_key,
            'pageurl': self.post_url,
        }

        request = FormRequest(
            url=self.captcha_in,
            method='GET',
            formdata=formdata,
            headers=make_headers_1(),
            callback=self.get_captcha_id,
            errback=self.fail_captcha_id,
            dont_filter=True,
            meta={
                'Registreringsnummer': Registreringsnummer,
                'dont_proxy': True,
            }
        )
        yield request


    @inline_requests
    def fail__RequestVerificationToken(self, failure):
        Registreringsnummer = failure.request.meta['Registreringsnummer']

        request = FormRequest(
            url=self.get_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get__RequestVerificationToken,
            errback=self.fail__RequestVerificationToken,
            dont_filter=True,
            meta={
                'Registreringsnummer': Registreringsnummer,
            }
        )
        yield request

    @inline_requests
    def get_captcha_id(self, response):
        Registreringsnummer = response.meta['Registreringsnummer']

        if response.text[0:2] != 'OK':
            print('Error. Captcha is not received')
            return

        captcha_id = response.text.split('|')[1]

        sleep(self.resp_time)
        fetch_url = "http://2captcha.com/res.php?key={}&action=get&id={}".format(self.api_key, captcha_id)
        resp_cnt = 0
        request = FormRequest(
            url=fetch_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get_recaptchaClientToken,
            errback=self.fail_recaptchaClientToken,
            dont_filter=True,
            meta={
                'fetch_url': fetch_url,
                'Registreringsnummer': Registreringsnummer,
                'captcha_id': captcha_id,
                'resp_cnt': resp_cnt,
                'dont_proxy': True,
            }
        )
        yield request

    @inline_requests
    def fail_captcha_id(self, failure):
        url = failure.request.meta['url']
        Registreringsnummer = failure.request.meta['Registreringsnummer']

        formdata = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': self.google_key,
            'pageurl': self.post_url,
            # 'proxy': 'http://1f7a28e9aa7446c491a11b8328a5ced7:@proxy.crawlera.com:8010/',
            'proxytype': 'http'
        }
        request = FormRequest(
            url=url,
            method='POST',
            formdata=formdata,
            headers=make_headers_1(),
            callback=self.get_captcha_id,
            errback=self.fail_captcha_id,
            dont_filter=True,
            meta={
                'url': url,
                'Registreringsnummer': Registreringsnummer,
                'dont_proxy': True,
            }
        )
        yield request


    def insert_row(self, result_row):
        result_file = open('Result.csv', 'a', encoding='utf-8', newline='')
        self.out_writer = csv.writer(result_file)
        self.out_writer.writerow(result_row)
        result_file.close()


if __name__ == '__main__':
    from scrapy.utils.project import get_project_settings
    from scrapy.crawler import CrawlerProcess, CrawlerRunner

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(FuRegnrScrapySpider)
    process.start()
