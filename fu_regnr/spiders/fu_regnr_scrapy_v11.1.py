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
from fu_regnr.settings import *
from random import randint

def make_headers_1():
    headers = {
        # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
        'user-agent': user_agents[randint(0, len(user_agents) - 1)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
    }
    return headers


def make_headers_2():
    headers = {
        # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
        'user-agent': user_agents[randint(0, len(user_agents) - 1)],
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
        self.input_data = csv.reader(open('Test.csv', 'r', encoding='utf-8'))
        # r = requests.get('https://file-post.net/en/p0/d1/1574176876_293875412_48/dir/Test.csv')
        # self.input_data = list(csv.reader(r.content.decode().splitlines(), delimiter=','))
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

        self.captcha_in_url = "http://2captcha.com/in.php"
        self.captcha_res_url = "http://2captcha.com/res.php?key={}&action=get".format(self.api_key) + "&id={}"

        self.max_resp_cnt = 12
        self.resp_time = 10
        self.total_cnt = 0
        self.total_scraping_done = True

    def start_requests(self):

        self.input_data = list(self.input_data)
        self.input_data.reverse()
        self.input_data.pop()
        while self.input_data:
            line = self.input_data.pop()
            if line:
                break
        self.Registreringsnummer = line[18]

        self.total_cnt += 1
        print("[{}] Scanning ...".format(self.Registreringsnummer))
        self.total_scraping_done = False
        request = FormRequest(
            url=self.get_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get__RequestVerificationToken,
            errback=self.fail__RequestVerificationToken,
            dont_filter=True,
            meta={
            }
        )
        yield request

    def get__RequestVerificationToken(self, response):
        self.__RequestVerificationToken = response.xpath(
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

        headers = make_headers_1()
        headers['cookie'] = self.cookie
        request = FormRequest(
            url=self.captcha_in_url,
            method='POST',
            formdata=formdata,
            headers=headers,
            callback=self.get_captcha_id,
            errback=self.fail_captcha_id,
            dont_filter=True,
            meta={
            }
        )
        yield request

    def get_captcha_id(self, response):
        if response.text[0:2] != 'OK':
            print('[Error] Captcha is not received')
            return

        self.captcha_id = response.text.split('|')[1]

        sleep(self.resp_time)
        fetch_url = self.captcha_res_url.format(self.captcha_id)
        resp_cnt = 0
        request = FormRequest(
            url=fetch_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get_recaptchaClientToken,
            errback=self.fail_recaptchaClientToken,
            dont_filter=True,
            meta={
                'resp_cnt': resp_cnt,
            }
        )
        yield request

    def get_recaptchaClientToken(self, response):
        resp_cnt = response.meta['resp_cnt']

        print("\t[{}] {}".format(resp_cnt, response.text))
        if response.text.split('|')[0] == 'OK':
            self.recaptchaClientToken = response.text.split('|')[1]

            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'cookie': self.cookie
            }
            payload = {
                '__RequestVerificationToken': self.__RequestVerificationToken,
                'Registreringsnummer': self.Registreringsnummer,
                'recaptchaClientToken': self.recaptchaClientToken,
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
                }
            )
            yield request

        else:
            resp_cnt += 1
            if resp_cnt >= self.max_resp_cnt:
                formdata = {
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': self.google_key,
                    'pageurl': self.post_url,
                }

                headers = make_headers_1()
                headers['cookie'] = self.cookie

                request = FormRequest(
                    url=self.captcha_in_url,
                    method='POST',
                    formdata=formdata,
                    headers=headers,
                    callback=self.get_captcha_id,
                    errback=self.fail_captcha_id,
                    dont_filter=True,
                    meta={
                    }
                )
                yield request
            else:
                sleep(self.resp_time)
                fetch_url = self.captcha_res_url.format(self.captcha_id)
                request = FormRequest(
                    url=fetch_url,
                    method='GET',
                    headers=make_headers_1(),
                    callback=self.get_recaptchaClientToken,
                    errback=self.fail_recaptchaClientToken,
                    dont_filter=True,
                    meta={
                        'resp_cnt': resp_cnt,
                    }
                )
                yield request

    def get_details(self, response):
        if response.xpath('//script[contains(@src, "https://www.google.com/recaptcha/api")]/@src'):
            print(f"\t[{self.Registreringsnummer}] Captcha is found")

            formdata = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': self.google_key,
                'pageurl': self.post_url,
            }

            headers = make_headers_1()
            headers['cookie'] = self.cookie
            request = FormRequest(
                url=self.captcha_in_url,
                method='POST',
                formdata=formdata,
                headers=headers,
                callback=self.get_captcha_id,
                errback=self.fail_captcha_id,
                dont_filter=True,
                meta={
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

            try:
                Fordonsstatus = \
                    [elm.strip() for elm in response.xpath('//a[@href="#ts-fordonsstatus"]/../../text()').extract() if
                     elm.strip()][0].strip()
            except:
                Fordonsstatus = ""
            try:
                Besiktigas_senast_8 = [elm.strip() for elm in response.xpath(
                    '//strong[contains(text(), "Besiktigas senast")]/../text()').extract() if elm.strip()][-2].strip()
            except:
                Besiktigas_senast_8 = ""
            try:
                Upplysningar = \
                    [elm.strip() for elm in
                     response.xpath('//strong[contains(text(), "Upplysningar")]/../text()').extract()
                     if elm.strip()][0].strip()
            except:
                Upplysningar = ""
            try:
                Import_införsel = \
                    [elm.strip() for elm in response.xpath('//a[@href="#ts-import"]/../../text()').extract() if
                     elm.strip()][0].strip()
            except:
                Import_införsel = ""
            try:
                Besiktigas_senast = [elm.strip() for elm in response.xpath(
                    '//strong[contains(text(), "Besiktigas senast")]/../text()').extract() if elm.strip()][-1].strip()
            except:
                Besiktigas_senast = ""
            try:
                Senast_godkända_besiktning = [elm.strip() for elm in response.xpath(
                    '//strong[contains(text(), "Senast god") and contains(text(), "besiktning")]/../text()').extract()
                                              if elm.strip()][0].strip()
            except:
                Senast_godkända_besiktning = ""
            try:
                Mätarställning = \
                    [elm.strip() for elm in response.xpath('//a[@href="#ts-matarstallning"]/../../text()').extract() if
                     elm.strip()][0].strip()
            except:
                Mätarställning = ""

            item = FuRegnrItem()
            item['Registreringsnummer'] = self.Registreringsnummer
            item['Försäkringsbolag'] = Försäkringsbolag
            item['Försäkringsdatum'] = Försäkringsdatum
            item['Fordonsstatus'] = Fordonsstatus
            item['Besiktigas_senast_8'] = Besiktigas_senast_8
            item['Upplysningar'] = Upplysningar
            item['Import_införsel'] = Import_införsel
            item['Besiktigas_senast'] = Besiktigas_senast
            item['Senast_godkända_besiktning'] = Senast_godkända_besiktning
            item['Mätarställning'] = Mätarställning

            yield item

            result_row = [
                self.Registreringsnummer, Försäkringsbolag, Försäkringsdatum, Fordonsstatus, Besiktigas_senast_8,
                Upplysningar, Import_införsel, Besiktigas_senast, Senast_godkända_besiktning, Mätarställning
            ]
            self.total_cnt += 1
            print("\t[Result {}] {}".format(self.total_cnt, result_row))
            self.insert_row(result_row=result_row)

            self.total_scraping_done = True

            while self.input_data:
                line = self.input_data.pop()
                if line:
                    break

            self.Registreringsnummer = line[18]

            self.total_cnt += 1
            print("[{}] Scanning ...".format(self.Registreringsnummer))
            self.total_scraping_done = False
            request = FormRequest(
                url=self.get_url,
                method='GET',
                headers=make_headers_1(),
                callback=self.get__RequestVerificationToken,
                errback=self.fail__RequestVerificationToken,
                dont_filter=True,
                meta={
                }
            )
            yield request

    def fail__RequestVerificationToken(self, failure):
        request = FormRequest(
            url=self.get_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get__RequestVerificationToken,
            errback=self.fail__RequestVerificationToken,
            dont_filter=True,
            meta={
            }
        )
        yield request

    def fail_captcha_id(self, failure):
        formdata = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': self.google_key,
            'pageurl': self.post_url,
        }

        headers = make_headers_1()
        headers['cookie'] = self.cookie
        request = FormRequest(
            url=self.captcha_in_url,
            method='POST',
            formdata=formdata,
            headers=headers,
            callback=self.get_captcha_id,
            errback=self.fail_captcha_id,
            dont_filter=True,
            meta={
            }
        )
        yield request

    def fail_recaptchaClientToken(self, failure):
        sleep(self.resp_time)
        fetch_url = self.captcha_res_url.format(self.captcha_id)
        resp_cnt = 0
        request = FormRequest(
            url=fetch_url,
            method='GET',
            headers=make_headers_1(),
            callback=self.get_recaptchaClientToken,
            errback=self.fail_recaptchaClientToken,
            dont_filter=True,
            meta={
                'resp_cnt': resp_cnt,
            }
        )
        yield request

    def fail_details(self, failure):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'cookie': self.cookie
        }
        payload = {
            '__RequestVerificationToken': self.__RequestVerificationToken,
            'Registreringsnummer': self.Registreringsnummer,
            'recaptchaClientToken': self.recaptchaClientToken,
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
