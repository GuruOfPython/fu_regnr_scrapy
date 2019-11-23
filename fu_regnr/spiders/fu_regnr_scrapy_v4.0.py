# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest
import requests
from time import sleep, time
from lxml import html
import csv
from os.path import dirname, abspath
import pkgutil

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
        r = requests.get('https://file-post.net/en/p0/d1/1573853892_75879959_48/dir/Test.csv')
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

        self.max_resp_cnt = 20
        self.resp_time = 5
        self.total_cnt = 0

    def start_requests(self):
        for i, line in enumerate(self.input_data):
            if i == 0:
                continue
            Registreringsnummer = line[18]
            print("[{}] Scanning ...".format(Registreringsnummer))
            if Registreringsnummer in self.already_list:
                print("\t[Already {}] {}".format(i, Registreringsnummer))
                continue

            url = "http://2captcha.com/in.php"

            formdata = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': self.google_key,
                'pageurl': self.post_url,
                'proxy': 'http://1f7a28e9aa7446c491a11b8328a5ced7:@proxy.crawlera.com:8010/',
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
                    'Registreringsnummer': Registreringsnummer
                }
            )
            yield request

    def get_captcha_id(self, response):
        url = response.meta['url']
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
            }
        )
        yield request

    def fail_captcha_id(self, failure):
        url = failure.request.meta['url']
        Registreringsnummer = failure.request.meta['Registreringsnummer']

        formdata = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': self.google_key,
            'pageurl': self.post_url,
            'proxy': 'http://1f7a28e9aa7446c491a11b8328a5ced7:@proxy.crawlera.com:8010/',
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
                'Registreringsnummer': Registreringsnummer
            }
        )
        yield request

    def get_recaptchaClientToken(self, response):
        fetch_url = response.meta['fetch_url']
        Registreringsnummer = response.meta['Registreringsnummer']
        captcha_id = response.meta['captcha_id']
        resp_cnt = response.meta['resp_cnt']

        print("\t[{}] {}".format(resp_cnt, response.text))
        if response.text.split('|')[0] == 'OK':
            recaptchaClientToken = response.text.split('|')[1]
            request = FormRequest(
                url=self.get_url,
                method='GET',
                headers=make_headers_1(),
                callback=self.get__RequestVerificationToken,
                errback=self.fail__RequestVerificationToken,
                dont_filter=True,
                meta={
                    'fetch_url': fetch_url,
                    'Registreringsnummer': Registreringsnummer,
                    'captcha_id': captcha_id,
                    'recaptchaClientToken': recaptchaClientToken,
                }
            )
            yield request

        else:
            resp_cnt += 1
            if resp_cnt >= self.max_resp_cnt:
                url = "http://2captcha.com/in.php"
                formdata = {
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': self.google_key,
                    'pageurl': self.post_url,
                    'proxy': 'http://1f7a28e9aa7446c491a11b8328a5ced7:@proxy.crawlera.com:8010/',
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
                        'Registreringsnummer': Registreringsnummer
                    }
                )
                yield request
            else:
                sleep(self.resp_time)
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
                    }
                )
                yield request

    def fail_recaptchaClientToken(self, failure):
        fetch_url = failure.request.meta['fetch_url']
        Registreringsnummer = failure.request.meta['Registreringsnummer']
        captcha_id = failure.request.meta['captcha_id']
        resp_cnt = failure.request.meta['resp_cnt']

        resp_cnt += 1
        if resp_cnt >= self.max_resp_cnt:
            url = "http://2captcha.com/in.php"
            formdata = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': self.google_key,
                'pageurl': self.post_url,
                'proxy': 'http://1f7a28e9aa7446c491a11b8328a5ced7:@proxy.crawlera.com:8010/',
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
                    'Registreringsnummer': Registreringsnummer
                }
            )
            yield request
        else:
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
                }
            )
            yield request

    def get__RequestVerificationToken(self, response):
        fetch_url = response.meta['fetch_url']
        Registreringsnummer = response.meta['Registreringsnummer']
        captcha_id = response.meta['captcha_id']
        recaptchaClientToken = response.meta['recaptchaClientToken']

        __RequestVerificationToken = response.xpath(
            '//input[@name="__RequestVerificationToken"]/@value').extract_first()

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
        payload = {
            '__RequestVerificationToken': __RequestVerificationToken,
            'Registreringsnummer': Registreringsnummer,
            'recaptchaClientToken': recaptchaClientToken,
            'Captcha.CaptchaResponse': ''
        }

        request = FormRequest(
            url=self.post_url,
            method='POST',
            headers=headers,
            formdata=payload,
            callback=self.get_details,
            errback=self.fail_details,
            dont_filter=True,
            meta={
                'Registreringsnummer': Registreringsnummer,
                '__RequestVerificationToken': __RequestVerificationToken,
                'recaptchaClientToken': recaptchaClientToken,
            }
        )
        yield request

    def fail__RequestVerificationToken(self, failure):
        fetch_url = failure.request.meta['fetch_url']
        Registreringsnummer = failure.request.meta['Registreringsnummer']
        captcha_id = failure.request.meta['captcha_id']
        recaptchaClientToken = failure.request.meta['recaptchaClientToken']

        request = FormRequest(
            url=self.get_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get__RequestVerificationToken,
            errback=self.fail__RequestVerificationToken,
            dont_filter=True,
            meta={
                'fetch_url': fetch_url,
                'Registreringsnummer': Registreringsnummer,
                'captcha_id': captcha_id,
                'recaptchaClientToken': recaptchaClientToken,
            }
        )
        yield request

    def get_details(self, response):
        Registreringsnummer = response.meta['Registreringsnummer']
        __RequestVerificationToken = response.meta['__RequestVerificationToken']
        recaptchaClientToken = response.meta['recaptchaClientToken']

        if response.xpath('//script[contains(@src, "https://www.google.com/recaptcha/api")]/@src'):
            print("\tCaptcha is found")
            url = "http://2captcha.com/in.php"
            formdata = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': self.google_key,
                'pageurl': self.post_url,
                'proxy': 'http://1f7a28e9aa7446c491a11b8328a5ced7:@proxy.crawlera.com:8010/',
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
                    'Registreringsnummer': Registreringsnummer
                }
            )
            yield request
        else:
            try:
                Försäkringsbolag = \
                    [elm.strip() for elm in
                     response.xpath('//strong[contains(text(), "kringsbolag")]/../text()').extract() if
                     elm.strip()][
                        0].strip()
            except:
                Försäkringsbolag = ''
            try:
                Försäkringsdatum = \
                    [elm.strip() for elm in
                     response.xpath('//strong[contains(text(), "kringsdatum")]/../text()').extract() if
                     elm.strip()][
                        0].strip()
            except:
                Försäkringsdatum = ''

            self.already_list.append(Registreringsnummer)
            result_row = [
                Registreringsnummer, Försäkringsbolag, Försäkringsdatum
            ]
            yield result_row
            self.total_cnt += 1
            print("\t[Result {}] {}".format(self.total_cnt, result_row))
            self.insert_row(result_row=result_row)

    def fail_details(self, failure):
        Registreringsnummer = failure.request.meta['Registreringsnummer']
        __RequestVerificationToken = failure.request.meta['__RequestVerificationToken']
        recaptchaClientToken = failure.request.meta['recaptchaClientToken']

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
        payload = {
            '__RequestVerificationToken': __RequestVerificationToken,
            'Registreringsnummer': Registreringsnummer,
            'recaptchaClientToken': recaptchaClientToken,
            'Captcha.CaptchaResponse': ''
        }

        request = FormRequest(
            url=self.post_url,
            method='POST',
            headers=headers(),
            formdata=payload,
            callback=self.get_details,
            errback=self.fail_details,
            dont_filter=True,
            meta={
                'Registreringsnummer': Registreringsnummer,
                '__RequestVerificationToken': __RequestVerificationToken,
                'recaptchaClientToken': recaptchaClientToken,
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
