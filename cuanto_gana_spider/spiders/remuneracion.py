# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 18:13:26 2020

@author: Juliano
"""

import scrapy
from lxml import etree
from parsel import Selector
import uuid
from cuanto_gana_spider.resources import institutions

class RemuneracionSpider(scrapy.Spider):
    name = 'remuneracion'
    selectors = {}

    def __init__(self, start='', stop='', *args, **kwargs):
        super(RemuneracionSpider, self).__init__(*args, **kwargs)
        try:
            self.start = int(start)
        except:
            self.start = 0
        try:
            self.stop = int(stop)
        except:
            self.stop = len(institutions)
    
    def start_requests(self):
        for code, institution in institutions[self.start:self.stop]:
            yield scrapy.Request('https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/'+code+'/PR/PCONT/', meta={'institution':institution})
    
    def parse(self, response):
        for year_link in response.css('a[target=_self]'):
            yield response.follow(year_link.xpath('@href').get(), 
                                  self.parse_year,
                                  meta={'institution':response.meta['institution']})

    def parse_year(self, response):
        for month_link in response.css('a[target=_self]'):
            yield response.follow(month_link.xpath('@href').get(), 
                                  self.parse_month,
                                  meta={'institution':response.meta['institution']})
        
    def parse_month(self, response):
        line_titles = response.xpath('//th//text()').getall()
        yield from self.yield_results(response, response.meta['institution'], line_titles)
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
                meta={
                    'institution':response.meta['institution'],
                    'line_titles':line_titles,
                })
        
    def next_page(self, response):
        parser = etree.XMLParser(strip_cdata=False)
        root = etree.fromstring(response.body, parser=parser, base_url=response.url)
        content = Selector(root=root).xpath('//text()').getall()
        inner_xml = content[0] if len(content)>0 else ""
        root2 = etree.fromstring("<newtable>" + inner_xml + "</newtable>")
        my_id = uuid.uuid4()
        self.selectors[my_id] = Selector(root=root2)
        yield from self.yield_results(self.selectors[my_id], response.meta['institution'], response.meta['line_titles'])
        del self.selectors[my_id]
    
    def yield_results(self, selector, institution, line_titles):
        """
        Yields results from a response.

        Args:
            selector (Selector): the parsel Selector instance from which xpath() can be called.
            institution (str): the institution name to be added in the yielded response.
            line_titles (list): list of strings to be used as keys for the result dictionary.

        Yields:
            dict: zip of line_titles and response's //tr/td//text()
        """

        for i,line in enumerate(selector.xpath('//tr')):
            if len(line.xpath('td')) > 0:
                results = dict(zip(line_titles, line.xpath('td//text()').getall()))
                results.update({
                    "Organismo": institution,
                    "Regimen": "Contrata"
                })
                yield results
            else:
                yield {
                    "DEBUG_MSG": str(i) + ", len td is 0",
                    "DEBUG_Organismo": institution,
                    "DEBUG_Regimen": "Contrata"
                }
