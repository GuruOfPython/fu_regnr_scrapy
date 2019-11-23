# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class FuRegnrItem(scrapy.Item):
    Registreringsnummer = Field()
    Försäkringsbolag = Field()
    Försäkringsdatum = Field()
    Fordonsstatus = Field()
    Besiktigas_senast_8 = Field()
    Upplysningar = Field()
    Import_införsel = Field()
    Besiktigas_senast = Field()
    Senast_godkända_besiktning = Field()
    Mätarställning = Field()

