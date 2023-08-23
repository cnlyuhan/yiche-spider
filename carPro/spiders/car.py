import scrapy
from scrapy.linkextractors import LinkExtractor
from ..items import CarItem, BrandItem
import random
from ..fake_useragent import get_requests_headers
from ..fake_useragent import get_ua
from urllib.parse import urlencode
from hashlib import md5
import math
import time
import json
import pickle
from ..settings import carid_filepath
import os

class CarSpider(scrapy.Spider):
    name = 'car'
    # allowed_domains = ['www.xxx.com']
    start_urls = ['https://car.yiche.com/']
    flag = 0
    par = None

    # 增量式爬虫
    carid_set = set()
    if os.path.exists(carid_filepath):
        print("文件存在！")
        f = open(carid_filepath, 'rb')
        temp_set = pickle.load(f)
        carid_set.update(temp_set)
        print(len(carid_set))
        print('cardid_set:', carid_set)
        f.close()
    else:
        print('文件不存在，现已创建！')


    def UnlockHeaders(self):
        timestamp = str(int(time.time() * 1000))
        timestamp1 = str(int(time.time()))
        n = "cid=" + '508' + "&param=" + self.par + '19DDD1FBDFF065D3A4DA777D2D7A81EC' + timestamp

        # 标准的md5算法
        obj = md5()
        obj.update(n.encode('utf-8'))
        sign = obj.hexdigest()

        e = str(int(math.floor(9e8 * random.random()) + 1e8))

        headers = {
            'User-Agent': get_ua(),
            'cookie': f'locatecity=370600; bitauto_ipregion=223.97.56.24%3A%E5%9B%9B%E5%B7%9D%E7%9C%81%E6%B3%B8%E5%B7%9E%E5%B8%82%3B2517%2C%E6%B3%B8%E5%B7%9E%E5%B8%82%2Cluzhou; auto_id=1379418d938c31e5b46c80341902f496; CIGDCID=hF2wCGSy6NTNtynCkB6XESPQ3AY4KZBZ; CIGUID=8782b007-6016-43c6-bbfc-884006db6193; selectcity=510500; selectcityid=2517; selectcityName=%E6%B3%B8%E5%B7%9E; UserGuid=8782b007-6016-43c6-bbfc-884006db6193; Hm_lvt_610fee5a506c80c9e1a46aa9a2de2e44=1673438164,1673490111; csids=2593_5536_5476_4322_1661; report-cookie-id={e}_{timestamp}; Hm_lpvt_610fee5a506c80c9e1a46aa9a2de2e44={timestamp1}',
            'refer': 'https://car.yiche.com/',
            'content-type': 'application/json;charset=UTF-8',
            'x-city-id': '2103',
            'x-ip-address': '223.97.56.24',
            'x-platform': 'pc',
            'x-sign': sign,  # 需要逆向开发
            'x-timestamp': timestamp,  # 需要逆向开发，当前系统时间（数字）
            'x-user-guid': 'c5389c4e5ec29568361cb968f185cdf9'  # 从cookie中暂时复制过去
        }
        return headers

    def parse(self, response):
        div_list = response.xpath('//div[@class="brand-list-content"]/div/div')
        for div in div_list:
            brand_list = div.xpath('./div[@class="item-brand"]')
            for brand in brand_list:
                item = BrandItem()
                brand_url = 'https://car.yiche.com' + brand.xpath('./a/@href').extract_first()
                brand_name = brand.xpath('./a/div/text()').extract_first()
                brand_id = int(brand_url.split('=')[-1])

                item['brand_id'] = brand_id
                item['brand_name'] = brand_name
                item['brand_url'] = brand_url

                yield scrapy.Request(url=brand_url, callback=self.parse_car, headers=get_requests_headers())
                yield item

    def parse_car(self, response):
        # 控制翻页
        if self.flag == 2:
            self.flag = 0

        div_list = response.xpath('//div[@class="search-result-list"]/div')
        # print(div_list)
        if not div_list:
            pass

        for div in div_list:
            """
            **************
            change datatype
            """
            item = CarItem()

            car_id = div.xpath('./@data-id').extract_first()

            # 判断这个车是否已经爬取过
            if set({int(car_id)}).issubset(self.carid_set):
                pass
            else:
                self.carid_set.add(int(car_id))
                # print(self.carid_set)
            car_name = div.xpath('./a/p[1]/text()').extract_first()
            car_detail_url = 'https://car.yiche.com/' + div.xpath('./a/@href').extract_first()
            car_price = div.xpath('./a/p[2]/text()').extract_first()
            price_list = str(car_price).split('-')
            if len(price_list) == 1:
                try:
                    car_price_low = car_price_high = float(price_list[0][:-1])
                    item['car_price_low'] = car_price_low
                    item['car_price_high'] = car_price_high
                except ValueError as e:
                    item['car_price_low'] = item['car_price_high'] = -1.00

            else:
                item['car_price_low'] = float(price_list[0])
                item['car_price_high'] = float(price_list[1][:-1])

            item['car_id'] = int(car_id)
            item['car_name'] = car_name
            # print(car_name)

            link = LinkExtractor(allow=r'mid=\d&page=\d').extract_links(response)
            if link:
                try:
                    next_url = link[self.flag].url
                except:
                    next_url = link[0].url
                self.flag += 1
                yield scrapy.Request(
                    headers=get_requests_headers(),
                    url=next_url,
                    callback=self.parse_car,
                )

            # 请求车的具体评分
            dic = '{"serialId":"%d"}'
            p = format(dic % int(car_id))
            self.par = p
            params = {
                'cid': '508',
                'param': p
            }
            url_rating = 'https://mapi.yiche.com/web_api/information_api/api/v1/point_comment/tags?' + urlencode(params)
            yield scrapy.Request(url=url_rating, callback=self.parse_carDetail, meta={'item': item},
                                 headers=self.UnlockHeaders())

            # print(item)
    def parse_carDetail(self, response):
        item = response.meta['item']
        resp = json.loads(response.text)
        rating = resp['data']['pointCommontInfo']['score']
        item['car_rating'] = rating
        yield item
        # print(item)
# https://mapi.yiche.com/web_api/information_api/api/v1/point_comment/tags?cid=508&param=%7B%22serialId%22%3A%222406%22%7D
# https://mapi.yiche.com/web_api/information_api/api/v1/point_comment/tags?cid=508&param=%7B%22serialId%22%3A+%222593%22%7D