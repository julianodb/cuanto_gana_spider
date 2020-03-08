# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 18:13:26 2020

@author: Juliano
"""

import scrapy
from lxml import etree
from parsel import Selector

class RemuneracionSpider(scrapy.Spider):
    name = 'remuneracion'
    start_urls = ['https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/AA001/PR/PCONT/43186985']
    line_titles = []

    def parse(self, response):
        self.line_titles = response.xpath('//th//text()').getall()
        for line in response.xpath('//tr'):
            if len(line.xpath('td')) > 0:
                yield dict(zip(self.line_titles, line.xpath('td//text()').getall()))
        for start_page in [100]:
            form = scrapy.FormRequest.from_response(
                response,
                formid="A2248:form-visualizar",
                formdata={
                        "javax.faces.partial.ajax": "true",
                        "javax.faces.source": "A2248:form-visualizar:datosplantilla",
                        "javax.faces.partial.execute": "A2248:form-visualizar:datosplantilla",
                        "javax.faces.partial.render": "A2248:form-visualizar:datosplantilla",
                        "A2248:form-visualizar:datosplantilla": "A2248:form-visualizar:datosplantilla",
                        "A2248:form-visualizar:datosplantilla_pagination": "true",
                        "A2248:form-visualizar:datosplantilla_first": str(start_page),
                        "A2248:form-visualizar:datosplantilla_rows": "100",
                        "A2248:form-visualizar:datosplantilla_encodeFeature": "true"
                },
                url=response.css('input[name="javax.faces.encodedURL"]').xpath('@value').get(),
                callback=self.next_page)
            yield form
        
        
    def next_page(self, response):
        parser = etree.XMLParser(strip_cdata=False)
        root = etree.fromstring(response.body, parser=parser, base_url=response.url)
        inner_xml = Selector(root=root).xpath('//text()').get()
        yield {'inner_xml': inner_xml}
        root2 = etree.fromstring("<newtable>" + inner_xml + "</newtable>")
        for line in Selector(root=root2).xpath('//tr'):
            if len(line.xpath('td')) > 0:
                yield dict(zip(self.line_titles, line.xpath('td//text()').getall()))
        #line_titles = response.xpath('//th//text()').getall()
        #for line in response.xpath('//tr'):
        #    if len(line.xpath('td')) > 0:
        #        yield dict(zip(line_titles, line.xpath('td//text()').getall()))
