# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest
import requests
from time import sleep, time
from lxml import html
import csv
from os.path import dirname, abspath


def request_one(Registreringsnummer, api_key):
    '''
    Anti-captcha
    '''
    page_url = "https://fu-regnr.transportstyrelsen.se/extweb/UppgifterAnnatFordon/Fordonsuppgifter"
    url = f"http://2captcha.com/in.php?key={api_key}&method=userrecaptcha&googlekey={google_key}&pageurl={page_url}"
    sess = requests.Session()
    resp = sess.get(url, headers=make_headers_1())
    if resp.text[0:2] != 'OK':
        quit('Error. Captcha is not received')
    captcha_id = resp.text[3:]

    # fetch ready 'g-recaptcha-response' token for captcha_id
    fetch_url = f"http://2captcha.com/res.php?key={api_key}&action=get&id=" + captcha_id

    resp_cnt = 0
    while 1:
        if resp_cnt > 10:
            Försäkringsbolag, Försäkringsdatum = request_one(Registreringsnummer, api_key)
        else:
            sleep(5)  # wait 5 sec.
            try:
                resp = sess.get(fetch_url, headers=make_headers_1())
            except:
                continue
            resp_cnt += 1
            print("\t[{}] {}".format(resp_cnt, resp.text))
            if resp.text.split('|')[0] == 'OK':
                recaptchaClientToken = resp.text[3:]
                break
            elif resp.text.split('|')[0] == 'ERROR_CAPTCHA_UNSOLVABLE':
                Försäkringsbolag, Försäkringsdatum = request_one(Registreringsnummer, api_key)


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
        self.input_data = csv.reader(open('Test.csv', 'r', encoding='utf-8'))

        self.result_file_name = 'Result.csv'
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

        self.start_url = "https://fu-regnr.transportstyrelsen.se/extweb/UppgifterAnnatFordon"

    def start_requests(self):
        for i, line in enumerate(self.input_data):
            if i == 0:
                continue
            Registreringsnummer = line[18]
            print("[{}] Scanning ...".format(Registreringsnummer))
            if Registreringsnummer in self.already_list:
                print("\t[Already {}] {}".format(i, Registreringsnummer))
                continue

            request = FormRequest(
                url=self.start_url,
                method='GET',
                headers=make_headers_1(),
                callback=self.get__RequestVerificationToken,
                errback=self.fail__RequestVerificationToken,
                dont_filter=True,
                meta={
                    'Registreringsnummer': Registreringsnummer
                }
            )
            yield request

    def get__RequestVerificationToken(self, response):
        Registreringsnummer = response.meta['Registreringsnummer']
        __RequestVerificationToken = response.xpath(
            '//input[@name="__RequestVerificationToken"]/@value').extract_first()

        page_url = "https://fu-regnr.transportstyrelsen.se/extweb/UppgifterAnnatFordon/Fordonsuppgifter"
        url = "http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(self.api_key,
                                                                                                      self.google_key,
                                                                                                      page_url)

        request = FormRequest(
            url=url,
            method='GET',
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

    def fail__RequestVerificationToken(self, failure):
        Registreringsnummer = failure.request.meta['Registreringsnummer']
        request = FormRequest(
            url=self.start_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get__RequestVerificationToken,
            errback=self.fail__RequestVerificationToken,
            dont_filter=True,
            meta={
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
        captcha_id = response.text.text[3:]

        fetch_url = "http://2captcha.com/res.php?key={}&action=get&id={}".format(self.api_key, captcha_id)
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
                'captcha_id': captcha_id
            }
        )
        yield request

    def fail_captcha_id(self, failure):
        url = failure.request.meta['url']
        Registreringsnummer = failure.request.meta['Registreringsnummer']

        request = FormRequest(
            url=url,
            method='GET',
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



    def fail_recaptchaClientToken(self, response):
        pass

    def get_details(self, response):
        pass

    def fail_details(self, response):
        pass

    def parse(self, response):
        pass
