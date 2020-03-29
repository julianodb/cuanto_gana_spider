# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from cuanto_gana_spider.resources import month_map
import re

class ProcessNumbers(object):
    def process_item(self, item, spider):
        new_item = item.copy()
        for key, val in item.items():
            if(not isinstance(val, str)):
                continue
            cleaned_val = re.sub(r'[\.$]', "", val.strip())
            if(key=="Mes" and val in month_map):
                number = month_map[val]
            else:
                try:
                    number = int(re.findall(r'\d+', cleaned_val)[0])
                except:
                    continue
            new_item[key + "_number"] = number
        return new_item
