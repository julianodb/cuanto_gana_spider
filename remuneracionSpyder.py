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
    selectors = {}

    def parse(self, response):
        self.line_titles = response.xpath('//th//text()').getall()
        for line in response.xpath('//tr'):
            if len(line.xpath('td')) > 0:
                yield dict(zip(self.line_titles, line.xpath('td//text()').getall()))
        total_count_candidate = response.selector.re('rowCount:(\d+)')
        total_count = int(total_count_candidate[0]) if len(total_count_candidate)>0 else 0
        for start_page in range(100,total_count,100):
            yield scrapy.FormRequest.from_response(
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
                        "A2248:form-visualizar:datosplantilla_rows": str(min(100,total_count-start_page)),
                        "A2248:form-visualizar:datosplantilla_encodeFeature": "true"
                },
                url=response.css('input[name="javax.faces.encodedURL"]').xpath('@value').get(),
                callback=self.next_page,
                cb_kwargs={'start_page': start_page})
        
        
    def next_page(self, response, start_page=0):
        parser = etree.XMLParser(strip_cdata=False)
        root = etree.fromstring(response.body, parser=parser, base_url=response.url)
        content = Selector(root=root).xpath('//text()').getall()
        inner_xml = content[0]
        root2 = etree.fromstring("<newtable>" + inner_xml + "</newtable>")
        self.selectors[start_page] = Selector(root=root2)
        for i,line in enumerate(self.selectors[start_page].xpath('//tr')):
            if len(line.xpath('td')) > 0:
                yield {"start_page, current": f"{start_page}, {i}", **dict(zip(self.line_titles, line.xpath('td//text()').getall()))}
            else:
                yield {"start_page, current": f"{start_page}, {i}, len td is 0"}
