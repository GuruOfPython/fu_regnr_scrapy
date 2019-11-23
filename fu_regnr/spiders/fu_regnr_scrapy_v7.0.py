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
import asyncio


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
        self.input_data.reverse()
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
        while self.input_data:
            line = self.input_data.pop()
            Registreringsnummer = line[18]
            if Registreringsnummer == 'Registreringsnummer':
                print("\t[Already {}] {}".format(self.total_cnt, Registreringsnummer))
                continue
            else:
                break

        self.get_one_by_one(line)

    async def get_one_by_one(self, line):
        recaptchaClientToken = await self.resolve_captcha(line=line)
        __RequestVerificationToken = await self.get__RequestVerificationToken()
        [
            Registreringsnummer, Försäkringsbolag, Försäkringsdatum, Fordonsstatus, Besiktigas_senast_8,
            Upplysningar, Import_införsel, Besiktigas_senast, Senast_godkända_besiktning, Mätarställning
        ] = await self.get_details(line, recaptchaClientToken, __RequestVerificationToken)

        item = FuRegnrItem()
        item['Registreringsnummer'] = Registreringsnummer
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
        self.already_list.append(Registreringsnummer)
        result_row = [
            Registreringsnummer, Försäkringsbolag, Försäkringsdatum, Fordonsstatus, Besiktigas_senast_8,
            Upplysningar, Import_införsel, Besiktigas_senast, Senast_godkända_besiktning, Mätarställning
        ]
        self.total_cnt += 1
        print("\t[Result {}] {}".format(self.total_cnt, result_row))

        if self.input_data:
            line = self.input_data.pop()
            Registreringsnummer = line[18]
            self.get_one_by_one(line)

    async def resolve_captcha(self, line):
        Registreringsnummer = line[18]
        sess = requests.Session()

        self.total_cnt += 1
        print("[{}] Scanning ...".format(Registreringsnummer))

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
        }
        url = "http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(self.api_key,
                                                                                                      self.google_key,
                                                                                                      self.post_url)
        recaptchaClientToken = None
        while 1:
            try:
                resp = sess.get(url, headers=headers)
                break
            except:
                pass
        if resp.text[0:2] != 'OK':
            print('Error. Captcha is not received')
            recaptchaClientToken = self.resolve_captcha(line)

        captcha_id = resp.text[3:]
        fetch_url = "http://2captcha.com/res.php?key={}&action=get&id={}".format(self.api_key, captcha_id)

        resp_cnt = 0
        max_resp_cnt = 20
        while 1:
            if resp_cnt >= max_resp_cnt:
                recaptchaClientToken = self.resolve_captcha(line)
            else:
                try:
                    sleep(5)
                    resp = sess.get(fetch_url, headers=headers)
                    resp_cnt += 1
                    print("\t[{}] {}".format(resp_cnt, resp.text))
                    if resp.text.split('|')[0] == 'OK':
                        recaptchaClientToken = resp.text.split('|')[1]
                        break
                    elif resp.text.split('|')[0] == 'ERROR_CAPTCHA_UNSOLVABLE':
                        recaptchaClientToken = self.resolve_captcha(line)
                except:
                    recaptchaClientToken = self.resolve_captcha(line)

        return recaptchaClientToken

    async def get__RequestVerificationToken(self):
        sess = requests.Session()
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
        }
        while 1:
            try:
                resp = sess.get(self.get_url, headers=headers)
                tree = html.fromstring(resp.text)
                __RequestVerificationToken = tree.xpath('//input[@name="__RequestVerificationToken"]/@value')[
                    0]
                break
            except:
                pass

        return __RequestVerificationToken

    async def get_details(self, line, recaptchaClientToken, __RequestVerificationToken):
        sess = requests.Session()
        Registreringsnummer = line[18]
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

        while 1:
            try:
                resp = sess.post(self.post_url, headers=headers, data=payload)
                break
            except:
                pass

        tree = html.fromstring(resp.text)
        if tree.xpath('//script[contains(@src, "https://www.google.com/recaptcha/api")]/@src'):
            print("\tCaptcha is found")
            self.get_one_by_one(line)
        else:
            try:
                Försäkringsbolag = \
                    [elm.strip() for elm in
                     tree.xpath('//strong[contains(text(), "kringsbolag")]/../text()') if
                     elm.strip()][
                        0].strip()
            except:
                Försäkringsbolag = ''
            try:
                Försäkringsdatum = \
                    [elm.strip() for elm in
                     tree.xpath('//strong[contains(text(), "kringsdatum")]/../text()') if
                     elm.strip()][
                        0].strip()
            except:
                Försäkringsdatum = ''

            try:
                Fordonsstatus = \
                    [elm.strip() for elm in tree.xpath('//a[@href="#ts-fordonsstatus"]/../../text()') if
                     elm.strip()][0].strip()
            except:
                Fordonsstatus = ""
            try:
                Besiktigas_senast_8 = [elm.strip() for elm in tree.xpath(
                    '//strong[contains(text(), "Besiktigas senast")]/../text()') if elm.strip()][-2].strip()
            except:
                Besiktigas_senast_8 = ""
            try:
                Upplysningar = \
                    [elm.strip() for elm in
                     tree.xpath('//strong[contains(text(), "Upplysningar")]/../text()')
                     if elm.strip()][0].strip()
            except:
                Upplysningar = ""
            try:
                Import_införsel = \
                    [elm.strip() for elm in tree.xpath('//a[@href="#ts-import"]/../../text()') if
                     elm.strip()][0].strip()
            except:
                Import_införsel = ""
            try:
                Besiktigas_senast = [elm.strip() for elm in tree.xpath(
                    '//strong[contains(text(), "Besiktigas senast")]/../text()') if elm.strip()][-1].strip()
            except:
                Besiktigas_senast = ""
            try:
                Senast_godkända_besiktning = [elm.strip() for elm in tree.xpath(
                    '//strong[contains(text(), "Senast god") and contains(text(), "besiktning")]/../text()')
                                              if elm.strip()][0].strip()
            except:
                Senast_godkända_besiktning = ""
            try:
                Mätarställning = \
                    [elm.strip() for elm in tree.xpath('//a[@href="#ts-matarstallning"]/../../text()') if
                     elm.strip()][0].strip()
            except:
                Mätarställning = ""

            return [
                Registreringsnummer, Försäkringsbolag, Försäkringsdatum, Fordonsstatus, Besiktigas_senast_8,
                Upplysningar, Import_införsel, Besiktigas_senast, Senast_godkända_besiktning, Mätarställning
            ]

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
